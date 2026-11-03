# Client handoff — installation and integration

Dashboard 1.4.0, English-first delivery revision 2026-11-03. The complete English guide is [START_HERE.md](../../START_HERE.md) at the root of either package. This file is an English quick reference for existing documentation links.

## Select the correct installation path

| Package | Purpose | Requirements |
|---|---|---|
| Source ZIP | Complete code, datasets, models, reports and Dashboard source | Python 3.12 plus Node.js/npm to build the Dashboard frontend |
| Web ZIP | Dashboard source, prebuilt frontend, matching inputs and verified results | Python 3.12 only |

The Web package has root `install.py`, `verify_delivery.py`, `config.toml` and `DELIVERY_MANIFEST.json`. The Source package does not. Extract into a fresh directory and open a terminal in its root. Do not copy a virtual environment from another computer.

## Web package

macOS / Linux:

```bash
python3.12 verify_delivery.py
python3.12 install.py
.venv-dashboard/bin/python dashboard/start.py --config config.toml
```

Windows PowerShell:

```powershell
py -3.12 verify_delivery.py
py -3.12 install.py
.\.venv-dashboard\Scripts\python.exe dashboard/start.py --config config.toml
```

The installer verifies files, creates a new environment and downloads pinned dependencies. It refuses to overwrite an existing environment. After setup, run only the start command. Keep the terminal open; Ctrl+C stops it. If the port is occupied, append `--port 8001` and update all URLs.

## Source package

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

Research reproduction has a separate root `requirements.txt` and workflow in the root README. It is not needed to view the supplied Dashboard results.

## Demonstrate and verify

Open <http://127.0.0.1:8000/?lang=en#watchlist>. English is the initial default; an explicit URL or saved language choice overrides it. Click **Reset demo**, then **Load demo example**. On 2026-08-28, SCL ranks 1 and is selected, TJX ranks 2 and is not selected, and CMG ranks 3 and is selected. Changing the watchlist does not recalculate portfolio returns. The [English speaking script](PRESENTATION_SCRIPT_EN.md) provides each action and explanation.

The example host is <http://127.0.0.1:8000/embed-example.html?lang=en>. API documentation is at `/api/docs`; `/api/openapi.json` and the packaged OpenAPI work without the Swagger UI CDN. Localhost is not a public customer URL.

With the server running, open another terminal and run the Web acceptance command:

```bash
python3.12 smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

For source, replace `smoke_check.py` with `dashboard/tools/smoke_check.py`. On Windows use `py -3.12`. A fresh package should report `status: passed` and `run_id: delivered`. A development checkout with additional runs needs the actual selected result directory, or omit `--expected-dir`.

## Keys and configuration

No API key or credentials are required for the delivered Dashboard or supplied-data replay. Installation needs internet access; installed local data browsing does not require a live feed. Optional upstream SEC collection needs the user's own `SEC_USER_AGENT` contact identifier, not an API key, and is outside the required workflow. Do not submit real credentials or personal `.env` files.

Edit root `config.toml` in Web, or copy `dashboard/config.example.toml` to `dashboard/config.toml` in Source and start with `--config dashboard/config.toml`. Verify the untouched package before editing configuration.

- `host` / `port`: local defaults 127.0.0.1 / 8000.
- `public_url`: eventual dedicated HTTPS origin; blank for local use.
- `result_dir`: complete verified replay; blank selects supplied/discovered results.
- `embed_origins`: exact origins allowed to embed the module.
- `api_origins`: exact origins allowed to make browser API calls.

Origins include scheme, host and optional port, with no path, wildcard or trailing slash. Separate multiple origins with commas. Precedence is defaults < TOML < `SAFECAPITAL_*` environment variables < CLI host/port. Relative result paths resolve against the config file. Restart after changing disk results or config.

## Client integration and limits

Use iframe or the read-only `/api/cs5_6_equity/v1` APIs. Obtain `default_run_id` from `/runs`; do not hardcode a developer's run ID. See [API contract](API_V1.md), [OpenAPI](openapi.json) and [integration handoff](PORTFOLIO_NEO_INTEGRATION.md).

Keep this module's stock universe, identifiers, ontology and engine independent of the client's global asset selector and other teams. iframe use requires compatible CSP on both sides. Browser API calls from another origin require `api_origins`. Allowlisting is not login protection: a gateway or later authentication layer must protect page, APIs and downloads together if access should be restricted.

Live data, uploads, online training/inference, personalised portfolio recomputation, trading and SSO are not implemented. Docker/public deployment are deferred; retained Docker examples are not the validated installation route. Client hosting, exact domains, authentication and staging regression require the client's core team.

Deliver both ZIPs, the English guide, accompanying validation/checksum files and the separately recorded video. The [English message template](CLIENT_SUBMISSION_EN.md) is a draft, not a sent message. Archive hashes establish integrity, not digital signatures. Install upgrades into a new directory, verify them, and retain the previous package for rollback.
