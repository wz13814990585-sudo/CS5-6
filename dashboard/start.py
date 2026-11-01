"""Start the built Dashboard without changing the original model environment."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not (ROOT / "dashboard/frontend/dist/index.html").is_file():
        parser.exit(
            2,
            "Frontend build missing. Run: npm --prefix dashboard/frontend ci && npm --prefix dashboard/frontend run build\n",
        )
    try:
        import uvicorn
        from dashboard.server.app import app
    except ImportError:
        parser.exit(
            2,
            "Install Dashboard dependencies in its environment: pip install -r dashboard/requirements.txt\n",
        )
    print(
        f"SafeCapital: http://{args.host}:{args.port}/\nEmbed mode: http://{args.host}:{args.port}/?embed=1",
        flush=True,
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
