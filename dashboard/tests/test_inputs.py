import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
from dashboard.server.app import ROOT, create_app
from dashboard.server.config import Settings
from dashboard.server.inputs import INPUT_FILES, load_source, bind
from dashboard.server.data import load_replay

SOURCE = ROOT / "FINAL_OUTPUTS/01_saved_model_replay/verified_replay"


class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(create_app(explicit=SOURCE, settings=Settings()))
        cls.client = cls.context.__enter__()
        cls.prefix = "/api/v1/runs/configured/inputs"

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_catalog_links_source_and_output_coverage(self):
        c = self.client.get(self.prefix).json()
        self.assertTrue(c["available"])
        self.assertEqual(c["model"]["snapshot_count"], 45)
        f, p = c["datasets"]
        self.assertEqual(f["source_rows"], 17353)
        self.assertEqual(len(f["source_dates"]), 574)
        self.assertEqual(f["output_aligned_rows"], 13517)
        self.assertEqual(len(f["output_dates"]), 366)
        self.assertEqual(p["output_aligned_rows"], 8354)
        self.assertEqual(len(p["output_dates"]), 210)
        self.assertEqual(f["omitted_columns"], ["target1", "target2"])
        self.assertFalse(Path(f["source_file"]).is_absolute())

    def test_factor_rows_equal_original_and_omit_labels(self):
        response = self.client.get(
            self.prefix + "/factors/rows", params={"date": "2026-08-28", "q": "anf"}
        ).json()
        self.assertEqual(response["total"], 1)
        row = response["rows"][0]
        original = next(
            r
            for r in csv.DictReader(
                (ROOT / INPUT_FILES["factors"]).open(encoding="utf-8-sig")
            )
            if r["date"] == "2026-08-28" and r["ticker"] == "ANF"
        )
        for key in (
            "revenue_growth_yoy",
            "operating_profitability",
            "cashflow_to_assets",
            "debt_to_assets",
            "asset_growth_yoy",
        ):
            self.assertEqual(row[key], float(original[key]))
        self.assertNotIn("target1", row)
        self.assertNotIn("target2", row)

    def test_source_history_and_output_scope_are_distinct(self):
        output = self.client.get(
            self.prefix + "/factors/rows", params={"date": "2015-09-04"}
        ).json()
        original = self.client.get(
            self.prefix + "/factors/rows",
            params={"date": "2015-09-04", "scope": "source"},
        ).json()
        self.assertEqual(output["total"], 0)
        self.assertGreater(original["total"], 0)
        self.assertEqual(
            self.client.get(self.prefix + "/prices/rows").json()["total"], 8354
        )
        self.assertEqual(
            self.client.get(
                self.prefix + "/prices/rows", params={"scope": "source"}
            ).json()["total"],
            17353,
        )

    def test_pagination_filter_and_invalid_requests(self):
        first = self.client.get(
            self.prefix + "/factors/rows", params={"date": "2026-08-28"}
        ).json()
        second = self.client.get(
            self.prefix + "/factors/rows", params={"date": "2026-08-28", "page": 2}
        ).json()
        self.assertEqual(len(first["rows"]), 10)
        self.assertEqual(first["total"], 40)
        self.assertFalse(
            {r["ticker"] for r in first["rows"]} & {r["ticker"] for r in second["rows"]}
        )
        self.assertEqual(
            self.client.get(
                self.prefix + "/factors/rows", params={"q": "NO_SUCH_STOCK"}
            ).json()["rows"],
            [],
        )
        for path in [
            "/unknown/rows",
            "/factors/rows?date=wrong",
            "/factors/rows?scope=bad",
            "/prices/rows?page=0",
            "/prices/rows?page_size=101",
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(self.prefix + path).status_code, 422)
        self.assertEqual(
            self.client.post(self.prefix + "/factors/rows").status_code, 405
        )

    def test_price_fields_and_raw_download_identity(self):
        rows = self.client.get(
            self.prefix + "/prices/rows", params={"date": "2026-08-28"}
        ).json()["rows"]
        self.assertIn("buy_price", rows[0])
        self.assertIn("sell_price", rows[0])
        self.assertNotIn("revenue_growth_yoy", rows[0])
        for key in ("factors", "prices"):
            response = self.client.get(self.prefix + "/" + key + "/download")
            self.assertEqual(response.content, (ROOT / INPUT_FILES[key]).read_bytes())
            self.assertIn("attachment", response.headers["content-disposition"])
            self.assertIn(
                "target1",
                next(csv.reader(io.StringIO(response.content.decode("utf-8-sig")))),
            )

    def test_missing_inputs_do_not_break_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            with TestClient(
                create_app(root=Path(root), explicit=SOURCE, settings=Settings())
            ) as client:
                self.assertFalse(client.get(self.prefix).json()["available"])
                response = client.get(self.prefix + "/factors/rows")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["error"]["code"], "inputs_unavailable")
                self.assertEqual(
                    client.get("/api/v1/runs/configured/overview").status_code, 200
                )

    def test_unrelated_inputs_cannot_be_bound_to_output(self):
        source = load_source(ROOT)
        replay = load_replay(SOURCE, "test")
        verification = json.loads(replay.downloads["backtest-verification"])
        verification["price_sha256"] = "0" * 64
        replay.downloads["backtest-verification"] = json.dumps(verification).encode()
        with self.assertRaises(ValueError):
            bind(source, replay)


if __name__ == "__main__":
    unittest.main()
