# SafeCapital client delivery development plan

## Current delivery

Dashboard 1.4 provides multiple followed stocks, shared historical dates, linked input/model/allocation details, example reset, CSV/JSON exports and failure/retry handling. See [workflow](PRESENTATION_WATCHLIST.md) and [feature validation](PRESENTATION_VALIDATION.md). The 2026-11-03 client revision makes documentation/API display text English and defaults new UI visits to English, with Chinese retained as an optional preference.

The current goal is local input/output visibility and documented read-only interfaces. Existing source files and verified results are used; no upload, new inference, training or trading flow is introduced. Docker, public hosting and client-domain integration are deferred until environment details are supplied.

## Delivery stages

| Stage | Work | Acceptance |
|---|---|---|
| Scope and baseline | Real metrics/charts/rankings/downloads/provenance | Original CSV values and research evidence preserved |
| Configuration | TOML, environment overrides, CLI and startup validation | Port/origin/result directory configurable without source edits; invalid configuration rejected |
| API contract | Namespaced v1 models, errors, OpenAPI, JS examples and exact CORS | Documented calls, compatibility aliases, no cross-origin authorisation for unlisted sites |
| Operations | Health, reverse proxy, update/rollback guidance | State actual platform/HTTPS/login responsibilities; old Compose examples remain deferred |
| Packaging | Prebuilt frontend/server, verified snapshot, matched inputs, dependency locks and hashes | Web ZIP excludes secrets/local environments/full training project; Source ZIP retains complete tracked research |
| Acceptance | Tests, fresh extraction/environments and HTTP/browser checks | Real outputs served without requiring research libraries or Node.js for Web |

The original six-stage delivery was validated on the native macOS path with 23 tests in version 1.1. Version 1.2 added input binding, coverage distinctions, browsing and APIs; version 1.3 added actual allocations and module scope; version 1.4 added presentation watchlists. These are dated milestones, not claims of repeated execution. See each validation record and the companion final archive report for exact coverage.

## Integration information needed from the client

- Final module address and exact embedding/API origins.
- Hosting platform and operational owner; any container requirement.
- Login/SSO requirements, including protection for page/API/downloads.
- Staging access and regression expectations for other Portfolio modules.
- Ownership and frequency of future verified-result updates.

## Later features requiring separate scope

New data ingestion, scheduled computation, new stock universes, uploads, parameterised backtests, online training/inference, fuller trade exports, rank-history charts, print reports, multi-tenant accounts and SSO. APIs and versioned snapshots provide extension points, but the current interface must not claim these features are implemented.
