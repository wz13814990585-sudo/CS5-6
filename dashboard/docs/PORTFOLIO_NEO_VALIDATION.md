# Portfolio Neo module 1.3 — historical validation

Date: 2026-11-01. Feature branch: `feature/cs5-6-portfolio-neo-integration`. Scope was this project's local module and host preview, not the client's actual site. English translation of the original record.

## Checks passed

- 39/39 backend tests: existing APIs/input identities/downloads/origin policies plus allocation contract, disjoint 66/40 scope, selection differing from top raw ranks, all-week weight totals, missing/corrupt snapshots, no-data/invalid dates/unknown runs.
- TypeScript/Vite production build and six language tests, including PortfolioPanel copy coverage.
- `verify-module.mjs`: success 200; no-data 200/no_data; invalid date 422/error; unknown run 404/error.
- Offline allocation export for two saved serialisations, 210 weeks each. Maximum error across eight original weekly account/return/cash/fee fields was 0. Independent accounting: 9586 checks per variant, maximum error 2.842170943040401e-14. Saved predictions were replayed; no training/new predictions occurred.
- Relative to the task-start manifest, 207 non-Dashboard file hashes were identical, preserving original models/data/reports/predictions/backtests.
- Desktop 1440×1000 and phone 390×844 had no page-wide horizontal overflow; wide tables scrolled inside containers.
- Browser interactions: English/Chinese switch; allocations 2026-08-28 → 2022-08-26; first-date holdings PLAY/CROX/LW/SBUX/BJ; PLAY linked to its date/rank; language retained selection; methodology expanded; host card opened/closed iframe; iframe language updated the same-origin shell.
- Benchmark/currency used unavailable/null with reasons. No independent financial publication timestamp was asserted.

## Metric conventions

Common210 / FullHistory covers 2022-08-26–2026-08-28. Initial capital 100000; final capital 149330.60888418998; total return 0.49330608884189986; annualised 0.1043902627962429; maximum drawdown −0.24878123919912354; Sharpe 0.5434211006497096. Annualisation compounds using 52 weeks/year, separate from the shorter final-test period in the report.

Final-period stocks SCL/CMG/UTZ/RH/URBN have raw ranks 1/3/4/6/7, 20% targets and integer-share actual weights; cash is approximately 0.22496%. Positions were liquidated at the period end; this is not current holdings.

## Evidence and boundaries

Original version screenshots remain in Git history. [Current English screenshots](LANGUAGE_SUPPORT.md#screenshots) illustrate the latest delivery and are not represented as historical 1.3 screenshots.

Actual client placement, authentication, global routing, other teams' ontology/modules, domain policies, whole-site behavior during module outage, deployment and production release were not performed. These require client repository/staging access and core-team review. Docker/public deployment remained deferred. Existing Starlette/httpx deprecation and input-test ResourceWarnings did not prevent passing checks; dependencies were not upgraded to suppress them.
