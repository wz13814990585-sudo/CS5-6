# SafeCapital — client delivery and installation guide

**Team:** CS5-6 · **Dashboard version:** 1.4.0 · **Delivery revision:** 2026-11-03

This delivery provides **Model-Based Stock Strategies**, an independent research module for Portfolio Neo / Strategy Lab. It includes a bilingual Dashboard, read-only input/output APIs, and verified historical results. The Dashboard runs locally or inside an iframe. Integration into the client's live website is a separate step requiring the client's hosting and authentication arrangements.

**API keys: none are required to run the delivered Dashboard or replay the supplied frozen research results.** Installation downloads dependencies. The Dashboard uses the supplied local data; it does not call a live market-data or AI service.

## 1. Choose your package

| Package | Contents | Requirements to start the Dashboard |
|---|---|---|
| `SafeCapital-Source-1.4.0-20261103.zip` | Complete tracked project: research code, supplied datasets, saved models, reports, Dashboard source, and documentation | 64-bit Python 3.12, Node.js 22 or later supported by the frontend dependencies, and npm; build the frontend once |
| `SafeCapital-Web-1.4.0-20261103.zip` | Dashboard source **and prebuilt frontend**, matching inputs, verified results, module snapshots, installation tools, and documentation | 64-bit Python 3.12; no Node.js, model libraries, or model training required |

Use the **Web package** for the quickest evaluation. Use the **Source package** for complete code review and research reproduction. The Web package does not contain the full model-training project and does not replace the source delivery.

Extract the ZIP into a new directory. Open a terminal in the extracted top-level folder containing this file. Do not run commands from inside a ZIP viewer. Source ZIPs do not include `.git`, virtual environments, `node_modules`, or prebuilt frontend files. Do not copy an environment from another computer.

**Identify the package:** the Web package has `install.py`, `verify_delivery.py`, `config.toml`, and `DELIVERY_MANIFEST.json` at its root. The Source package has `safecapital.py`, `tools/check_release.py`, and `RELEASE_MANIFEST.json` instead. Follow only the matching instructions below.

## 2. Web package: install and run

### macOS / Linux

```bash
python3.12 --version
python3.12 verify_delivery.py
python3.12 install.py
.venv-dashboard/bin/python dashboard/start.py --config config.toml
```

### Windows PowerShell

```powershell
py -3.12 --version
py -3.12 verify_delivery.py
py -3.12 install.py
.\.venv-dashboard\Scripts\python.exe dashboard/start.py --config config.toml
```

The installer verifies package files, creates a new `.venv-dashboard`, and installs the pinned dependencies from `dashboard/requirements.txt`. It refuses to overwrite an existing environment. If installation was interrupted, extract a fresh copy and retry. Do not run the installer in the full source project.

Keep the terminal open while using the Dashboard. On subsequent starts, run only the last command. Press **Ctrl+C** to stop. If port 8000 is occupied, append `--port 8001` to the start command and use port 8001 in the browser and checks.

## 3. Source package: install and run the Dashboard

Use this section for the full source ZIP or a GitHub checkout. The root-level `install.py` from section 2 is deliberately absent here. This procedure does not install research/model dependencies and does not retrain or replay the models.

### macOS / Linux

```bash
python3.12 --version
node --version
npm --version
python3.12 tools/check_release.py
python3.12 -m venv .venv-dashboard
.venv-dashboard/bin/python -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python dashboard/start.py
```

### Windows PowerShell

```powershell
py -3.12 --version
node --version
npm --version
py -3.12 tools/check_release.py
py -3.12 -m venv .venv-dashboard
.\.venv-dashboard\Scripts\python.exe -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.\.venv-dashboard\Scripts\python.exe dashboard/start.py
```

Run these commands in a fresh extraction. After the first successful setup, only the final start command is needed. Frontend source changes require another `npm --prefix dashboard/frontend run build`.

To reproduce the research calculation, use the **separate research environment and instructions in the root `README.md`**. The research `requirements.txt` is different from `dashboard/requirements.txt`. The complete frozen replay is `python safecapital.py` in that research environment; it is optional for viewing the supplied Dashboard results. Raw data acquisition is outside the delivered reproduction procedure.

## 4. Open and verify

| Page | Local address |
|---|---|
| English Dashboard | <http://127.0.0.1:8000/?lang=en#watchlist> |
| Chinese Dashboard | <http://127.0.0.1:8000/?lang=zh#watchlist> |
| iframe entry demonstration | <http://127.0.0.1:8000/embed-example.html?lang=en> |
| Interactive API documentation | <http://127.0.0.1:8000/api/docs> |
| OpenAPI JSON, without the documentation UI | <http://127.0.0.1:8000/api/openapi.json> |
| Module health | <http://127.0.0.1:8000/api/cs5_6_equity/v1/health> |

