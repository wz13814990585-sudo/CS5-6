"""API acceptance tests against real delivered results and isolated corrupt copies."""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from fastapi.testclient import TestClient
from dashboard.server.app import ROOT, create_app, frame_sources
from dashboard.server.data import discover, load_replay

SOURCE = ROOT / "FINAL_OUTPUTS/01_saved_model_replay/verified_replay"


class RealResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(
            create_app(explicit=SOURCE, origins="https://client.example")
        )
        cls.client = cls.client_context.__enter__()
        cls.prefix = "/api/runs/configured"

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_overview_uses_real_results(self):
        result = self.client.get(self.prefix + "/overview").json()
        self.assertEqual(result["run"]["prediction_rows"], 13517)
        self.assertEqual(len(result["dates"]), 366)
        self.assertEqual(result["ticker_count"], 40)
        self.assertAlmostEqual(result["summary"]["final_capital"], 149330.60888418998)
        self.assertAlmostEqual(result["summary"]["total_return"], 0.49330608884189986)
        self.assertEqual(self.client.get("/api/health").status_code, 200)

    def test_equity_and_derived_drawdown_match_summary(self):
        rows = self.client.get(self.prefix + "/equity").json()["rows"]
        summary = self.client.get(self.prefix + "/overview").json()["summary"]
        self.assertEqual(len(rows), 210)
        self.assertEqual(rows[-1]["end_capital"], summary["final_capital"])
        self.assertAlmostEqual(
            min(r["drawdown"] for r in rows), summary["max_drawdown"]
        )

    def test_date_search_and_pagination(self):
        path = self.prefix + "/rankings"
        first = self.client.get(path, params={"date": "2026-08-28"}).json()
        second = self.client.get(path, params={"date": "2026-08-28", "page": 2}).json()
        self.assertEqual(first["total"], 40)
        self.assertEqual(first["rows"][0]["ticker"], "SCL")
        self.assertEqual(
            [r["ensemble_predicted_rank"] for r in first["rows"]], list(range(1, 11))
        )
        self.assertFalse(
            {r["ticker"] for r in first["rows"]} & {r["ticker"] for r in second["rows"]}
        )
        match = self.client.get(path, params={"date": "2026-08-28", "q": "anf"}).json()
        self.assertEqual(match["total"], 1)
        self.assertEqual(match["rows"][0]["ticker"], "ANF")
        empty = self.client.get(
            path, params={"date": "2026-08-28", "q": "NO_SUCH_TICKER"}
        ).json()
        self.assertEqual(empty["rows"], [])
        self.assertEqual(
            self.client.get(path, params={"date": "2019-08-30"}).json()["total"], 27
        )

    def test_invalid_queries_and_unknown_runs(self):
        for params, code in [
            ({"date": "not-date"}, 422),
            ({"date": "2026-08-29"}, 404),
            ({"date": "2026-08-28", "page": 0}, 422),
            ({"date": "2026-08-28", "page_size": 1000}, 422),
        ]:
            with self.subTest(params=params):
                self.assertEqual(
                    self.client.get(
                        self.prefix + "/rankings", params=params
                    ).status_code,
                    code,
                )
        self.assertEqual(self.client.get("/api/runs/missing/overview").status_code, 404)
        self.assertEqual(self.client.post("/api/runs").status_code, 405)

    def test_downloads_are_exact_verified_bytes(self):
        for kind, path in [
            ("predictions", "saved_model_predictions.csv"),
            ("equity", "backtest/weekly_capital.csv"),
            ("summary", "backtest/summary.csv"),
            ("manifest", "manifest.json"),
        ]:
            with self.subTest(kind=kind):
                response = self.client.get(self.prefix + "/downloads/" + kind)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, (SOURCE / path).read_bytes())
                self.assertIn("attachment;", response.headers["content-disposition"])
        self.assertEqual(
            self.client.get(self.prefix + "/downloads/requirements.txt").status_code,
            404,
        )
        self.assertEqual(self.client.get("/requirements.txt").status_code, 404)
        self.assertEqual(self.client.get("/dashboard/server/app.py").status_code, 404)

    def test_frame_policy_and_no_cross_origin_api_grant(self):
        response = self.client.get(
            "/api/runs", headers={"Origin": "https://untrusted.example"}
        )
        self.assertIn(
            "frame-ancestors 'self' https://client.example",
            response.headers["content-security-policy"],
        )
        self.assertNotIn("access-control-allow-origin", response.headers)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_built_ui_and_embed_example(self):
        for url in ["/", "/?embed=1", "/embed-example.html"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("iframe", self.client.get("/embed-example.html").text)


class ResultIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.folder = self.root / "runs/replay"
        shutil.copytree(SOURCE, self.folder)

    def change_manifest(self, edit):
        path = self.folder / "manifest.json"
        data = json.loads(path.read_text())
        edit(data)
        path.write_text(json.dumps(data))

    def test_tampered_result_is_excluded(self):
        (self.folder / "backtest/summary.csv").write_text("tampered")
        runs, rejected = discover(self.root)
        self.assertEqual(runs, {})
        self.assertEqual(rejected, 1)
        with TestClient(create_app(root=self.root, origins="")) as client:
            self.assertEqual(client.get("/api/health").status_code, 503)
            self.assertIsNone(client.get("/api/runs").json()["default_run_id"])

    def test_explicit_invalid_result_never_falls_back(self):
        self.change_manifest(lambda m: m.update(status="failed"))
        with self.assertRaises(ValueError):
            discover(ROOT, self.folder)

    def test_missing_artifact_is_rejected(self):
        (self.folder / "saved_model_predictions.csv").unlink()
        self.assertEqual(discover(self.root)[0], {})

    def test_manifest_paths_cannot_escape(self):
        self.change_manifest(lambda m: m["files"].update({"../outside": "a" * 64}))
        with self.assertRaises(ValueError):
            load_replay(self.folder, "test")

    def test_symlink_cannot_escape(self):
        artifact = self.folder / "saved_model_predictions.csv"
        outside = self.root / "outside.csv"
        artifact.rename(outside)
        artifact.symlink_to(outside)
        with self.assertRaises(ValueError):
            load_replay(self.folder, "test")

    def test_served_snapshot_is_immutable_until_restart(self):
        result = load_replay(self.folder, "test")
        before = result.downloads["summary"]
        (self.folder / "backtest/summary.csv").write_text("changed after startup")
        self.assertEqual(result.downloads["summary"], before)
        self.assertAlmostEqual(
            result.overview["summary"]["final_capital"], 149330.60888418998
        )

    def test_non_finite_numeric_data_is_rejected(self):
        path = self.folder / "backtest/weekly_capital.csv"
        content = path.read_text().replace("99171.861807464593", "NaN", 1)
        self.assertIn("NaN", content)
        path.write_text(content)
        self.change_manifest(
            lambda m: m["files"].update(
                {
                    "backtest/weekly_capital.csv": hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
                }
            )
        )
        with self.assertRaises(ValueError):
            load_replay(self.folder, "test")

    def test_embedding_origin_validation(self):
        self.assertEqual(frame_sources(""), "'self'")
        self.assertIn(
            "http://localhost:9000",
            frame_sources("https://customer.example,http://localhost:9000"),
        )
        for raw in [
            "*",
            "https://example.com/",
            "https://example.com; script-src *",
            "https://user:pass@example.com",
            "javascript:alert(1)",
            "https://example.com\nhttps://bad.example",
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                frame_sources(raw)


if __name__ == "__main__":
    unittest.main()
