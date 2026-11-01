import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
from dashboard.server.app import create_app, ROOT
from dashboard.server.config import Settings
from dashboard.tools.verify_delivery import verify

SOURCE = ROOT / "FINAL_OUTPUTS/01_saved_model_replay/verified_replay"


class IntegrationTests(unittest.TestCase):
    def test_config_precedence_and_relative_result_path(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.toml"
            path.write_text(
                'port=8001\nresult_dir="results"\npublic_url="https://research.example/"\n'
            )
            settings = Settings.load(path, {"SAFECAPITAL_PORT": "8010"})
            self.assertEqual(settings.port, 8010)
            self.assertEqual(settings.result_dir, (Path(temp) / "results").resolve())
            self.assertEqual(settings.override(port=8020).port, 8020)
            self.assertEqual(settings.port, 8010)

    def test_bad_configuration_fails(self):
        for text in [
            "port=0",
            "port=3.5",
            "host=2",
            "unknown=1",
            'public_url="https://a.example/sub/"',
            'api_origins="*"',
            'embed_origins="https://user:pass@a.example"',
            "result_dir=123",
        ]:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "config.toml"
                path.write_text(text)
                with self.assertRaises(ValueError):
                    Settings.load(path, {})
        with self.assertRaises(ValueError):
            Settings(public_url="https://a.example,").validate()

    def test_versioned_api_and_legacy_match(self):
        with TestClient(create_app(explicit=SOURCE, settings=Settings())) as client:
            for suffix in [
                "health",
                "runs",
                "runs/configured/overview",
                "runs/configured/equity",
                "runs/configured/rankings?date=2026-08-28",
            ]:
                with self.subTest(suffix=suffix):
                    a = client.get("/api/" + suffix)
                    b = client.get("/api/v1/" + suffix)
                    self.assertEqual(a.status_code, 200)
                    self.assertEqual(a.json(), b.json())

    def test_cors_is_separate_from_embedding(self):
        settings = Settings(
            api_origins="https://api-client.example",
            embed_origins="https://frame-client.example",
        )
        with TestClient(create_app(explicit=SOURCE, settings=settings)) as client:
            allowed = client.get(
                "/api/v1/runs", headers={"Origin": "https://api-client.example"}
            )
            self.assertEqual(
                allowed.headers["access-control-allow-origin"],
                "https://api-client.example",
            )
            self.assertNotIn("access-control-allow-credentials", allowed.headers)
            denied = client.get(
                "/api/v1/runs", headers={"Origin": "https://frame-client.example"}
            )
            self.assertNotIn("access-control-allow-origin", denied.headers)
            self.assertIn(
                "https://frame-client.example",
                denied.headers["content-security-policy"],
            )
            preflight = client.options(
                "/api/v1/runs",
                headers={
                    "Origin": "https://api-client.example",
                    "Access-Control-Request-Method": "GET",
                },
            )
            self.assertEqual(preflight.status_code, 200)
            denied_method = client.options(
                "/api/v1/runs",
                headers={
                    "Origin": "https://api-client.example",
                    "Access-Control-Request-Method": "POST",
                },
            )
            self.assertEqual(denied_method.status_code, 400)

    def test_error_contract_and_request_id(self):
        with TestClient(create_app(explicit=SOURCE, settings=Settings())) as client:
            for path, status, code in [
                ("/api/v1/runs/nope/overview", 404, "not_found"),
                ("/api/v1/runs/configured/rankings?date=bad", 422, "invalid_request"),
            ]:
                response = client.get(path)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()["error"]["code"], code)
                self.assertEqual(
                    response.json()["error"]["request_id"],
                    response.headers["x-request-id"],
                )
                self.assertNotIn(str(ROOT), response.text)

    def test_public_config_does_not_expose_private_paths(self):
        settings = Settings(public_url="https://research.example/", result_dir=SOURCE)
        with TestClient(create_app(settings=settings)) as client:
            result = client.get("/api/v1/config")
            self.assertEqual(result.json()["public_url"], "https://research.example/")
            self.assertNotIn(str(SOURCE), result.text)
            self.assertEqual(result.json()["api_version"], "v1")

    def test_openapi_defines_response_and_error_schemas(self):
        schema = create_app(settings=Settings()).openapi()
        self.assertIn("/api/v1/runs/{run_id}/overview", schema["paths"])
        self.assertNotIn("/api/runs", schema["paths"])
        endpoint = schema["paths"]["/api/v1/runs/{run_id}/rankings"]["get"]
        self.assertEqual(
            endpoint["responses"]["200"]["content"]["application/json"]["schema"][
                "$ref"
            ],
            "#/components/schemas/Rankings",
        )
        self.assertEqual(
            endpoint["responses"]["422"]["content"]["application/json"]["schema"][
                "$ref"
            ],
            "#/components/schemas/ErrorResponse",
        )

    def test_delivery_integrity_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "file.txt").write_bytes(b"real")
            record = {
                "schema_version": 1,
                "version": "test",
                "files": {
                    "file.txt": {
                        "bytes": 4,
                        "sha256": hashlib.sha256(b"real").hexdigest(),
                    }
                },
            }
            (root / "DELIVERY_MANIFEST.json").write_text(json.dumps(record))
            self.assertEqual(verify(root)["status"], "passed")
            (root / "file.txt").write_bytes(b"fake")
            with self.assertRaises(ValueError):
                verify(root)


if __name__ == "__main__":
    unittest.main()
