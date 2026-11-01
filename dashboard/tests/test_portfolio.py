"""Contract and failure isolation checks against actual immutable replay artifacts."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from dashboard.server.app import ROOT, create_app
from dashboard.server.portfolio import load_archive, source_key

PREFIX = "/api/cs5_6_equity/v1"
SOURCE = ROOT / "FINAL_OUTPUTS/01_saved_model_replay/verified_replay"


class PortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(explicit=SOURCE)
        cls.context = TestClient(cls.app)
        cls.client = cls.context.__enter__()
        cls.path = PREFIX + "/runs/configured/portfolio"

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_real_results_scope_and_absent_values(self):
        result = self.client.get(self.path)
        self.assertEqual(result.status_code, 200)
        d = result.json()
        self.assertEqual(d["status"], "success")
        self.assertEqual(d["module_id"], "cs5_6_equity")
        self.assertEqual(d["universe"]["training_count"], 66)
        self.assertEqual(d["universe"]["external_count"], 40)
        self.assertFalse(
            set(d["universe"]["training_tickers"])
            & set(d["universe"]["external_tickers"])
        )
        self.assertFalse(d["universe"]["includes_etfs"])
        self.assertFalse(d["universe"]["shared_asset_selector"])
        self.assertEqual(d["strategy"]["signal_frequency"], "weekly")
        self.assertEqual(d["strategy"]["id"], "Top5_NoLoss13w")
        self.assertEqual(
            (d["backtest"]["start"], d["backtest"]["end"]), ("2022-08-26", "2026-08-28")
        )
        self.assertEqual(d["backtest"]["weeks"], 210)
        self.assertAlmostEqual(
            d["metrics"]["annualized_return"],
            (d["metrics"]["final_capital"] / 100000) ** (52 / 210) - 1,
        )
        self.assertAlmostEqual(d["metrics"]["total_return"], 0.49330608884189986)
        self.assertIsNone(d["units"]["currency"])
        self.assertIsNone(d["benchmark"]["total_return"])
        self.assertIsNone(d["benchmark"]["series"])
        self.assertIsNone(d["data_cutoff"]["financial_publication_timestamp"])

    def test_selected_holdings_differ_from_raw_top_five(self):
        d = self.client.get(self.path).json()
        a = d["allocation"]
        self.assertEqual(
            [x["ticker"] for x in a["rows"]], ["SCL", "CMG", "UTZ", "RH", "URBN"]
        )
        self.assertEqual([x["model_rank"] for x in a["rows"]], [1, 3, 4, 6, 7])
        self.assertAlmostEqual(
            sum(x["actual_weight"] for x in a["rows"]) + a["cash_weight"], 1
        )
        for row in a["rows"]:
            self.assertAlmostEqual(
                row["actual_weight"],
                row["shares"]
                * row["execution_price_proxy"]
                / a["post_trade_open_value"],
            )
            self.assertEqual(row["target_weight"], 0.2)
        self.assertTrue(a["liquidated_at_period_end"])
        first = self.client.get(self.path, params={"date": "2022-08-26"}).json()
        self.assertFalse(first["allocation"]["liquidated_at_period_end"])
        self.assertEqual(
            d["provenance"]["allocation_verification"]["maximum_weekly_error"], 0
        )

    def test_all_exported_weeks_reconcile(self):
        archive = self.app.state.portfolio_archive
        self.assertEqual(len(archive["snapshots"]), 2)
        for snapshot in archive["snapshots"].values():
            self.assertEqual(len(snapshot["dates"]), 210)
            for value in snapshot["dates"].values():
                self.assertAlmostEqual(
                    sum(r["actual_weight"] for r in value["rows"])
                    + value["cash_weight"],
                    1,
                )
                self.assertLessEqual(len(value["rows"]), 5)
                self.assertTrue(
                    all(
                        r["ticker"] in archive["external_tickers"]
                        for r in value["rows"]
                    )
                )

    def test_controlled_no_data_and_invalid_input(self):
        missing = self.client.get(self.path, params={"date": "2019-08-30"})
        self.assertEqual(missing.status_code, 200)
        self.assertEqual(missing.json()["status"], "no_data")
        self.assertEqual(missing.json()["allocation"]["rows"], [])
        self.assertIsNone(missing.json()["allocation"]["cash_weight"])
        self.assertGreater(missing.json()["universe"]["signal_count"], 0)
        for path, code in [
            (self.path + "?date=not-a-date", 422),
            (PREFIX + "/runs/missing/portfolio", 404),
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, code)
            self.assertEqual(response.json()["status"], "error")
            self.assertEqual(response.json()["module_id"], "cs5_6_equity")
            self.assertEqual(
                response.json()["error"]["request_id"], response.headers["x-request-id"]
            )

    def test_namespace_and_legacy_results_are_identical(self):
        for suffix in (
            "overview",
            "equity",
            "inputs",
            "rankings?date=2026-08-28",
            "downloads/equity",
        ):
            new = self.client.get(PREFIX + "/runs/configured/" + suffix)
            legacy = self.client.get("/api/v1/runs/configured/" + suffix)
            self.assertEqual(new.status_code, 200)
            self.assertEqual(new.content, legacy.content)

    def test_missing_snapshot_does_not_disable_other_outputs(self):
        with patch(
            "dashboard.server.app.load_archive", side_effect=ValueError("corrupt")
        ):
            with TestClient(create_app(explicit=SOURCE)) as client:
                d = client.get(self.path).json()
                self.assertEqual(d["status"], "partial")
                self.assertIsNone(d["allocation"]["cash_weight"])
                self.assertIsNone(d["universe"]["training_count"])
                self.assertEqual(
                    client.get(PREFIX + "/runs/configured/equity").status_code, 200
                )
                self.assertTrue(
                    client.get(PREFIX + "/runs/configured/inputs").json()["available"]
                )

    def test_different_input_identity_cannot_reuse_allocations(self):
        archive = deepcopy(self.app.state.portfolio_archive)
        key = source_key(self.app.state.runs["configured"])
        archive["snapshots"][key]["input_hashes"]["factors"] = "0" * 64
        with patch.object(self.app.state, "portfolio_archive", archive):
            self.assertEqual(self.client.get(self.path).json()["status"], "partial")

    def test_tampering_rejected_by_archive_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "dashboard/data/cs5_6_equity"
            shutil.copytree(ROOT / "dashboard/data/cs5_6_equity", folder)
            path = folder / "portfolio.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_archive(root)

    def test_original_results_download_unchanged(self):
        for kind, name in [
            ("predictions", "saved_model_predictions.csv"),
            ("equity", "backtest/weekly.csv"),
            ("summary", "backtest/summary.csv"),
        ]:
            replay = self.app.state.runs["configured"]
            data = self.client.get(
                PREFIX + "/runs/configured/downloads/" + kind
            ).content
            self.assertEqual(
                hashlib.sha256(data).hexdigest(),
                hashlib.sha256(replay.downloads[kind]).hexdigest(),
            )
