# CS5-6 / Portfolio Neo integration handoff

**Model-Based Stock Strategies** is an independent module under `cs5_6_equity`. It displays existing inputs, model rankings, actual stock allocations and historical performance, with standalone, iframe and read-only API access. Visual styling follows the client's dark green Strategy Lab reference. English is the default interface and documentation; Chinese is optional in the UI.

This is a locally demonstrable module, not a completed integration into the client's live site. Client source, authentication and staging access are needed to verify actual placement, permissions and other modules. Docker/public deployment remain deferred.

## Demonstrate locally

Install from [START_HERE](../../START_HERE.md), then open `http://127.0.0.1:8000/?lang=en#watchlist`. The host example is `/embed-example.html?lang=en`; click Explore strategies. The API explorer is `/api/docs`, with offline `/api/openapi.json`. Use the [English presentation script](PRESENTATION_SCRIPT_EN.md).

Show the watchlist, inputs and rankings, followed by actual stocks/weights and the full historical performance. The Common210 FullHistory simulation spans 2022-08-26–2026-08-28 (210 signal weeks): annualised return 10.44%, total return 49.33%, maximum drawdown −24.88%, capital 100000 to 149330.61. Chart window changes do not change full-run headline metrics. Target and actual weights differ because of integer shares/cash. Latest saved holdings are SCL, CMG, UTZ, RH and URBN; raw ranks 1/3/4/6/7 are not simply the first five ranks. Final positions were liquidated; this is not a live holdings page.

## Client requirements and acceptance boundaries

| Requirement | Implementation | Remaining boundary |
|---|---|---|
| Separate Portfolio Neo entry | Proposed Strategy Lab card + isolated iframe | Exact client-page placement needs core-team integration |
| Model/strategy/stocks/weights | Weekly selection, target/actual weights and cash | Historical simulation, not live trading |
| Performance, drawdown and benchmark | Verified 210-week series; benchmark marked unavailable | No matched verified benchmark supplied |
| 66 training and 40 disjoint external stocks; no ETFs | Actual lists/counts and signal-date availability | 66 is the full training universe; early snapshots have changing coverage |
| FullHistory separate from final-test | Explicit Common210 scope/dates/weeks | Do not substitute the report's shorter-window metrics |
| Annualisation, costs, execution and currency | 52-week compounding, 10 bps per side, integer shares, historical next-week proxies and final liquidation | Currency=null; no asserted real next-open fills or historical S&P 500 membership |
| Separate ontology/engine | Namespaced API, data directory and entities | Do not overwrite global routing, login, asset selector or other teams |
| Failure isolation | Missing/bad allocation snapshot disables that view; verified outputs remain | Client-wide failure regression still needs staging |
| Provenance and honest missing values | File hashes, independent accounting, null plus reason | Signal date is not a verified financial publication timestamp |
| Success/no-data/error examples | verify-module.mjs and JSON samples | Reproducible locally |
| Responsive bilingual module | Desktop/mobile feature validation and language switch | Client host/device acceptance remains |
| Feature branch and focused PR | Module developed on isolated project branches | Client core team controls its own merge and production release |

Earlier version-specific checks are preserved in [1.3 validation](PORTFOLIO_NEO_VALIDATION.md) and [1.4 validation](PRESENTATION_VALIDATION.md). Merging this team's repository does not imply merging or deploying the client's site.

## API and data contract

New clients use `/api/cs5_6_equity/v1`; `/api/v1` and `/api` are compatibility aliases. Read-only GET endpoints do not upload files, train or predict. Human-readable labels/reasons are English. Discover the run ID before querying it.

| Relative path | Purpose |
|---|---|
| `runs` | Available run IDs and default_run_id |
| `runs/{id}/portfolio?date=2026-08-28` | Complete module contract; omitted date selects the latest backtest signal |
| `runs/{id}/overview` | Full metrics, source and ranking dates |
| `runs/{id}/equity` | 210 weekly capital/net-return/drawdown observations |
| `runs/{id}/rankings?date=2026-08-28&q=ANF&page_size=10` | Model ranking before strategy filtering |
| `runs/{id}/inputs` | Run-bound inputs and field metadata |
| `runs/{id}/inputs/{dataset}/rows?date=2026-08-28&scope=output&q=SCL` | factors or prices; join by date + exact ticker |
| `runs/{id}/inputs/{dataset}/download` | Complete original input CSV |
| `runs/{id}/downloads/{kind}` | Original predictions/equity/summary/manifest and verification files |

Watchlist extensions are documented in [PRESENTATION_WATCHLIST](PRESENTATION_WATCHLIST.md).

