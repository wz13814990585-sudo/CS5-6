"""Same-origin frontend and read-only API. Start from the repository root."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import uuid
from pathlib import Path
from datetime import date as Date
from typing import Literal

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .data import discover
from .config import Settings, frame_sources, exact_origins
from . import schemas
from .inputs import load_source, bind

ROOT = Path(__file__).resolve().parents[2]


def create_app(
    root: Path = ROOT,
    explicit: Path | None = None,
    origins: str | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or Settings.load()
    settings.validate()
    ancestors = frame_sources(
        origins if origins is not None else settings.embed_origins
    )
    configured = explicit or settings.result_dir

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.runs, app.state.rejected = discover(root, configured)
        for replay in app.state.runs.values():
            schemas.Overview.model_validate(replay.overview)
            schemas.Equity.model_validate({"rows": replay.equity})
        app.state.inputs = {}
        try:
            source = load_source(root)
        except (OSError, ValueError, KeyError, TypeError):
            source = None
        for run_id, replay in app.state.runs.items():
            try:
                if source is None:
                    raise ValueError("Input files unavailable")
                app.state.inputs[run_id] = bind(source, replay)
            except (ValueError, KeyError, TypeError):
                app.state.inputs[run_id] = None
        yield

    app = FastAPI(
        title="SafeCapital Dashboard API",
        version="1.2.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(exact_origins(settings.api_origins)),
        allow_methods=["GET"],
        allow_headers=["Accept"],
        expose_headers=["Content-Disposition", "X-Request-ID"],
        allow_credentials=False,
    )
    router = APIRouter(
        responses={
            status: {"model": schemas.ErrorResponse}
            for status in (404, 405, 422, 500, 503)
        }
    )

    def error_response(request, status, code, message, fields=None):
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": getattr(request.state, "request_id", ""),
                    "fields": fields or [],
                },
                "detail": message,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        code = {
            404: "not_found",
            405: "method_not_allowed",
            503: "no_verified_results",
        }.get(exc.status_code, "http_error")
        if isinstance(exc.detail, dict):
            code, message = exc.detail["code"], exc.detail["message"]
        else:
            message = str(exc.detail)
        return error_response(request, exc.status_code, code, message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = [".".join(str(x) for x in e["loc"]) for e in exc.errors()]
        return error_response(
            request, 422, "invalid_request", "请求参数不符合接口约定", fields
        )

    @app.middleware("http")
    async def headers(request, call_next):
        request.state.request_id = uuid.uuid4().hex
        try:
            response = await call_next(request)
        except Exception:
            logging.getLogger("safecapital").exception(
                "Request failed id=%s", request.state.request_id
            )
            response = error_response(
                request,
                500,
                "internal_error",
                "服务暂时不可用，请提供请求编号联系维护人员",
            )
        response.headers["X-Request-ID"] = request.state.request_id
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

    @router.get("/config", response_model=schemas.PublicConfig)
    def config():
        return {
            "app_version": "1.2.0",
            "api_version": "v1",
            "public_url": settings.public_url,
            "data_mode": "historical_read_only",
        }

    @router.get("/health", response_model=schemas.Health)
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

    @router.get("/runs", response_model=schemas.Runs)
    def runs():
        items = [r.info for r in app.state.runs.values()]
        return {
            "runs": items,
            "default_run_id": items[0]["id"] if items else None,
            "rejected_runs": app.state.rejected,
        }

    @router.get("/runs/{run_id}/overview", response_model=schemas.Overview)
    def overview(run_id: str):
        return get_run(run_id).overview

    @router.get("/runs/{run_id}/equity", response_model=schemas.Equity)
    def equity(run_id: str):
        return {"rows": get_run(run_id).equity}

    @router.get("/runs/{run_id}/rankings", response_model=schemas.Rankings)
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

    @router.get(
        "/runs/{run_id}/downloads/{kind}",
        response_class=Response,
        responses={
            200: {
                "description": "Exact original verified file bytes",
                "content": {"text/csv": {}, "application/json": {}},
            }
        },
    )
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

    def get_inputs(run_id):
        get_run(run_id)
        inputs = app.state.inputs.get(run_id)
        if inputs is None:
            raise HTTPException(
                503,
                {
                    "code": "inputs_unavailable",
                    "message": "缺少与本次运行一致的输入文件，或输入校验未通过；输出仍可独立查看。",
                },
            )
        return inputs

    @router.get("/runs/{run_id}/inputs", response_model=schemas.InputCatalog)
    def input_catalog(run_id: str):
        get_run(run_id)
        inputs = app.state.inputs.get(run_id)
        if inputs is None:
            return {
                "available": False,
                "reason": "缺少与本次运行一致的输入文件，或输入校验未通过；输出仍可独立查看。",
                "run_id": run_id,
                "datasets": [],
                "model": None,
            }
        return inputs["catalog"]

    @router.get(
        "/runs/{run_id}/inputs/{dataset}/rows", response_model=schemas.InputRows
    )
    def input_rows(
        run_id: str,
        dataset: Literal["factors", "prices"],
        date: Date | None = None,
        scope: Literal["output", "source"] = "output",
        q: str = Query("", max_length=30),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
    ):
        inputs = get_inputs(run_id)
        table = (
            inputs["aligned"][dataset]
            if scope == "output"
            else inputs["source"].tables[dataset]
        )
        key = date.isoformat() if date else None
        rows = [
            r
            for r in table
            if (key is None or r["date"] == key)
            and q.strip().upper() in r["ticker"].upper()
        ]
        start = (page - 1) * page_size
        return {
            "dataset": dataset,
            "scope": scope,
            "date": key,
            "total": len(rows),
            "page": page,
            "page_size": page_size,
            "rows": rows[start : start + page_size],
        }

    @router.get(
        "/runs/{run_id}/inputs/{dataset}/download",
        response_class=Response,
        responses={
            200: {
                "description": "Complete original input CSV, including research label columns",
                "content": {"text/csv": {}},
            }
        },
    )
    def input_download(run_id: str, dataset: Literal["factors", "prices"]):
        inputs = get_inputs(run_id)
        return Response(
            inputs["source"].content[dataset],
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="safecapital-{run_id}-input-{dataset}.csv"'
            },
        )

    app.include_router(router, prefix="/api/v1")
    app.include_router(router, prefix="/api", include_in_schema=False)

    # Mount only built frontend assets; never expose the repository or arbitrary files.
    dist = root / "dashboard/frontend/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="dashboard")
    return app


app = create_app()
