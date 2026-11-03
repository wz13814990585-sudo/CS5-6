# Dashboard V1 validation record

Historical validation: 2026-11-01, macOS 14.5 arm64, Python 3.12.10, Node.js 25.2.1. This is an English translation of the original record; it is not a claim that these checks were rerun during translation. Original screenshots remain in Git history; current English illustrations are listed in [language support](LANGUAGE_SUPPORT.md#screenshots).

## Real data and automated checks

The local default was `saved_ensemble_20261101T062202_638390Z`: 13,517 predictions, 366 signal weeks, 210 backtest weeks. API final capital 149330.60888418998 and total return 0.49330608884189986 matched its original CSV. The browser showed 149,330.61 and +49.33%. The tracked delivered replay also loaded and matched values; no local runs directory was required for a fresh environment.

- TypeScript and Vite production build passed.
- 15 Dashboard tests passed; 87 research regression tests passed in the separate model environment.
- API coverage: original metrics/bytes; ranking date/search/pagination; invalid input, writes, no results, corruption, non-finite values, path/symlink escape, snapshot consistency and embed origins.
- At that validation date, npm audit reported zero known vulnerabilities and pip-audit of the fully pinned Python dependencies reported none. These are dated checks, not a current security guarantee.
- Dashboard dependencies were isolated; research source, inputs and frozen models were unchanged.

Log: api-tests.log (`dashboard/docs/api-tests.log` in the complete source package). Starlette emitted an httpx testing-adapter deprecation warning; runtime does not require httpx.

## Browser checks recorded at the time

1. Real metrics/chart loaded; Weekly return and Last 52 weeks displayed 2025-09-05–2026-08-28.
2. ANF on 2026-08-28 had rank 30 and score 0.3417; unmatched search showed an empty state.
3. Pagination showed ranks 11–20; 2019-08-30 had 27 ranked stocks, led by TJX at score 0.8272.
4. Switching to delivered retained the historical metrics and changed the source ID.
5. Same-origin iframe loaded and allowed searching.
6. A temporary host at 127.0.0.1:9001 embedded the module at port 8000 using an exact origin allowance; real metrics/search worked. Temporary configuration/server were removed afterwards.
7. At 390×844, page scrollWidth was 390; mobile navigation worked and ranking tables scrolled locally.
8. A real summary download completed; API checks confirmed original file bytes.
9. No application console errors were observed.

## Limits

Docker recipes existed but daemon/image/container execution was not tested. Public hosting, client HTTPS/login and target Windows/client CSP acceptance were pending. V1 was a historical-result viewer, not online training, arbitrary inference or trading.
