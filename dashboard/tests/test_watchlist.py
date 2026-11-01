"""Watchlists inspect saved facts without changing research results."""

import csv
import io
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from dashboard.server.app import ROOT, create_app
from dashboard.server.config import Settings
from dashboard.server.inputs import INPUT_FILES
from dashboard.server.watchlist import FEATURES, export_stocks

PREFIX = "/api/cs5_6_equity/v1/runs/configured"
SOURCE = ROOT / "FINAL_OUTPUTS/01_saved_model_replay/verified_replay"


class WatchlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(explicit=SOURCE, settings=Settings())
        cls.context = TestClient(cls.app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def query(self, tickers="SCL,TJX,CMG", date="2026-08-28", suffix=""):
        return self.client.get(
            PREFIX + "/watchlist" + suffix, params={"tickers": tickers, "date": date}
        )

    def test_catalog_contains_only_external_stocks_and_real_names(self):
        d = self.client.get(PREFIX + "/stocks").json()
        portfolio = self.client.get(PREFIX + "/portfolio").json()
        self.assertEqual(
            [s["ticker"] for s in d["stocks"]],
            portfolio["universe"]["external_tickers"],
        )
        self.assertEqual(len(d["stocks"]), 40)
        self.assertEqual(len(d["backtest_dates"]), 210)
        self.assertEqual(len(d["ranking_dates"]), 366)
        self.assertEqual(d["default_date"], "2026-08-28")
        self.assertIn(
            "CHIPOTLE",
            next(s["stock_name"] for s in d["stocks"] if s["ticker"] == "CMG"),
        )
        self.assertFalse(d["watchlist_changes_strategy"])

    def test_real_example_distinguishes_ranking_and_actual_selection(self):
        response = self.query(" scl, tjx,CMG,SCL ")
        self.assertEqual(response.status_code, 200)
        d = response.json()
        self.assertEqual(d["requested_tickers"], ["SCL", "TJX", "CMG"])
        self.assertEqual(d["status"], "success")
        self.assertEqual(
            [r["ranking"]["ensemble_predicted_rank"] for r in d["rows"]], [1, 2, 3]
        )
        self.assertEqual(
            [r["selection_status"] for r in d["rows"]],
            ["selected", "not_selected", "selected"],
        )
        self.assertIsNone(d["rows"][1]["allocation"])
        self.assertIsNone(d["rows"][1]["exclusion_reason"])
        self.assertEqual(d["rows"][0]["allocation"]["target_weight"], 0.2)
        self.assertTrue(d["strategy_context"]["liquidated_at_period_end"])
        self.assertEqual(
            d["strategy_context"]["metrics_scope"], "original_strategy_full_backtest"
        )

    def test_factors_prices_and_rankings_match_original_files_by_exact_date(self):
        d = self.query("CMG,SCL", "2022-08-26").json()
        for kind, columns in [
            ("factors", FEATURES),
            ("prices", ("buy_price", "sell_price")),
        ]:
            with (ROOT / INPUT_FILES[kind]).open(encoding="utf-8-sig") as file:
                originals = {(r["date"], r["ticker"]): r for r in csv.DictReader(file)}
            for row in d["rows"]:
                original = originals[(d["signal_date"], row["ticker"])]
                self.assertEqual(row[kind], {k: float(original[k]) for k in columns})
                self.assertNotIn("target1", row[kind])
                self.assertNotIn("target2", row[kind])
        ranking = self.client.get(
            PREFIX + "/rankings", params={"date": "2022-08-26", "page_size": 100}
        ).json()
        for row in d["rows"]:
            self.assertEqual(
                row["ranking"],
                next(r for r in ranking["rows"] if r["ticker"] == row["ticker"]),
            )

    def test_no_data_is_not_a_zero_or_a_rejected_stock(self):
        d = self.query(date="2015-09-04").json()
        self.assertEqual(d["status"], "no_data")
        for row in d["rows"]:
            self.assertEqual(row["selection_status"], "no_data")
            self.assertEqual(row["factors_status"], "no_data")
            self.assertIsNone(row["ranking"])
            self.assertIsNone(row["factors"])
            self.assertIsNone(row["prices"])
            self.assertIsNone(row["allocation"])
        early = self.query("SCL", "2019-08-30").json()
        self.assertEqual(early["status"], "partial")
        self.assertIsNotNone(early["rows"][0]["ranking"])
        self.assertEqual(early["rows"][0]["selection_status"], "no_data")
        self.assertIsNone(early["rows"][0]["prices"])

    def test_missing_snapshot_preserves_inputs_and_rankings(self):
        with patch.object(self.app.state, "portfolio_archive", None):
            d = self.query().json()
            self.assertEqual(d["status"], "partial")
            for row in d["rows"]:
                self.assertEqual(row["selection_status"], "unavailable")
                self.assertIsNone(row["allocation"])
                self.assertIsNotNone(row["factors"])
                self.assertIsNotNone(row["ranking"])
            self.assertIsNotNone(d["provenance"]["input_hashes"]["factors"])
            self.assertIsNone(d["provenance"]["allocation_artifact_sha256"])

    def test_missing_inputs_do_not_create_a_false_selection_or_break_outputs(self):
        with patch.dict(self.app.state.inputs, {"configured": None}):
            d = self.query().json()
            self.assertEqual(d["status"], "partial")
            for row in d["rows"]:
                self.assertEqual(row["factors_status"], "unavailable")
                self.assertEqual(row["selection_status"], "unavailable")
                self.assertIsNone(row["factors"])
                self.assertIsNone(row["allocation"])
                self.assertIsNotNone(row["ranking"])
            self.assertIsNone(d["provenance"]["input_hashes"])
            self.assertEqual(self.client.get(PREFIX + "/equity").status_code, 200)

    def test_csv_and_json_export_only_current_date_and_selection(self):
        params = {"tickers": "CMG,TJX", "date": "2022-08-26"}
        expected = self.client.get(PREFIX + "/watchlist", params=params).json()
        for format in ("csv", "json"):
            response = self.client.get(
                PREFIX + "/watchlist/download", params={**params, "format": format}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                "2022-08-26." + format, response.headers["content-disposition"]
            )
            if format == "json":
                self.assertEqual(response.json(), expected)
            else:
                rows = list(
                    csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
                )
                self.assertEqual([r["ticker"] for r in rows], ["CMG", "TJX"])
                self.assertEqual({r["signal_date"] for r in rows}, {"2022-08-26"})
                for row, original in zip(rows, expected["rows"]):
                    self.assertEqual(
                        float(row["ensemble_ranking_score"]),
                        original["ranking"]["ensemble_ranking_score"],
                    )
                    self.assertEqual(row["watchlist_changes_strategy"], "False")
                    self.assertEqual(row["currency"], "")
                    self.assertEqual(len(row["factors_sha256"]), 64)
                    self.assertEqual(row["weight_units"], "decimal_fraction")
                    self.assertNotIn("total_return", row)
        missing = self.query(date="2015-09-04", suffix="/download").content
        row = next(csv.DictReader(io.StringIO(missing.decode("utf-8-sig"))))
        self.assertEqual(row["actual_weight"], "")
        self.assertEqual(row["ensemble_ranking_score"], "")

    def test_csv_formula_like_names_remain_literal(self):
        d = self.query("SCL").json()
        d["rows"][0]["stock_name"] = "=1+1"
        d["rows"][0]["factors"]["asset_growth_yoy"] = -0.25
        row = next(
            csv.DictReader(io.StringIO(export_stocks(d, "csv").decode("utf-8-sig")))
        )
        self.assertEqual(row["stock_name"], "'=1+1")
        self.assertEqual(float(row["asset_growth_yoy"]), -0.25)

    def test_selections_never_mutate_original_strategy_or_downloads(self):
        paths = [
            "portfolio",
            "overview",
            "equity",
            "rankings?date=2026-08-28",
            "downloads/predictions",
            "downloads/equity",
        ]
        before = {path: self.client.get(PREFIX + "/" + path).content for path in paths}
        for tickers in ("TJX", "SCL,CMG", "ANF,UTZ,URBN"):
            d = self.query(tickers).json()
            self.assertFalse(d["watchlist_changes_strategy"])
            self.assertEqual(
                d["strategy_context"]["metrics"],
                json.loads(before["portfolio"])["metrics"],
            )
        for path, original in before.items():
            self.assertEqual(self.client.get(PREFIX + "/" + path).content, original)

    def test_invalid_and_unsupported_requests_are_structured_errors(self):
        for params in [
            {"date": "2026-08-28", "tickers": "SCL,AAPL"},
            {"date": "2026-08-28", "tickers": " , "},
            {
                "date": "2026-08-28",
                "tickers": ",".join("X" + str(i) for i in range(41)),
            },
            {"date": "bad", "tickers": "SCL"},
            {"tickers": "SCL"},
            {"date": "2026-08-28"},
        ]:
            with self.subTest(params=params):
                response = self.client.get(PREFIX + "/watchlist", params=params)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["status"], "error")
                self.assertEqual(
                    response.json()["error"]["request_id"],
                    response.headers["x-request-id"],
                )
        unsupported = self.query("SCL,AAPL").json()
        self.assertEqual(unsupported["error"]["code"], "unsupported_stocks")
        self.assertEqual(self.client.post(PREFIX + "/watchlist").status_code, 405)
        self.assertEqual(
            self.client.get(
                PREFIX.replace("configured", "missing") + "/stocks"
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                PREFIX + "/watchlist/download?tickers=SCL&date=2026-08-28&format=bad"
            ).status_code,
            422,
        )
