# SafeCapital API v1 contract

Local base URL: `http://127.0.0.1:8000/api/cs5_6_equity/v1/`. Business APIs provide read-only GET queries/downloads. The major contract version is v1; clients should ignore added optional fields. Removing a field or changing its meaning requires a new major version. `/api/v1` and `/api` remain compatibility aliases, not the preferred integration namespace.

Machine-readable schema: [openapi.json](openapi.json), also served at `/api/openapi.json`. `/api/docs` uses externally hosted Swagger UI assets; offline consumers can use the JSON directly. Human-readable API labels, descriptions and errors are English. UI language does not change identifiers, numeric fields or original downloads. No API key is required; built-in login/SSO is not implemented.

See [portfolio contract](PORTFOLIO_NEO_INTEGRATION.md) and [watchlist contract](PRESENTATION_WATCHLIST.md#read-only-watchlist-api) for detailed module fields and status semantics.

## Request sequence

1. GET `runs` and read `default_run_id`; never hardcode a developer's local folder name.
2. GET `runs/{id}/inputs`, then query `inputs/factors/rows` or `inputs/prices/rows`.
3. GET `runs/{id}/overview` for metrics, coverage and available ranking dates.
4. GET `runs/{id}/equity` for the complete weekly account series.
5. GET `runs/{id}/rankings?date=2026-08-28&q=ANF&page=1&page_size=10`.
6. GET `runs/{id}/downloads/summary` for the original result file.

Executable example: `node dashboard/examples/client.mjs http://127.0.0.1:8000/`.

| Endpoint | Main response fields / behavior |
|---|---|
| `health` | status, verified_runs, rejected_runs; 503 if no valid results |
| `config` | app_version, api_version, public_url, data_mode |
| `runs` | runs, default_run_id (null if none), rejected_runs |
| `runs/{id}/stocks` | stocks, backtest_dates, ranking_dates, default_date |
| `runs/{id}/watchlist?date=2026-08-28&tickers=SCL,TJX,CMG` | rows, selection_status, strategy_context, provenance; existing results only |
| `runs/{id}/watchlist/download?...&format=csv` | Current selection CSV; `format=json` returns the JSON contract |
| `runs/{id}/inputs` | available, reason, run_id, datasets, model |
| `runs/{id}/inputs/{dataset}/rows` | dataset, scope, date, total, page, page_size, rows |
| `runs/{id}/inputs/{dataset}/download` | Complete original input CSV bytes |
| `runs/{id}/portfolio` | Module/model/strategy, universe, backtest metrics, allocations, assumptions and provenance |
| `runs/{id}/overview` | run, summary, dates, prediction_first_date, prediction_last_date, ticker_count, ranking_notice |
| `runs/{id}/equity` | rows: date, start_capital, end_capital, net_return, cash, fees, drawdown and original account fields |
| `runs/{id}/rankings` | date, total, page, page_size, rows |
| `runs/{id}/downloads/{kind}` | Original bytes; Content-Disposition supplies the filename |

Ranking rows include ticker, date, ensemble_predicted_rank, ensemble_ranking_score, model_1/2/3_percentile, and original component scores/IDs. Pages start at 1; page_size is 1–100. `q` is a case-insensitive ticker substring, at most 30 characters. A page beyond the last page has empty rows but retains the full matched total. A nonexistent signal date returns 404; arbitrary calendar dates are not substituted.

Download kinds: `predictions`, `equity`, `summary`, `manifest`, `prediction-verification`, `backtest-verification`. Original CSV bytes and numerical formatting are preserved.

## Input queries

`dataset` is `factors` or `prices`. Omit `date` for all dates in the chosen scope. Default `scope=output` returns records aligned to that run's output date/ticker keys; `scope=source` returns complete source coverage. Sort order is date descending, ticker ascending. Pagination and ticker search follow ranking conventions. An input query with a valid date but no matching data returns 200 with empty rows and total=0; rankings return 404 for a date without predictions.

- Factors: date, ticker, stock_name and the five raw fields revenue_growth_yoy, operating_profitability, cashflow_to_assets, debt_to_assets, asset_growth_yoy. The model further applies within-week percentile transforms.
- Prices: date, ticker, stock_name, buy_price, sell_price. Prices are historical next-week open/close execution proxies.
- Join by date + ticker, not row order. Ranking precedes strategy filtering and does not imply a trade. Earlier prices can support the 13-week historical filter.
- Dataset metadata distinguishes source_rows/source_dates from output_aligned_rows/output_dates and supplies columns, source_columns, omitted_columns, sha256 and bytes.
- Input downloads always contain the full original file, ignoring current query filters/pagination. Research columns such as target1/target2 remain in that file but are not returned as model input fields or used for prediction.
- Startup checks input/config/model identities against the replay. Missing/mismatched data yields catalog available=false; rows/downloads return 503 inputs_unavailable. Verified outputs remain available. Restart after changing files.

Example: `runs/{id}/inputs/factors/rows?scope=output&date=2026-08-28&q=ANF&page=1&page_size=10`.

## Semantics

Returns, drawdowns and weights are decimal fractions: 0.10 means 10%. The ensemble score is the average of three within-week component percentiles, not an expected return or probability. Rank 1 is the highest weekly model rank. Rankings are not actual holdings, trading instructions or a live market state.

`date` is a signal date; `end_capital` is capital at the end of the corresponding holding period. `finished_utc` is the run completion timestamp, not data coverage. Client display can convert timestamps to local time. Capital retains the research accounting units; no currency is inferred. Summary metrics always describe the full backtest; clipping the chart does not reset drawdown's historical peak. APIs, charts and downloads use one verified in-memory snapshot per running server.

## Errors

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Request parameters do not match the API contract.",
    "request_id": "server-generated-id",
    "fields": ["query.date"]
  },
  "detail": "Request parameters do not match the API contract."
}
```

Namespaced errors also carry module status/identity where defined by the response schema.

| HTTP | code | Client action |
|---|---|---|
| 404 | not_found | Select an available run/date or correct the download kind |
| 405 | method_not_allowed | Use GET |
| 422 | unsupported_stocks | Select supported stocks; do not submit an empty/unsupported watchlist |
| 422 | invalid_request | Correct parameters indicated by fields |
| 503 | no_verified_results | Show unavailable and contact the maintainer |
| 503 | inputs_unavailable | Inspect catalog.reason; verified outputs may still be usable |
| 500 | internal_error | Retain request_id for the maintainer |

Responses include `X-Request-ID`. Errors do not expose server paths/stack traces. API Cache-Control is no-store.

## Cross-origin browser access

iframe-contained API requests do not need CORS. A client-built browser frontend on another origin must be listed exactly in `api_origins`. Only GET is authorised; cross-origin cookies/credentials are disabled. Allowed callers can read Content-Disposition and X-Request-ID. CORS and embedding policies are not authentication. If login is required, protect page, API and downloads at the gateway and agree the SSO design separately.