| Portfolio field | Meaning |
|---|---|
| module_id, module_version, run_id, data_mode | Identity and historical_simulation scope |
| status | success, partial, no_data; inspect per-field availability as well |
| model, strategy | Frozen three components / 45 snapshots, Top5_NoLoss13w, weekly, at most five positions, 0.2 target per stock |
| universe | Full training and external stock lists, counts and signal-date availability |
| signal_date, data_cutoff | Dataset signal/latest-source dates; financial_publication_timestamp=null |
| backtest | start/end/weeks/scope/window, separate from the chosen allocation date |
| metrics, units | Fractional returns/drawdowns/weights; original capital units, currency=null |
| benchmark | unavailable; name/return/series null with reason, not a zero-return benchmark |
| assumptions | Annualisation, 52 weeks, fees, proxy prices, integer shares, 13-week filter, final liquidation |
| allocation | status/reason, phase, rows, cash/cash_weight, value and liquidation marker |
| allocation.rows | ticker/company, model_rank, target_weight, actual_weight, shares, execution_price_proxy, market_value_at_open |
| provenance | Result, manifest, engine and allocation hashes plus offline verification evidence |

`actual_weight = shares × next_week_open_proxy / post_trade_open_value`, where post-trade value is stock value at open proxies plus cash after rebalancing. Cash weight plus stock weights equals 1. This is post-trade allocation, not end-of-week valuation. The last week carries `liquidated_at_period_end=true`.

Top-level success does not establish benchmark/currency availability. A legal date without a backtest returns HTTP 200/no_data, empty rows and cash_weight=null, not an all-cash portfolio. Only a verified all-cash week may have available allocation, empty rows and cash_weight=1. Invalid dates return 422, unknown runs 404; namespaced errors include status/module_id and error code/message/request_id/fields.

```bash
node dashboard/examples/verify-module.mjs http://127.0.0.1:8000/
node dashboard/examples/client.mjs http://127.0.0.1:8000/
```

The examples cover success, 2019-08-30 without allocation, invalid dates and missing runs. JSON samples are actual adapter outputs, not simulated replacements for research results. Always query runs even if examples show `delivered`.

## Research engine and provenance

Module entities are **Module → Model → Run → WeeklySignal → EquityAllocation → BacktestMetrics**. IDs combine module_id, run_id, signal_date and ticker. These are this module's JSON relationships, not a replacement for a shared RDF/ontology. Original research engine, filenames and run identities remain intact.

Allocation exports live in `dashboard/data/cs5_6_equity/`. The offline exporter uses the original integer-share engine and independent verifier on saved predictions; it does not train or produce new predictions. Two saved CSV serialisations have matching snapshots, each covering 210 weeks: maximum original account-series difference 0; 9586 independent accounting checks per snapshot, maximum numerical difference approximately 2.84e-14.

Maintainer-only export in the full research environment:

```bash
.venv/bin/python dashboard/tools/export_portfolio_snapshot.py
```

Runtime reads the snapshot after validating its hash, size, scope and weights, then binds it through three result hashes and four input/config hashes. If a new run has no matching snapshot, allocation is unavailable while valid original outputs remain queryable. Regenerate and verify offline before restart; do not edit metrics/hashes to bypass validation.

## Client implementation steps

1. Agree the client repository, staging URL, module origin, authentication requirements and owners.
2. Run the native service on a dedicated HTTPS origin. Configure public_url and exact embed_origins; api_origins is independently required only for cross-origin browser JSON requests.
3. Add a Strategy Lab card/tab in the client's feature branch. Keep global assets, login, routing and other modules intact. The core team chooses exact placement.
4. Embed `https://research.example.com/?embed=1&lang=en`, replacing the module origin, with a labelled iframe and suitable height/scroll behavior. Both sites must permit the embedding in CSP.
5. A client-native interface may consume JSON instead. Do not import module CSS globally or merge ontologies. Preserve missing-value and provenance semantics.
6. If login is required, protect page, API and downloads at the gateway. Origin allowlists are not authentication.
7. In staging, check mobile layouts, language, loading/no-data/error states and host navigation/login/other strategies while the module is unavailable. The host asset selector must not change this module's 40-stock universe.
8. The core team reviews a focused PR and controls merge/release. This handoff does not modify the client website automatically.

Runtime is Python 3.12 with locked Dashboard dependencies; prebuilt Web use needs neither Node.js nor model libraries. Frontend source uses React 19, TypeScript, Vite and Recharts with package-lock.json. Portfolio implementation is in `dashboard/server/portfolio.py`, `schemas.py`, `PortfolioPanel.tsx` and `client-theme.css`. The Web package includes snapshots, inputs, original results, offline OpenAPI and documentation, not the entire training project. Legacy Docker recipes are not the current validated startup route.
