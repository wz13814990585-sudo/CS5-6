"""Build a portable customer ZIP from an explicitly validated real replay."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from dashboard.server.data import discover, load_replay
from dashboard.server.app import create_app
from dashboard.server.config import Settings
from dashboard.server.inputs import INPUT_FILES, load_source, bind
from dashboard.tools.verify_delivery import verify

VERSION = "1.2.0"


def build(output, result=None):
    dist = ROOT / "dashboard/frontend/dist"
    if not (dist / "index.html").is_file():
        raise ValueError(
            "Build frontend first: npm --prefix dashboard/frontend run build"
        )
    if result:
        replay = load_replay(result, "delivery")
        folder = Path(result)
    else:
        runs, _ = discover(ROOT)
        if not runs:
            raise ValueError("No verified replay")
        run_id, replay = next(iter(runs.items()))
        folder = ROOT / (
            "FINAL_OUTPUTS/01_saved_model_replay/verified_replay"
            if run_id == "delivered"
            else f"runs/{run_id}"
        )
    inputs = load_source(ROOT)
    bind(inputs, replay)
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Delivery already exists: {output}")
    with tempfile.TemporaryDirectory(prefix="safecapital-package-") as temporary:
        dest = Path(temporary) / f"SafeCapital-Web-{VERSION}"
        dest.mkdir()
        # Explicit source whitelist: no .env, local config, caches or arbitrary project files.
        tracked = (
            subprocess.check_output(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                cwd=ROOT,
            )
            .decode()
            .split("\0")
        )
        for name in tracked:
            if (
                name
                and name.startswith("dashboard/")
                and Path(name).suffix
                in {
                    ".py",
                    ".ts",
                    ".tsx",
                    ".css",
                    ".html",
                    ".svg",
                    ".json",
                    ".txt",
                    ".in",
                    ".md",
                    ".example",
                    ".toml",
                    ".yaml",
                    ".mjs",
                    ".jpg",
                }
            ):
                if name.endswith("/config.toml"):
                    continue
                p = ROOT / name
                if p.is_symlink():
                    raise ValueError("Symlink in source package")
                out = dest / name
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, out)
        shutil.copytree(dist, dest / "dashboard/frontend/dist")
        for key, name in INPUT_FILES.items():
            path = dest / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(inputs.content[key])
        relative = "FINAL_OUTPUTS/01_saved_model_replay/verified_replay"
        target = dest / relative
        target.mkdir(parents=True)
        # Use verified in-memory bytes; never copy unrelated files from a run folder.
        manifest = json.loads(replay.downloads["manifest"])
        (target / "manifest.json").write_bytes(replay.downloads["manifest"])
        for name in manifest["files"]:
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            content = (folder / name).read_bytes()
            if hashlib.sha256(content).hexdigest() != manifest["files"][name]:
                raise ValueError("Result changed during packaging")
            path.write_bytes(content)
        mappings = {
            "dashboard/tools/install_delivery.py": "install.py",
            "dashboard/tools/verify_delivery.py": "verify_delivery.py",
            "dashboard/tools/smoke_check.py": "smoke_check.py",
            "dashboard/config.example.toml": "config.toml",
            "dashboard/docs/CUSTOMER_HANDOFF.md": "START_HERE.md",
            "dashboard/compose.delivery.yaml": "compose.yaml",
            "dashboard/Dockerfile.delivery": "Dockerfile",
            "dashboard/.dockerignore.delivery": ".dockerignore",
            "NOTICE.md": "NOTICE.md",
        }
        for src, to in mappings.items():
            shutil.copyfile(ROOT / src, dest / to)
        (dest / "dashboard/docs/openapi.json").write_text(
            json.dumps(
                create_app(settings=Settings()).openapi(), ensure_ascii=False, indent=2
            )
            + "\n"
        )
        files = {}
        for path in sorted(dest.rglob("*")):
            if path.is_file():
                content = path.read_bytes()
                files[path.relative_to(dest).as_posix()] = {
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "bytes": len(content),
                }
        record = {
            "schema_version": 1,
            "version": VERSION,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_worktree_dirty": bool(
                subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
            ),
            "result": replay.info,
            "files": files,
        }
        (dest / "DELIVERY_MANIFEST.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        )
        verify(dest)
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(dest.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(dest.parent))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n")
    return {
        "archive": str(output),
        "sha256": digest,
        "bytes": output.stat().st_size,
        "result": replay.info,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "deliveries" / f"SafeCapital-Web-{VERSION}.zip",
    )
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.result), ensure_ascii=False, indent=2))