`127.0.0.1` means the computer running the server. It is not a public link for another person. Use screen sharing for a remote local demonstration. Opening `index.html` directly does not start the API server.

In **Watchlist**, click **Reset demo**, then **Load demo example**. At the historical date **2026-08-28**, SCL ranks 1 and is selected, TJX ranks 2 and is not selected, and CMG ranks 3 and is selected. Inspect factors and actual allocations, switch historical dates, and download the current CSV or JSON selection. Selecting stocks changes the view, not the strategy or its return.

The original full strategy covers 210 signal weeks from 2022-08-26 to 2026-08-28: initial capital 100000, final capital approximately 149330.61, total return 49.33%, annualised return 10.44%, and maximum drawdown −24.88%. These are saved historical simulation results, not live holdings or a forecast. The benchmark and currency are not independently established in the supplied results and are marked unavailable.

With the server running, open another terminal in the same package root and run the appropriate acceptance check:

**Web package:**

```bash
python3.12 smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

**Fresh Source package:**

```bash
python3.12 dashboard/tools/smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

On Windows, replace `python3.12` with `py -3.12`. These checks use only the Python standard library. They verify the page assets, real inputs, holdings, watchlist, original metrics, errors, and downloaded result bytes. Expect `"status": "passed"` and `"run_id": "delivered"` on an unmodified fresh package. If using a development checkout with other runs, omit `--expected-dir` or point it to the selected run's actual directory.

An optional detailed API example, if Node.js is installed, is:

```bash
node dashboard/examples/verify-watchlist.mjs http://127.0.0.1:8000/
```

## 5. API keys, configuration, and connectivity

| Item | Requirement |
|---|---|
| Dashboard / supplied-data replay | No API key, cloud account, or live data feed |
| Dependency installation | Internet access to Python/npm package registries |
| Dashboard after installation | Local historical browsing and APIs work without a live data service |
| Interactive `/api/docs` | Its Swagger UI assets use an external CDN; use `/api/openapi.json` or the packaged `dashboard/docs/openapi.json` if unavailable |
| Optional upstream SEC collection scripts | Require the user's own `SEC_USER_AGENT` contact identifier and internet access; this is not an API key and is not needed for the delivered Dashboard/replay |
| Application login / SSO | Not implemented; the current API has no API-key authentication |

Do not include actual keys, tokens, passwords, personal `.env` files, or credentials in a submission. Sample domains and contact identifiers are placeholders, not credentials.

For the **Web package**, edit root `config.toml` after verification and installation. For the **Source package**, copy `dashboard/config.example.toml` to `dashboard/config.toml` and start with `--config dashboard/config.toml`. Without a config file, source startup uses the local defaults.

```toml
host = "127.0.0.1"
port = 8000
public_url = ""
result_dir = ""
embed_origins = ""
api_origins = ""
```

`public_url` is the eventual dedicated HTTPS origin; leave it blank locally. `result_dir` selects a complete verified replay; leave it blank to use the supplied result. Relative result paths are anchored to the config file. `embed_origins` controls which sites may embed the module; `api_origins` independently controls cross-origin browser API reads. Both accept exact comma-separated origins, including scheme and optional port, without paths, trailing slashes, or wildcards.

Configuration precedence is defaults → TOML → `SAFECAPITAL_*` environment variables → CLI host/port. A user-edited config no longer matches the original package checksum; verify the untouched package first, then keep a record of intentional edits. Restart the service to load new data/configuration; browser refresh alone does not reload disk results.

## 6. Connect to Portfolio Neo / Strategy Lab

The client can add a **Model-Based Stock Strategies** card or tab alongside existing Strategy Lab options. Keep this module's multi-stock universe separate from the host website's single-asset selector. Its research engine, data, identifiers, and ontology remain isolated under `cs5_6_equity`.

### Option A: iframe

Host this service on a dedicated HTTPS origin and embed:

```html
<iframe
  src="https://research.example.com/?embed=1&lang=en"
  title="Model-Based Stock Strategies"
  width="100%"
  height="1400"
  style="border:0;border-radius:16px"
  loading="lazy">
</iframe>
```

Replace the example domain. Configure this service's `public_url` and `embed_origins` for the actual origins. The client's CSP must allow the Dashboard in `frame-src`; this module supplies its `frame-ancestors` policy. Avoid conflicting proxy `X-Frame-Options` headers. iframe-contained API calls are same-origin and do not require API CORS. The local entry demonstration includes loading, readiness, retry, and standalone fallback behavior.

