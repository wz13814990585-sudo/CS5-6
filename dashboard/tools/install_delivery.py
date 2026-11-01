"""Create an isolated runtime for the unpacked customer delivery. Python 3.12."""

from pathlib import Path
import subprocess
import sys
import venv
from verify_delivery import verify

ROOT = Path(__file__).resolve().parent
if __name__ == "__main__":
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Use Python 3.12 for the verified runtime.")
    print(verify(ROOT))
    target = ROOT / ".venv-dashboard"
    if target.exists():
        raise SystemExit(
            "Environment already exists; use it or create a fresh unpacked delivery."
        )
    venv.EnvBuilder(with_pip=True).create(target)
    python = target / (
        "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    )
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-r",
            str(ROOT / "dashboard/requirements.txt"),
        ],
        check=True,
    )
    print("Installation complete. Run:")
    print(
        f'"{python}" "{ROOT / "dashboard/start.py"}" --config "{ROOT / "config.toml"}"'
    )
