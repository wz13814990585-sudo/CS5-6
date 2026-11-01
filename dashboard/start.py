"""Start the built Dashboard without changing the original model environment."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--config", type=Path, help="Deployment TOML file")
    args = parser.parse_args()
    if not (ROOT / "dashboard/frontend/dist/index.html").is_file():
        parser.exit(
            2,
            "Frontend build missing. Run: npm --prefix dashboard/frontend ci && npm --prefix dashboard/frontend run build\n",
        )
    try:
        import uvicorn
        from dashboard.server.app import create_app
        from dashboard.server.config import Settings

        settings = Settings.load(args.config).override(host=args.host, port=args.port)
        app = create_app(settings=settings)
    except ImportError:
        parser.exit(
            2,
            "Install Dashboard dependencies in its environment: pip install -r dashboard/requirements.txt\n",
        )
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Invalid Dashboard configuration: {exc}\n")
    print(
        f"SafeCapital: http://{settings.host}:{settings.port}/\nEmbed mode: http://{settings.host}:{settings.port}/?embed=1",
        flush=True,
    )
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
