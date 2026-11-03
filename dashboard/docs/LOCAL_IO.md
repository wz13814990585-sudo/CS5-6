# Local Dashboard: inputs, outputs and interfaces

The Dashboard reads existing project files and verified historical results. All APIs are read-only: queries do not accept uploads, train models or rerun calculations. Use the native Python service; Docker is not required. First installation is documented in [START_HERE](../../START_HERE.md).

## Start and browse

From the installed project root, run `.venv-dashboard/bin/python dashboard/start.py` (Windows: `.\.venv-dashboard\Scripts\python.exe dashboard/start.py`). For a configured Web package append `--config config.toml`. Open <http://127.0.0.1:8000/?lang=en> and keep the terminal running.

1. Open **Input data**, choose **Model factor inputs** or **Backtest price inputs**, then select a date or search a ticker.
2. **Aligned with this output** is the default scope; **Full source file** exposes earlier history on an independent date. Wide tables scroll inside their own containers.
3. Click **View output** to show the same date/ticker in Stock rankings. Inputs earlier than prediction coverage are explicitly marked outside that coverage.
4. **Performance** shows the original full strategy; raw stock rankings are before filtering and are not actual holdings. Use **Stocks & weights** for the saved allocation.
5. Copy the current query URL or open JSON. Full-input downloads preserve the entire original file; watchlist exports use the selected date/stocks.

Restart the Python service after changing data. Refreshing the browser does not reload disk files.

## Language

English is the first-visit default. The **English / Chinese** selector preserves run, date, stock search, input scope, pagination and chart choices. Explicit `?lang=en` or `?lang=zh` overrides a saved preference; existing Chinese preferences remain honoured. Use `?embed=1&lang=en` for an English client embed. API display labels/reasons are English; the optional Chinese UI translates those labels locally. Numerical values, identifiers and original research downloads are not translated or reformatted.

## Model inputs

| Input | Project path | Purpose |
|---|---|---|
| Raw model factors | `external_validation/ensemble_ranker/inputs/test40.csv` | date/ticker and five financial factors; models transform them to within-week percentiles |
| Historical execution prices | `external_validation/shared_inputs/inputs/test40_with_prices.csv` | next-week open/close proxies for the historical backtest |

Factors: `revenue_growth_yoy`, `operating_profitability`, `cashflow_to_assets`, `debt_to_assets`, `asset_growth_yoy`. `stock_name` is a display label.

Each source file has 17,353 rows over 574 signal weeks, 2015-09-04 to 2026-08-28. Predictions align to 13,517 factor rows / 366 weeks; portfolio outputs align to 8,354 price rows / 210 weeks. Earlier prices may still support the 13-week lookback, so output alignment does not mean only those rows were used in computation.

Original CSVs also contain research fields such as `target1/target2`; complete downloads preserve them. Queries expose the listed input fields only. Future-return labels are not prediction or selection inputs.

Input identity is checked against model configuration, saved-model manifest and prediction/backtest verification records. Missing or mismatched inputs become unavailable while verified outputs remain accessible. SHA-256 checks file consistency, not authenticity from a third party.

## Outputs

- 13,517 stock-week model predictions: ensemble rank/score and three component percentiles, linked by signal date and ticker.
- 210 weekly account observations: capital, net return, cash, fees and drawdown.
- Full strategy metrics: initial capital 100000, final capital approximately 149330.61, total return 49.33%; the actual selected run's CSV is authoritative.
- Original prediction, capital, summary and verification downloads.

The Dashboard does not regenerate these outputs. Development checkouts select the latest valid local replay; fresh packages use the tracked verified replay. Request `/api/cs5_6_equity/v1/runs` for the actual ID.

## Query interfaces

Base URL: `http://127.0.0.1:8000/api/cs5_6_equity/v1/`.

| Purpose | GET path |
|---|---|
| Active run | `runs` |
| Inputs and fields | `runs/{id}/inputs` |
| Factors | `runs/{id}/inputs/factors/rows?date=2026-08-28&q=ANF&scope=output` |
| Prices | `runs/{id}/inputs/prices/rows?date=2026-08-28&q=ANF&scope=output` |
| Complete input | `runs/{id}/inputs/{dataset}/download` |
| Linked ranking | `runs/{id}/rankings?date=2026-08-28&q=ANF` |
| Summary | `runs/{id}/overview` |
| Account series | `runs/{id}/equity` |

`dataset` is `factors` or `prices`. Input rows accept `scope=output` or `source`; omit date for all dates in that scope. Page numbering starts at 1; page size is at most 100. `q` searches a ticker substring; joins still use exact date + ticker.

Provide the client [OpenAPI](openapi.json), [API guide](API_V1.md) and [JavaScript example](../examples/client.mjs). Run the example with `node dashboard/examples/client.mjs http://127.0.0.1:8000/`; it discovers the run/date and prints one stock's factors, prices, ranking, summary and download URLs. For a hosted installation replace the base URL and configure exact `api_origins` for cross-origin browser callers. Localhost refers to the caller's own computer.
