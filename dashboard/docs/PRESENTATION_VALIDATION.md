# Dashboard 1.4 presentation — historical validation

Date: 2026-11-02 (Australia/Sydney). Scope: read-only followed-stock queries and presentation interactions. macOS, Python 3.12, Node.js 25.2.1. Client-site deployment, Docker and SSO were outside scope. This English translation preserves the original record; the companion archive report records the latest English-first delivery checks.

## Automated checks

| Check | Recorded outcome |
|---|---|
| TypeScript / Vite build | Passed |
| Backend API/integrity tests | 49/49, including ten watchlist tests |
| Frontend language/search/storage/timeout tests | 12/12 |
| HTTP smoke | Passed; final capital 149330.60888418998, 210 weeks, 17,353 rows per input |
| verify-watchlist.mjs | Success, JSON export, no-data, invalid stocks and unchanged original metrics passed |
| Original research files | 207 non-Dashboard files unchanged against pre-feature main, excluding the manifest itself |

Commands used were `npm --prefix dashboard/frontend run build`, Python unittest discovery under `dashboard/tests`, Node tests under `dashboard/frontend/tests`, `dashboard/tools/smoke_check.py`, and `dashboard/examples/verify-watchlist.mjs`.

Backend tests covered supported tickers/companies, exact date/ticker joins to factors/prices/ranks, sample selection differences, null preservation, missing input/snapshot isolation, CSV/JSON, CSV escaping, unchanged strategy metrics/original downloads and structured invalid requests. Existing dependency deprecation and ResourceWarnings were non-fatal. Earlier 87 research regressions and research-run records were retained, not rerun for this feature.

## Browser checks recorded at the time

- 2026-08-28 example: SCL rank 1 selected; TJX rank 2 not selected; CMG rank 3 selected. Weights came from verified snapshots.
- TJX detail: five raw factors, rank 2, score 0.8083 and component percentiles 62.50/87.50/92.50%; no fabricated rejection reason.
- Company search Chipotle, URBN keyboard add/remove, duplicate prevention, unsupported AAPL, clear and reset worked.
- Switching to 2022-08-26 aligned research/allocation/input/ranking selectors and changed sample ranks to 34/23/35. Old results/export links were not presented for the new query. Input pagination reset on date changes.
- At 2019-08-30, ranks could exist without allocation; CMG had no rank. Missing allocation was distinct from not selected and null was not zero.
- Full source independently selected 2015-09-04 without changing research date; demo reset restored output alignment/date/search/chart state.
- Both languages retained state; all new visible and accessibility copy was covered. Refresh retained followed stocks and restored the latest backtest date.
- Actual CSV download had three sample rows and blank TJX weights; JSON export matched the API response.
- Desktop 1280×1000/default and mobile 390×844 were checked. Mobile page width remained 390 and only table containers scrolled horizontally. Temporary viewport settings were reset.
- No normal application console errors were observed.

## Fault isolation

A separate temporary local proxy returned 503 for the module page; the host showed loading, then retry/standalone fallback after 12 seconds while remaining usable. Restoring the proxy and retrying loaded the iframe and its readiness message. A watchlist-only 503 produced an isolated error/retry while original performance remained available; recovery reloaded correct rows. Frontend tests covered response/body timeouts and external cancellation. Temporary servers were stopped; real port 8000 data was not changed for fault injection.

## Portable package check at that time

The 1.4 preflight ZIP was extracted outside the repository, verified and served on port 8002, using the existing locked Web Python environment rather than a fresh install. It required no research environment or local runs directory. Run ID was delivered, inputs/allocations were available, and original-byte smoke / verify-watchlist passed. The final package then recorded the feature commit and independent checksum. This historical roundtrip is not claimed as a new-computer dependency installation.

## Screenshots and remaining integration work

Original screenshots are preserved in Git history. Current English-first delivery illustrations are listed in [language support](LANGUAGE_SUPPORT.md#screenshots), with the new archive's own validation report identifying when they were captured.

The client must still confirm hosting/authentication, exact origins and staging access, then validate actual entry placement and regression of other Portfolio functions. This record establishes a local demonstrable module and interface contract, not client production deployment.
