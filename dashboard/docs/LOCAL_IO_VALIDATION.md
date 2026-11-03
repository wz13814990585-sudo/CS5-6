# Local input/output 1.2 — historical validation

2026-11-01; macOS 14.5 arm64, Python 3.12.10, Node.js 25.2.1. Scope: existing inputs and historical outputs; Docker/public deployment deferred. English translation of the original record, not a new execution claim.

## Automated checks

- 30 Dashboard tests passed: the earlier 23 plus seven input tests. Log: local-io-tests.log (`dashboard/docs/local-io-tests.log` in the complete source package).
- TypeScript and Vite build passed.
- HTTP checks verified both input download hashes, 17,353 rows each, queried values against the original input files, and output bytes against the local replay: 13,517 predictions, 210 backtest weeks, final capital 149330.60888418998.
- Input coverage included full/output scopes, exact factors, label exclusion, pagination/search, invalid parameters, original downloads, missing inputs and identity mismatch rejection.
- The JavaScript example returned latest SCL factors/prices/rank 1/score about 0.925 and backtest summary.
- Packaging 1.2 included both inputs, configuration and manifest with the result. A temporary ZIP extracted separately passed file, page, input-query and summary checks using the existing Web environment; it did not repeat a fresh installation. Version 1.1's fresh install is documented separately.
- OpenAPI included the input catalog/query/download contracts.

## Browser checks

Real factor/price tables, date/ticker filtering and source/output scopes worked. ANF 2026-08-28 View output linked to rank 30 / score 0.3417. Full source allowed 2015-09-04 with an outside-prediction-range label. Copied URLs matched date, stock, scope and page. At 390px, there was no page-wide overflow; tables scrolled locally and output links stayed accessible. No browser warning/error was recorded.

Models, inputs and historical outputs were unchanged. No upload, live inference, training or trading flow was added. The earlier research regression/computation record was not rerun for this step. Historical screenshots remain in Git history; see [current English illustrations](LANGUAGE_SUPPORT.md#screenshots).
