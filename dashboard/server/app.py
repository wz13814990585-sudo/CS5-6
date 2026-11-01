"""Same-origin frontend and read-only API. Start from the repository root."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from urllib.parse import urlsplit
from datetime import date as Date

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .data import discover

ROOT = Path(__file__).resolve().parents[2]


def frame_sources(raw: str) -> str:
    values = ["'self'"]
    for origin in raw.split(","):
        origin = origin.strip()
        if not origin:
            continue
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or any(c.isspace() for c in origin)
            or any(c in origin for c in "*;'\\")
        ):
            raise ValueError(
                "SAFECAPITAL_EMBED_ORIGINS requires comma-separated exact http(s) origins without trailing slashes"
            )
        _ = parsed.port  # Reject invalid port syntax.
        values.append(origin)
    return " ".join(values)


def create_app(
    root: Path = ROOT, explicit: Path | None = None, origins: str | None = None
) -> FastAPI:
    ancestors = frame_sources(
        origins if origins is not None else os.getenv("SAFECAPITAL_EMBED_ORIGINS", "")
    )
    configured = explicit or (
        Path(os.environ["SAFECAPITAL_RESULT_DIR"])
        if os.getenv("SAFECAPITAL_RESULT_DIR")
        else None
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.runs, app.state.rejected = discover(root, configured)
        yield

    app = FastAPI(
        title="SafeCapital Dashboard API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; "
            f"base-uri 'self'; frame-ancestors {ancestors}"
        )
        # Swagger's optional documentation UI loads its assets from this pinned upstream CDN.
        if request.url.path == "/api/docs":
            response.headers["Content-Security-Policy"] = (
                f"frame-ancestors {ancestors}; object-src 'none'"
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def get_run(run_id):
        if run_id not in app.state.runs:
            raise HTTPException(404, "未找到校验通过的回放结果")
        return app.state.runs[run_id]

    @app.get("/api/health")
    def health():
        if not app.state.runs:
            raise HTTPException(
                503, "没有可用的已验证结果，请运行默认流程后重启 Dashboard"
            )
        return {
            "status": "ok",
            "verified_runs": len(app.state.runs),
            "rejected_runs": app.state.rejected,
        }

    @app.get("/api/runs")
    def runs():
        items = [r.info for r in app.state.runs.values()]
        return {
            "runs": items,
            "default_run_id": items[0]["id"] if items else None,
            "rejected_runs": app.state.rejected,
        }

    @app.get("/api/runs/{run_id}/overview")
    def overview(run_id: str):
        return get_run(run_id).overview

    @app.get("/api/runs/{run_id}/equity")
    def equity(run_id: str):
        return {"rows": get_run(run_id).equity}

    @app.get("/api/runs/{run_id}/rankings")
    def rankings(
        run_id: str,
        date: Date,
        q: str = Query("", max_length=30),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
    ):
        replay = get_run(run_id)
        key = date.isoformat()
        if key not in replay.rankings:
            raise HTTPException(404, "该日期没有预测记录，请选择可用信号日期")
        rows = [
            r for r in replay.rankings[key] if q.strip().upper() in r["ticker"].upper()
        ]
        start = (page - 1) * page_size
        return {
            "date": key,
            "total": len(rows),
            "page": page,
            "page_size": page_size,
            "rows": rows[start : start + page_size],
        }

    @app.get("/api/runs/{run_id}/downloads/{kind}")
    def download(run_id: str, kind: str):
        replay = get_run(run_id)
        if kind not in replay.downloads:
            raise HTTPException(404, "Unknown download")
        ext = "csv" if kind in {"predictions", "equity", "summary"} else "json"
        return Response(
            replay.downloads[kind],
            media_type="text/csv" if ext == "csv" else "application/json",
            headers={
                "Content-Disposition": f'attachment; filename="safecapital-{run_id}-{kind}.{ext}"'
            },
        )

    # Mount only built frontend assets; never expose the repository or arbitrary files.
    dist = root / "dashboard/frontend/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="dashboard")
    return app


app = create_app()
