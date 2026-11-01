"""Verify the customer package against DELIVERY_MANIFEST.json (standard library only)."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def verify(root):
    root = Path(root).resolve()
    manifest = json.loads((root / "DELIVERY_MANIFEST.json").read_text("utf-8"))
    if manifest.get("schema_version") != 1 or not manifest.get("files"):
        raise ValueError("Invalid delivery manifest")
    errors = []
    for name, expected in manifest["files"].items():
        parts = name.split("/")
        if (
            PurePosixPath(name).is_absolute()
            or any(x in ("", ".", "..") for x in parts)
            or "\\" in name
            or ":" in name
        ):
            errors.append(f"Unsafe path: {name}")
            continue
        path = root / name
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(root)
            or not path.is_file()
        ):
            errors.append(f"Missing/unsafe file: {name}")
            continue
        content = path.read_bytes()
        if (
            len(content) != expected["bytes"]
            or hashlib.sha256(content).hexdigest() != expected["sha256"]
        ):
            errors.append(f"File mismatch: {name}")
    if errors:
        raise ValueError("\n".join(errors))
    return {
        "status": "passed",
        "checked_files": len(manifest["files"]),
        "version": manifest["version"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Delivery verification failed: {exc}\n")
