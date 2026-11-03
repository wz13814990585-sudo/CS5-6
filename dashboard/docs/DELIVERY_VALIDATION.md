# Customer delivery 1.1 — historical validation

Date: 2026-11-01. Environment: macOS 14.5 arm64, Python 3.12.10, Node.js 25.2.1. English translation of the original acceptance record. For the latest archive-specific results use the companion final delivery report; translation does not rerun historical checks.

## Implemented and checked

- Historical result browsing, queries, downloads and embedding retained.
- TOML/environment/CLI configuration precedence, relative result paths and rejection of invalid settings.
- Typed `/api/v1` contract, OpenAPI, unified errors/request IDs and compatible `/api`; distinct CORS and iframe origins.
- Native installer, source/delivery Compose references, proxy configuration, updates and rollback guidance.
- ZIP containing built frontend, server/source, real snapshot, locked dependencies, offline contract, install/verify/smoke tools and SHA-256 manifest.
- Extraction outside the repository followed by a fresh Python 3.12 environment and installation from pinned dependencies. No pandas/XGBoost and no Node.js needed for runtime.

## Results

All 23 web tests passed, as did TypeScript/Vite builds and both Compose configuration parses. This established configuration validity only, not container runtime. Package hashes and sizes verified. The extracted server passed HTTP acceptance from an independent working directory: 13,517 predictions, 210 weeks, final capital 149330.60888418998.

The smoke check covered page/script assets, health, rankings, account/summary consistency, four original downloads byte-for-byte and the 404 error contract. The JS example returned actual final capital and latest leader SCL. OpenAPI was generated from current response models. Logs: integration-tests.log (`dashboard/docs/integration-tests.log` in the complete source package).

The browser displayed real metrics and delivered provenance; searching, downloads and iframe examples worked. Prior mobile/cross-origin evidence is in [V1 validation](VALIDATION.md). Original research files/models were unchanged; their 87-test record was maintained separately.

## Remaining limits

Docker daemon was unavailable, so image/container startup was not tested. Windows/Linux native runtime, client HTTPS/domains/login and client CSP were not integrated. The module was read-only historical research, not live analysis or trading. Original screenshots remain in Git history; [current English screenshots](LANGUAGE_SUPPORT.md#screenshots) illustrate the latest UI rather than version 1.1.
