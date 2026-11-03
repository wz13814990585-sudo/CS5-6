"""Build a portable customer ZIP from an explicitly validated real replay."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import posixpath
import re
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
from dashboard.server.portfolio import load_archive, contract
from dashboard.server.watchlist import inspect_stocks

VERSION = "1.4.0"


def package_documentation(dest, tracked):
    """Include both language pages and their linked reference files offline."""
    tracked = {name for name in tracked if name}
    readmes = {name for name in tracked if "readme" in Path(name).name.lower()}
    pairs = {}
    for name in sorted(readmes):
        if name.endswith(".zh-CN.md"):
            continue
        translated = str(Path(name).with_name(Path(name).stem + ".zh-CN.md"))
        if translated not in readmes:
            raise ValueError(f"Missing README language counterpart: {name}")
        pairs[name] = translated
    pending = list(readmes)
    references = set(readmes)
    while pending:
        name = pending.pop()
        if Path(name).suffix != ".md":
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", (ROOT / name).read_text()):
            link = target.strip("<>").split("#", 1)[0]
            if not link or "://" in link or link.startswith(("/", "mailto:")):
                continue
            relative = posixpath.normpath(posixpath.join(str(Path(name).parent), link))
            if relative not in tracked:
                raise ValueError(f"Untracked documentation link: {name} -> {relative}")
            if relative not in references:
                references.add(relative)
                pending.append(relative)
    for name in sorted(references):
        source = ROOT / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Unsafe documentation source: {name}")
        target = dest / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    notices = {
        "README.md": "> **Web runtime package:** Follow [START_HERE.md](START_HERE.md). Python 3.12 is required; Node.js, Docker and model training are not needed to run Web. Research README pages describe the full Source package; this runtime does not include every research program, dataset or model weight. Verify this package with `verify_delivery.py` and `DELIVERY_MANIFEST.json`.",
        "README.zh-CN.md": "> **Web 运行包：**请按 [START_HERE.zh-CN.md](START_HERE.zh-CN.md) 安装。运行需要 Python 3.12，不需要 Node.js、Docker 或模型训练。研究 README 描述完整源码包，本运行包不包含全部研究程序、数据和模型权重。使用 `verify_delivery.py` 和 `DELIVERY_MANIFEST.json` 核验本包。",
    }
    for name, notice in notices.items():
        path = dest / name
        lines = path.read_text().splitlines()
        nav = next(i for i, line in enumerate(lines) if "[中文](" in line or "[English](" in line)
        lines[nav + 1:nav + 1] = ["", notice]
        path.write_text("\n".join(lines) + "\n")
    return {
        "mode": "separate_language_pages",
        "default_language": "en",
        "readme_groups": len(pairs),
        "readme_pages": len(readmes),
        "readme_pairs": pairs,
        "root_indexes": ["README.md#readme-index", "README.zh-CN.md#readme-index"],
        "linked_reference_files": len(references),
        "package_note": "Root language pages add matching-language runtime instructions. Other README pages match the source commit.",
    }


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
    bound_inputs = bind(inputs, replay)
    archive = load_archive(ROOT)
    module_result = contract(replay, bound_inputs, archive)
    if module_result["status"] != "success":
        raise ValueError("Package requires matching verified portfolio allocations")
    watchlist = inspect_stocks(
        replay, bound_inputs, archive, module_result["signal_date"], "SCL,TJX,CMG"
    )
    if watchlist["status"] != "success":
        raise ValueError(
            "Package requires complete watchlist demonstration inputs and outputs"
        )
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
                    ".png",
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
            "START_HERE.md": "START_HERE.md",
            "START_HERE.zh-CN.md": "START_HERE.zh-CN.md",
            "dashboard/compose.delivery.yaml": "compose.yaml",
            "dashboard/Dockerfile.delivery": "Dockerfile",
            "dashboard/.dockerignore.delivery": ".dockerignore",
            "NOTICE.md": "NOTICE.md",
        }
        for src, to in mappings.items():
            shutil.copyfile(ROOT / src, dest / to)
        documentation = package_documentation(dest, tracked)
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
            "delivery_revision": "2026-11-03-language-switch",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_worktree_dirty": bool(
                subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
            ),
            "result": replay.info,
            "documentation": documentation,
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
