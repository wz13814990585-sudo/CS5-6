# Presentation watchlist: workflow and API

Dashboard 1.4 presents existing historical results for followed stocks. The selection is a viewing preference, not a new portfolio calculation. Client-site integration still requires its staging environment and core-team review.

## Start the demonstration

Install using root [START_HERE](../../START_HERE.md). Start the service from the package root and open <http://127.0.0.1:8000/?lang=en#watchlist>. English is the initial default; Chinese is optional. Use screen sharing for a remote local demo. Read the [English presentation script](PRESENTATION_SCRIPT_EN.md) for ready-to-speak wording.

| Step | Action | Explain |
|---|---|---|
| Prepare | Reset demo, then Load demo example | Restores SCL/TJX/CMG at 2026-08-28 and resets searches, pagination and charts |
| Select stocks | Search Chipotle/CMG; add and remove URBN | Ticker/company search, multiple selection, duplicate protection; 40 supported external stocks only |
| Compare results | Inspect the three sample rows | SCL rank 1 selected; TJX rank 2 not selected; CMG rank 3 selected. Ranking differs from actual allocation |
| Connect inputs and outputs | Open TJX View details | Five raw factors, model rank/score/component percentiles, and allocation status; no invented stock-specific rejection reason |
| Change date | Select 2022-08-26; then restore the example | Watchlist, allocation, rankings and output-aligned inputs share the historical date |
| Explain performance | Open Performance | Metrics describe the original full strategy: 10.44% annualised, 49.33% total return over 2022-08-26–2026-08-28 |
| Export | Export current CSV or Export JSON | Current run/date/stocks; complete input downloads remain full original files |
| Integrate | Show API links and the iframe example | Client can embed the module or build its own interface over the same APIs |

## Boundaries and exceptional states

- Search AAPL to show that unsupported stocks do not receive invented results.
- Select 2019-08-30 in Stock rankings. The shared date moves outside allocation coverage. SCL/TJX have ranks but no backtest allocation; CMG has no saved rank. **No allocation data** differs from **Not selected**.
- Five-factor displays show raw values; models apply within-week percentiles. Research target1/target2 labels are not exposed as input-query fields and do not enter predictions.
- Weights describe simulated rebalancing at next-week open proxies. Positions were liquidated after the last holding period; these are not current holdings. Prices are historical execution proxies, not forecasts. Currency is unspecified.
- Full source file mode allows independent dates from 2015 onward; output-aligned inputs use the shared research date.
- Watchlists are stored in the current browser, not a server account. Refresh keeps the selected stocks but restores the run's latest backtest date. Cross-site iframe storage depends on browser policy; there is no cross-device/account synchronisation promise.
- API requests time out after 12 seconds and allow retry. New queries cancel stale requests so old results cannot overwrite a new selection. Export links appear only for the current loaded response.
- The local iframe host waits for module readiness; after 12 seconds without it, retry and a standalone link appear. A module failure must not disable the host page.
- Custom portfolio backtests, uploads, live data, trades, rank-history charts and print reports are not part of this version.

## Read-only watchlist API

Base: `/api/cs5_6_equity/v1/`. First GET `runs` and read `default_run_id`.

| Request | Purpose |
|---|---|
| `GET runs/{id}/stocks` | Supported tickers/companies, backtest dates, ranking dates and default date |
| `GET runs/{id}/watchlist?date=2026-08-28&tickers=SCL,TJX,CMG` | Join selected inputs, ranking, allocation and provenance |
| `GET runs/{id}/watchlist/download?date=2026-08-28&tickers=SCL,TJX,CMG&format=csv` | Current-selection CSV; use format=json for the complete JSON response |

Date and tickers are required. Comma-separated tickers are trimmed, uppercased, deduplicated and retained in selection order. Maximum selection is the run's supported universe (currently 40). One unsupported stock rejects the entire request with HTTP 422 `unsupported_stocks`; it is not silently discarded. Invalid date/format returns 422, unknown run returns 404 and writes are not supported.

The stock catalog covers the run, not necessarily every date. Company names prefer the selected date's input; otherwise the latest available source name is a catalog label.

| Response field | Meaning |
|---|---|
| module_id/module_version/run_id/signal_date/requested_tickers | Identity, date and requested order |
| status | success: all selected ranks/factors/prices/allocation judgments available; partial: some missing; no_data: none of the selected stocks has a rank on that date |
| watchlist_changes_strategy | Always false |
| rows | ticker, stock_name, factors_status/factors, prices_status/prices, ranking, selection_status, allocation, exclusion_reason |
| factors_status / prices_status | available; no_data for missing aligned records; unavailable for absent or mismatched source identity |
| selection_status | selected; not_selected when rank and verified allocation exist but the stock is absent; no_data without relevant allocation/rank; unavailable when identity/snapshot cannot be verified |
| allocation | Original real target/actual weights, shares and related fields only for selected stocks; otherwise null |
| exclusion_reason | null: original files do not record per-stock rejection reasons |
| strategy_context.metrics_scope | original_strategy_full_backtest; metrics/backtest/units/assumptions do not change with the watchlist |
| provenance | Original output, matched input and allocation snapshot hashes; missing items are null |

Always inspect field status/null even when the top-level response is successful. Missing is not zero. The complete model/universe contract remains on `portfolio`.

CSV uses UTF-8 BOM for spreadsheet compatibility. Percentiles/weights are fractions: 0.2 means 20%. Nulls become empty cells. CSV contains selected date/run/stocks, factors, historical prices, model outputs, selection/weight/share fields and hashes; it does not invent a watchlist return. JSON includes clearly scoped original portfolio metrics.

```bash
node dashboard/examples/verify-watchlist.mjs http://127.0.0.1:8000/
```

Reproducible responses are in `dashboard/examples/cs5_6_equity/watchlist-success.json`, `watchlist-no-data.json` and `watchlist-invalid.json`. [OpenAPI](openapi.json) is the machine-readable schema.

## Client integration

1. iframe: link the Strategy Lab entry to `https://research.example.com/?embed=1&lang=en#watchlist`, replacing the example origin. Set `embed_origins` and the client's `frame-src` policy. The local host example is in `dashboard/frontend/public/embed-example.html` and `.mjs`.
2. Client-native UI: populate a selector from stocks, then request watchlist with date/tickers. Configure `api_origins` for cross-origin browser calls, or proxy through the client's backend.
3. Readiness: `{type:"cs5_6_equity:ready",version:"1.4.0"}` means the frontend mounted, not that every dataset is healthy. Validate both `event.origin` and `event.source`. The example validates same-origin; real cross-origin integration needs the exact agreed origin.
4. Production: obtain hosting/authentication/staging details, implement a focused client feature branch/PR and regression-test the other Portfolio functions. The local demonstration is not a production deployment.

Feature evidence: [PRESENTATION_VALIDATION](PRESENTATION_VALIDATION.md).
