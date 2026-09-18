# Repository cleanup report

Cleanup preserved the research methodology and changed only paths, generated-output names, documentation, and artifact placement.

| Path | Status | Action | Reason |
|---|---|---|---|
| `raw data/fetch_and_clean(1).py` | ACTIVE | Kept | Official daily-data entry point |
| `raw data/build_technical_factors.py` | ACTIVE | Kept | Generates canonical weekly panel |
| `raw data/collect_sec_fundamentals.py` | ACTIVE | Kept | Used by factor builder |
| `data/Original_basic_data.csv` | GENERATED | Kept locally, ignored | Reproducible raw download |
| `data/clean_basic_data.csv` | GENERATED | Kept locally, ignored | Required daily input for targets and factors |
| `data/test_data_weekly.csv` | ACTIVE | Kept as canonical | Single weekly dataset consumed downstream |
| `factor_analysis/test_data_weekly.csv` | DUPLICATE | Removed old path | Canonical file is under `data/` |
| `factor_analysis/build_weekly_factor_analysis.py` | ACTIVE | Kept | Official factor-analysis entry point |
| `factor_analysis/weekly_factor_analysis_from_original_csv.xlsx` | LEGACY | Moved to `archive/legacy_analysis/` | Unreferenced manual spreadsheet |
| `ml/config.py`, `data.py`, `factor_sets.py` | ACTIVE | Kept | Core configuration, data, and feature contracts |
| `ml/relevance.py`, `metrics.py`, `validation.py` | ACTIVE | Kept | Current labeling, metrics, and time folds |
| `ml/xgb_ranker.py`, `optimize_ranker.py`, `rolling.py` | ACTIVE | Kept | Current ranker implementation |
| `ml/run_xgb_ranker_experiments.py` | ACTIVE | Kept | Official ML entry point |
| `ml/forward_selection.py` | OPTIONAL | Kept | Planned research feature; currently not called |
| `outputs/factor_analysis/` | GENERATED | Kept | Official current factor outputs |
| `outputs/xgb_ranker/` | GENERATED | Kept | Official current model outputs |
| `outputs/xgb_ranker_optimized/` | LEGACY | Moved to `archive/legacy_outputs/` | Superseded 2016–2023 optimization flow |
| Old compatibility output aliases | DUPLICATE | Moved to `archive/legacy_outputs/compatibility_aliases/` | Byte-identical current aliases or stale optional output |
| `raw data/test_data_weekly.csv.textClipping` | LEGACY | Moved to `archive/legacy_data/` | Finder clipping, not a dataset |
| `.DS_Store` files | GENERATED | Deleted | OS metadata, ignored and reproducible |
| `tests/` | ACTIVE | Kept | Correctness and leakage verification |

## Duplicate evidence

SHA-256 comparisons confirmed these moved pairs were byte-identical:

- `factor_correlation.csv` and `warmup_factor_correlation.csv`
- `factor_metrics_by_date.csv` and `warmup_factor_metrics_by_date.csv`
- `factor_selection_summary.csv` and `warmup_single_factor_summary.csv`
- `xgb_ranker_hyperparameter_results.csv` and `warmup_ranker_search.csv`
- `xgb_ranker_factor_set_comparison.csv` and `warmup_factor_set_comparison.csv`
- `xgb_ranker_summary.csv` and `xgb_ranker_oos_summary.csv`

Generated official CSV/JSON results remain tracked for review and grading. Large locally regenerated daily files remain ignored. No research logic was changed.
