# Changelog

## 2026-11-01

- Added Chinese/English Dashboard switching, persistent language preference, language-specific embed links and translated input/output views while preserving active filters and API data contracts.

- Added Dashboard 1.2 local input/output browsing: identity-checked factors and price inputs, source/output coverage, row-to-ranking links, versioned query/download endpoints and an executable client example. Docker deployment is deferred.

- Added customer delivery 1.1: deployment configuration, versioned typed read-only API, separate iframe/CORS origins, portable prebuilt ZIP tooling, installation and checksum checks, and clean-environment HTTP acceptance. All 23 web tests passed; container runtime and customer-specific deployment remain unverified.

- Added a standalone/embed React Dashboard and read-only FastAPI service for real verified replay results, including charts, date/search/pagination, exact file downloads, domain-scoped embedding, isolated dependencies and deployment guidance.

- Corrected the training guide, root README and data guide to list the required daily adjusted-close input and describe checks of all labels, including final-week and gap-adjacent rows.
- Revalidated the current runtime on macOS in an isolated pinned-dependency environment: 87 regression tests, all 13,517 frozen predictions, the selected 210-week strategy, and all 45 newly fitted training-demonstration snapshots passed.
- Added current command logs, input/source/output identities and numerical verification records. Preserved the October 26 Windows record separately and left original data, frozen models and delivered historical outputs unchanged.
- Refreshed the release inventory for the documentation and validation evidence.

## 2026-10-29

- Independent accounting now rebuilds each week's OPEN orders from ranks, prices, target weights and cash for Top5, Top10, Top5_RankWeighted and Top5_NoLoss13w, and requires the delivered orders to match exactly. A held position below its target is accepted only when remaining cash cannot fund one more share, so partial (for example half-size) positions are rejected.
- Training preparation now verifies every supplied label, including the 16 rows whose next weekly row is missing and the final-week rows, as ln(daily adjusted close on the label end date / weekly adjusted close) using `data/clean_basic_data.csv` (training tickers only; no external test stocks). The daily file is a verification reference and is now part of the training input identity.
- The integer-share engine returns order and holding tables with fixed columns, so an all-cash run with no trades no longer raises `KeyError: 'date'`; the verifier also accepts column-less empty ledgers.
- Added regression tests for partial positions, all-cash runs, labels before missing weeks and final-week labels.
- Refreshed RELEASE_MANIFEST.json, including the README files clarified after the 2026-10-26 release. docs/VALIDATION.md and docs/validation_results.json remain the 2026-10-26 validation record.

## 2026-10-26

- Restricted external strategy delivery to the frozen Ensemble Top5_NoLoss13w Common210 FullHistory case.
- Removed standalone external Ranker fitting, model artifacts, predictions and comparisons.
- Converted V1 into a training-only Ensemble demonstration using the supplied processed weekly training data. Removed external prediction, backtest, reporting and resume interfaces from this workflow.
- Removed retrained-Ensemble external results and separate final-year annualised-return displays from the external result package.
- Retained original four-model research methodology and evidence.
- Documented strategy selection, 13-week filtering, equal target allocations, integer shares, fees and cash rules.
- Retained a verified complete frozen replay with predictions, weekly capital and numerical verification records. Individual order and holding exports are outside the presentation scope.
- Defined reproduction as starting from the supplied processed weekly data; raw acquisition and reconstruction are outside delivery scope.
- Added regression coverage for the training-only boundary and preserved failure/status, exact inference and independent accounting checks. See docs/VALIDATION.md for validation outcomes.
- Kept delivery text in English and refreshed file-integrity manifests.