### Option B: client-built interface using the API

Use the read-only namespace **`/api/cs5_6_equity/v1`**. First request `/runs`, read `default_run_id`, then request data for that ID. Do not hardcode a developer's local run ID. For example:

```text
GET /api/cs5_6_equity/v1/runs
GET /api/cs5_6_equity/v1/runs/{run_id}/stocks
GET /api/cs5_6_equity/v1/runs/{run_id}/inputs
GET /api/cs5_6_equity/v1/runs/{run_id}/watchlist?date=2026-08-28&tickers=SCL,TJX,CMG
GET /api/cs5_6_equity/v1/runs/{run_id}/portfolio?date=2026-08-28
GET /api/cs5_6_equity/v1/runs/{run_id}/overview
GET /api/cs5_6_equity/v1/runs/{run_id}/equity
```

Configure `api_origins` when a different-origin browser frontend calls these APIs. Schema and examples are provided in [OpenAPI](dashboard/docs/openapi.json), the [API guide](dashboard/docs/API_V1.md), and [JavaScript client](dashboard/examples/client.mjs). `null` is unavailable, not zero; returns and weights are fractions. Read the status of each result and field. Raw model rankings are before strategy filtering and do not equal selected holdings.

Allowlisting an origin is **not authentication**. If the client requires login, its gateway or a future authentication layer must protect the page, API, and downloads together. Agree on hosting, origins, access control, ownership, and staging acceptance before production rollout. Docker and public deployment are not prerequisites for this delivery and are not its validated installation path. Legacy Docker examples remain reference material only.

## 7. Scope and evidence

The research scope is 66 training stocks and 40 separate external evaluation stocks, with no ETFs. The supplied strategy uses weekly signals, three frozen components, up to five positions, a 13-week historical-return filter, integer shares, and 10 basis points per side. Execution uses historical next-week open/close proxies; the final holding period is liquidated. The Dashboard does not guarantee point-in-time financial publication data, real next-open execution, or S&P 500 historical membership.

This release does not provide arbitrary stock universes, data uploads, online inference/training, personalised portfolio recomputation, live prices, actual trading, or customer SSO. The watchlist is a local browser preference and is not stored as a server-side account. A missing per-stock exclusion reason is not inferred.

The companion final validation report records the actual platform and commands used for the two ZIPs. Earlier feature evidence is in [Dashboard 1.4 validation](dashboard/docs/PRESENTATION_VALIDATION.md). The local entry page is a simulation of integration, not evidence of deployment on the client's site. Windows/Linux commands are provided, but platform coverage must be read from the validation report; no untested platform or client production deployment is claimed.

## 8. Troubleshooting

| Symptom | Action |
|---|---|
| `python3.12` / `py -3.12` not found | Install 64-bit Python 3.12 and reopen the terminal. Do not substitute an unverified Python version. |
| `install.py` not found | You probably have the Source package: follow section 3. |
| `Frontend build missing` | In the Source package run `npm ci` and `npm run build` with the prefixes shown above. If using the Web package, verify/re-extract the untouched ZIP. |
| Dependency download failure | Check internet/proxy access; retain the pinned requirements and retry in a new extraction. |
| Address already in use | Start with `--port 8001` and change every browser/check URL to that port. |
| Page opens but no verified result | Check the full extraction, original manifest, and any `result_dir` override; do not substitute fabricated data. |
| API docs are blank | Open `/api/openapi.json`; CDN availability does not control the Dashboard's local API. |
| Another person cannot open localhost | Run their own copy, use screen sharing, or arrange an authorised hosted endpoint. |
| iframe is blocked | Check both sites' CSP, exact allowed origins, and proxy headers. |
| File verification fails after editing | Compare against a fresh extraction and distinguish intended config changes from corruption. |

## 9. Submission checklist and supporting files

Provide the complete source ZIP, the optional prebuilt Web ZIP, this guide, the companion validation/checksum files, and the team's separately recorded video. Identify the final Git commit when submitting. Source ZIPs are exported from that commit; Git history remains in the repository. ZIP integrity hashes are not digital signatures.

- [English submission message template](dashboard/docs/CLIENT_SUBMISSION_EN.md)
- [Bilingual ready-to-read presentation script](dashboard/docs/PRESENTATION_SCRIPT_ZH_EN.md)
- [Chinese installation guide](dashboard/docs/CUSTOMER_HANDOFF.md)
- [Feature and interface walkthrough](dashboard/docs/PRESENTATION_WATCHLIST.md)
- [Integration scope and research provenance](dashboard/docs/PORTFOLIO_NEO_INTEGRATION.md)

Repository: <https://github.com/wz13814990585-sudo/CS5-6>
