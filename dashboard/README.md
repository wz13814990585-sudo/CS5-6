# SafeCapital Dashboard 1.4 — English-first delivery

**English** | [中文](README.zh-CN.md)

<a id="readme-en"></a>

Start with the [English installation and handoff guide](../START_HERE.md). It distinguishes the full **Source ZIP** from the prebuilt **Web ZIP**. No API key is needed for the delivered Dashboard or supplied-data replay. The initial interface is English; Chinese remains an optional language. Explicit URL choices and saved preferences take precedence over the default.

### What the module does

The React/TypeScript frontend and FastAPI backend serve an independent, read-only historical stock research module. It supports standalone access, iframe embedding and namespaced APIs. It does not train models, accept arbitrary uploads, run a new backtest, fetch live prices or execute trades.

- Select multiple stocks by ticker or company name from the 40 external evaluation stocks. Inspect five raw factors, model ranks/scores, component percentiles, strategy selection and actual weights together.
- Share a historical date across watchlist, allocation, rankings and output-aligned inputs; browse the complete input source on an independent date.
- Load/reset a reproducible SCL/TJX/CMG example and export the current selection as CSV or JSON. Watchlist preferences do not change the original portfolio or its returns.
- View original full-backtest account value, weekly return and drawdown; inspect all history, the final 52 weeks or final 156 weeks. Headline metrics always describe the full 210-week backtest.
- Browse 366 model signal dates, ranking pagination/search, verified run versions and provenance. Download original predictions, weekly capital, summary and verification files without rewriting their bytes.
- Switch English/Chinese while preserving active filters. Use `?lang=en` or `?lang=zh` to override a saved preference; embed mode accepts the same parameters.
- Handle loading, no-data and API errors, with request timeouts/retry and an iframe failure fallback. Missing values remain unavailable, not zero.

The portfolio module has an independent `cs5_6_equity` namespace. It preserves the 66-stock training / disjoint 40-stock external research scope, weekly signals, verified actual holdings and declared execution assumptions. A verified market benchmark and currency are unavailable. Raw model ranks are before strategy filtering and are not holdings.

### Local access

After installation, start from the extracted project root:

```bash
.venv-dashboard/bin/python dashboard/start.py
```

For the prebuilt Web package, append `--config config.toml`. On Windows use `.\.venv-dashboard\Scripts\python.exe` instead. Keep the terminal open and stop with Ctrl+C. Append `--port 8001` if port 8000 is occupied.

- [Dashboard](http://127.0.0.1:8000/?lang=en#watchlist)
- [Embedded mode](http://127.0.0.1:8000/?embed=1&lang=en)
- [Example host page](http://127.0.0.1:8000/embed-example.html?lang=en)
- [API documentation](http://127.0.0.1:8000/api/docs)
- [OpenAPI JSON](http://127.0.0.1:8000/api/openapi.json)

Localhost is only accessible on the computer running the service; it is not a public customer URL. The API documentation UI uses an external CDN; the local Dashboard and OpenAPI JSON do not need a live data service.

### First installation from source

Requirements: 64-bit Python 3.12 and Node.js/npm compatible with the pinned frontend dependencies (Node.js 22 or later supported version). Use a fresh extraction and run from the project root. The Dashboard environment is independent of the research environment.

macOS / Linux:

```bash
python3.12 tools/check_release.py
python3.12 -m venv .venv-dashboard
.venv-dashboard/bin/python -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python dashboard/start.py
```

Windows PowerShell:

```powershell
py -3.12 tools/check_release.py
py -3.12 -m venv .venv-dashboard
.\.venv-dashboard\Scripts\python.exe -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.\.venv-dashboard\Scripts\python.exe dashboard/start.py
```

For the prebuilt Web ZIP use its root `verify_delivery.py` / `install.py` instead; it needs no Node.js. Those root scripts are not present in the Source ZIP. Full instructions, configuration and troubleshooting are in [START_HERE](../START_HERE.md).

### Results and updates

Startup scans `runs/` and the tracked `FINAL_OUTPUTS/01_saved_model_replay/verified_replay/`. Only completed `frozen_model_inference` runs with passed verification, matching file hashes, row counts and coverage are accepted. Training runs are not served. Corrupt runs are skipped and counted; if no valid result exists, the service reports unavailable rather than generating data.

A development checkout selects its latest valid replay. A fresh source/Web package uses the included `delivered` result. The local run and delivered replay have equal numerical results but different run timestamps and file identities. Always obtain the actual ID through `/api/cs5_6_equity/v1/runs`.

Verified results and downloads are held in the same in-memory snapshot. Restart after changing disk data; browser refresh does not rescan it. To select a specific complete replay, use `result_dir` in TOML or `SAFECAPITAL_RESULT_DIR`. Invalid explicit configuration fails rather than silently substituting another run. Hash verification establishes file consistency, not a third-party digital signature.

### APIs and integration

New clients use **`/api/cs5_6_equity/v1`**. `/api/v1` and `/api` are compatibility aliases. All business endpoints are read-only GET. Start with `runs`, then query `stocks`, `watchlist`, `inputs`, `portfolio`, `overview`, `equity`, `rankings` or downloads for that run. Human-readable API labels/reasons are English; identifiers, numerical values and original downloads remain stable. The optional Chinese UI translates those display labels locally.

See [API contract](docs/API_V1.md), [watchlist API](docs/PRESENTATION_WATCHLIST.md), [OpenAPI](docs/openapi.json) and [integration handoff](docs/PORTFOLIO_NEO_INTEGRATION.md).

For iframe use, host on a dedicated HTTPS origin, configure exact `embed_origins`, and have the client allow the module in its `frame-src` CSP. The module uses `frame-ancestors`; avoid conflicting proxy X-Frame-Options headers. iframe API requests are same-origin. A different-origin client frontend calling JSON directly needs its exact origin in `api_origins`.

No login/SSO is implemented. An embed/CORS allowlist is not authentication. If required, the client gateway must protect pages, APIs and downloads together. Client hosting, domain, authentication, staging regression and production release are separate responsibilities. Docker and public deployment remain deferred; old Docker recipes are reference material and are not a validated route for the current input/portfolio package.

### Development, packaging and evidence

Run the backend, then `npm --prefix dashboard/frontend run dev` for Vite development; it proxies `/api` to port 8000. Rebuild the frontend before serving changed source through Python.

```bash
.venv-dashboard/bin/python -m pip install -r dashboard/requirements-test.txt
.venv-dashboard/bin/python -m unittest discover -s dashboard/tests -v
node --experimental-strip-types --test dashboard/frontend/tests/*.test.ts
npm --prefix dashboard/frontend run build
```

Web packaging requires a Git checkout, Dashboard dependencies and built frontend; it is not a client installation command. The package contains the root English guide, frontend/server source, prebuilt assets, pinned dependencies, matched inputs, module snapshots, verified results and validation tools. It excludes the complete training environment and refuses to overwrite existing archives. See [build instructions](docs/DELIVERY_BUILD.md).

Further reading: [input/output guide](docs/LOCAL_IO.md), [English presentation script](docs/PRESENTATION_SCRIPT_EN.md), [demo guide](docs/CUSTOMER_DEMO_GUIDE.md), [language policy](docs/LANGUAGE_SUPPORT.md), [1.4 feature validation](docs/PRESENTATION_VALIDATION.md), [development plan](docs/DEVELOPMENT_PLAN.md). Earlier validation documents are dated historical records, not claims that all checks were rerun for every revision.
