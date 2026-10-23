"""Verify the immutable files delivered in this package."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
manifest = json.loads((ROOT / "package_manifest.json").read_text())
errors = []
for name, expected in manifest["files_sha256"].items():
    path = ROOT / name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        errors.append(name)
if errors:
    raise SystemExit("Missing or changed delivery files: " + ", ".join(errors))
print(f"Passed: {len(manifest['files_sha256'])} delivery files match SHA-256.")
