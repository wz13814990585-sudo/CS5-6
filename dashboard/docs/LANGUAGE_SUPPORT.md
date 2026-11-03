# English-first delivery and optional Chinese interface

Client revision: 2026-11-03; Dashboard 1.4.0. English is the primary documentation, API display language and initial UI language. Chinese is an optional UI preference, not the first-visit default.

## Behavior

- The language selector lists English first. It remains available in embedded mode.
- Priority: valid URL `lang` parameter → valid saved browser preference → English. Invalid/missing settings fall back to English. A user who explicitly chose Chinese keeps that preference; use `?lang=en` for an English presentation link.
- Switching preserves the run, historical date, stocks, searches, scope, pagination and chart choices. It does not rerun calculations.
- Share `/?lang=en` or `/?lang=zh`; iframe links use `/?embed=1&lang=en` or `zh`. Copied embed code retains the selected language.
- If storage is unavailable, switching still works; the URL retains the selected language. The example shell follows the language of its same-origin iframe.
- Initial HTML lang/title/description and the no-preference host page are English, including before React finishes loading.

Coverage includes navigation, metrics/charts, factor/price labels, provenance/status, rankings, allocations, watchlists, downloads, integration guidance, loading/empty/error states and accessibility text. Dates/numbers follow display locale, while raw identifiers/values stay unchanged.

## API and files

API human-readable labels, notices, reasons and errors are English. The optional Chinese UI translates canonical English backend display text through the same catalog. Structured field names, codes, status enums, numerical outputs and original CSV/model/report bytes remain stable. English docs explain errors; no language query is required for API use.

All primary Markdown guides, installation instructions, API docs, plans and historical validation records are English. The primary speaking script is [PRESENTATION_SCRIPT_EN.md](PRESENTATION_SCRIPT_EN.md). The compatible `PRESENTATION_SCRIPT_ZH_EN.md` begins with the complete English script and contains a collapsed optional bilingual reference. Chinese text in localization source/tests and that optional reference is deliberate secondary-language content.

The research PDF, Word guide and workbook text were audited for language without changing their values. Original computed data and trained model artifacts are not translated. Current screenshots are captured from the English UI. Earlier screenshot files remain available in Git history, preventing old Chinese-only illustrations from becoming the client's default evidence.

## Maintenance and checks

The catalog is `dashboard/frontend/src/messages.ts`; language resolution/link rules are in `i18n-core.ts` / `i18n.tsx`. Chinese source keys are internal localization identifiers paired with English text. API strings are canonical English; reverse lookup supports the optional Chinese interface. Add copy to the catalog when adding UI features.

```bash
node --experimental-strip-types --test dashboard/frontend/tests/*.test.ts
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python -m unittest discover -s dashboard/tests -v
```

Tests cover default/URL/saved preference rules, placeholders, translated copy, English backend labels in both UI languages, query timeouts and watchlist behavior. The companion English-first delivery report records fresh archive installation and live browser/API checks.

## Historical bilingual validation

The initial 2026-11-01 bilingual build passed six language tests, TypeScript/Vite, HTTP input/output checks and real iframe interaction. ANF at 2026-08-21 remained rank 29 / score 0.3833 across switching; Last 52 weeks / Drawdown choices remained. Refresh retained English; URL choices overrode storage. A 390px check had no page overflow and no final browser warning/error. That initial release defaulted to Chinese; the current revision intentionally changes the fallback to English. These are separate dated validations.

## Screenshots

Current English illustrations, captured for this client revision:

- [Watchlist](client-watchlist-en.png)
- [TJX details](client-details-en.png)
- [Mobile view](client-mobile-en.png)
- [Local embedding example](client-embed-en.png)

These screenshots are saved evidence, not live data or client production deployment.
