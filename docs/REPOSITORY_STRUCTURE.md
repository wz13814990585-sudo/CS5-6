# Repository structure

```text
CS5-6/
├── README.md                         # Quick start and canonical paths
├── requirements.txt                 # Python runtime dependencies
├── raw data/                         # Acquisition/factor-generation source code
│   ├── fetch_and_clean(1).py         # Download and clean daily Yahoo OHLCV
│   ├── build_technical_factors.py    # Build the common-date 45-factor weekly panel
│   └── collect_sec_fundamentals.py   # Point-in-time SEC fundamental factors
├── data/                             # Generated datasets
│   ├── clean_basic_data.csv          # Canonical cleaned daily OHLCV (generated locally)
│   └── test_data_weekly.csv          # Canonical weekly factor panel
├── factor_analysis/
│   ├── __init__.py                   # Package marker
│   └── build_weekly_factor_analysis.py # Warmup factor analysis and factor-set export
├── ml/
│   ├── __init__.py                   # Package exports
│   ├── config.py                     # Dates, paths, features, and search constants
│   ├── data.py                       # Shared calendar, weekly target, and leakage guards
│   ├── factor_sets.py                # Factor-set JSON loading and validation
│   ├── relevance.py                  # Date-local ordinal relevance labels
│   ├── metrics.py                    # Date-first Rank IC, NDCG, and Top-K metrics
│   ├── validation.py                 # Chronological folds and date checks
│   ├── xgb_ranker.py                 # XGBRanker fit/predict adapter
│   ├── optimize_ranker.py            # Warmup-only joint configuration search
│   ├── rolling.py                    # Frozen monthly full-window rolling OOS fits
│   ├── forward_selection.py          # Optional warmup forward-selection research
│   └── run_xgb_ranker_experiments.py # Official end-to-end ML entry point
├── tests/                            # Automated correctness/leakage tests
├── outputs/
│   ├── factor_analysis/              # Current official factor outputs
│   └── xgb_ranker/                   # Current official frozen-ranker outputs
├── archive/
│   ├── legacy_data/                  # Preserved non-canonical data fragments
│   ├── legacy_outputs/               # Historical/duplicate experiment outputs
│   ├── legacy_analysis/              # Old manual analysis artifacts
│   └── legacy_scripts/               # Reserved for obsolete scripts (currently none)
└── docs/
    ├── ARCHITECTURE.md                # Research methodology and timing
    ├── REPOSITORY_STRUCTURE.md        # This repository map
    └── CLEANUP_REPORT.md              # Cleanup decisions and evidence
```

Only `outputs/factor_analysis/` and `outputs/xgb_ranker/` are official result locations. Nothing under `archive/` is imported or consumed by the pipeline.
