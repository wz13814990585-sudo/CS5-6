# Client demonstration and website integration guide

Dashboard 1.4, English-first edition. For a ready-to-read 8–10 minute presentation use [PRESENTATION_SCRIPT_EN.md](PRESENTATION_SCRIPT_EN.md). This guide provides a deeper 12–15 minute walkthrough and integration discussion. Figures refer to the supplied verified historical result; recheck them if changing the run.

## Purpose

Help the client understand where data comes from, what the models output, and how the results can be used on their site.

```text
Existing factors → within-week percentile transforms → saved models → stock rankings
Stock rankings + historical prices + strategy rules → backtest → capital and metrics
```

The Dashboard reads these completed inputs/outputs. Page navigation, searches and date changes do not rerun training or the backtest. Stock/date preferences are different from model factor inputs.

## Prepare

Install using [START_HERE](../../START_HERE.md); keep a working service running rather than starting a duplicate. Open the English Dashboard `/?lang=en#watchlist`, host preview `/embed-example.html?lang=en`, and `/api/docs`. If Swagger cannot load its external CDN, use `/api/openapi.json` or [packaged OpenAPI](openapi.json).

English is the fresh-browser default. A previously saved Chinese preference is respected, so use the explicit English URL when presenting. Click Reset demo then Load demo example; confirm SCL/TJX/CMG, 2026-08-28. Keep the same run throughout. Prepare the [English screenshots](LANGUAGE_SUPPORT.md#screenshots) as a clearly labelled saved fallback. Hide unrelated accounts, credentials and private windows while recording.

## Walkthrough

| Stage | Actions | Explain |
|---|---|---|
| User preference | Search Chipotle, show CMG deduplication, add/remove URBN | Forty supported external stocks; preferences choose what to inspect |
| Linked outputs | Compare SCL/TJX/CMG ranks 1/2/3 and selection | SCL/CMG selected; TJX not selected. Rank and actual allocation are different outputs |
| Stock detail | Open TJX View details | Five raw factors, score 0.8083, component percentiles 62.5/87.5/92.5%; not expected returns or probabilities |
| Historical date | Choose 2022-08-26, visit allocations/inputs/rankings | Shared date gives ranks 34/23/35; none of the three selected. Restore the example afterwards |
| Actual holdings | Inspect Stocks & weights | Latest allocation SCL/CMG/UTZ/RH/URBN, raw ranks 1/3/4/6/7, 20% targets and slightly different integer-share actual weights; cash shown separately |
| Full performance | Switch Account value, Weekly return, Drawdown and chart window | Metrics always represent the original full strategy, not a followed-stock portfolio |
| Input evidence | Switch factors/prices; search a ticker; show full source vs output-aligned scope | Existing original values and explicit coverage; join by exact date/ticker |
| Exports | Download current watchlist CSV/JSON and a complete input/result file | Current-selection export differs from full original files; null is not zero |
| Provenance | Open Verification & files and methodology details | Passed file checks, saved model/strategy assumptions and historical simulation scope |
| Integration | Show API JSON, then open the host card/iframe | Same module via iframe or same data via client-native UI; actual hosting/authentication/staging still required |

Five raw TJX factors on 2026-08-28: revenue growth 0.116225, operating profitability 0.329211, cash flow/assets 0.223447, debt/assets 0.079374, asset growth 0.134974. These are display-rounded values; the API returns numeric values and original files retain precision. The model applies within-week percentile transformations.

## Performance and research scope

| Item | Saved result |
|---|---|
| Full backtest signal period | 2022-08-26 to 2026-08-28 |
| Signal weeks | 210 |
| Initial / final research capital | 100000 / 149330.60888418998 |
| Total / annualised return | 49.33% / 10.44% |
| Maximum drawdown / Sharpe | −24.88% / 0.543 |
| Model prediction coverage | 13,517 stock-week rows, 366 signal weeks |
| Source input coverage | Each CSV: 17,353 rows, 574 weeks, 2015-09-04–2026-08-28 |
| Output-aligned price rows | 8,354 rows over 210 weeks |
| Research universes | 66 training stocks; 40 separate external stocks; no ETFs |

The full-history simulation is separate from the report's shorter final-test results. Annualisation uses 52-week compounding. Strategy assumptions include weekly signals, a trailing 13-week nonnegative return filter, up to five positions, integer shares, 10 bps per side and next-week historical open/close proxies. Final positions were liquidated. Currency and a matched verified benchmark are unavailable; do not assert market outperformance, live holdings, future guarantees, independent financial-publication timing or S&P 500 historical membership.

## Input/output and missing-data explanations

Source factor inputs are `external_validation/ensemble_ranker/inputs/test40.csv`; price inputs are `external_validation/shared_inputs/inputs/test40_with_prices.csv`. Full CSVs include research labels target1/target2, but those labels are not model inputs or selection signals. Earlier price rows may support the 13-week filter even when they are outside displayed output alignment.

Use 2019-08-30 in Stock rankings to show no allocation coverage; CMG also has no rank that week. An absent allocation record differs from a verified decision not to select a stock. Search AAPL to demonstrate the unsupported universe boundary. No stock-specific TJX exclusion reason is stored, so describe the outcome without inventing its cause.

## Client integration discussion

Provide the [API guide](API_V1.md), [OpenAPI](openapi.json), [JavaScript example](../examples/client.mjs), and [integration handoff](PORTFOLIO_NEO_INTEGRATION.md). Start with `/api/cs5_6_equity/v1/runs` to find the run ID. Input, ranking, watchlist, allocation, performance and download queries are all read-only. Display text is English; missing data is null/unavailable and weights/returns use fractions.

For iframe, host the module on an agreed dedicated HTTPS origin, add a Strategy Lab card and configure exact embed_origins plus the client's frame-src policy. A client-built interface can use the APIs; different-origin browser calls need api_origins. Neither allowlist implements authentication. The client gateway must protect page, API and downloads if login is required.

The module remains independent of the host's single-asset selector, ontology, global routing and other strategies. Ask the client to confirm hosting, domains, access control, maintenance/update ownership, staging and regression acceptance. The core team reviews the client feature branch/PR and controls production deployment. A successful local iframe demo is not a claim of completed client production integration.

## Close and handle questions

Summarise the demonstrated path: followed stocks → inputs → rankings/actual allocations → original performance → exports → integration options. Explain that uploads, live data, online model runs, new universes, personalised backtests, trading and SSO need separate scope.

If a query fails, use Retry and check the local service. If iframe loading fails, use its Retry module/standalone entry. If the service cannot be restored, explicitly identify backup screenshots as saved validation images. Do not present a saved image as a live result. See the English script for detailed answers and spoken fallback wording.
