# Weekly cross-sectional XGBRanker research pipeline

This repository builds weekly stock-ranking signals from daily market, fundamental, and macro data. The model predicts ranking scores—not percentage returns—for the following full market week.

## Repository layout

- `raw data/` — data acquisition and factor-generation source code (the name is historical; generated data does not live here).
- `data/` — generated daily and weekly datasets. The canonical weekly panel is `data/test_data_weekly.csv`.
- `factor_analysis/` — warmup factor evaluation and factor-set construction.
- `ml/` — chronological warmup selection and frozen XGBRanker rolling OOS pipeline.
- `tests/` — target, leakage, grouping, rolling, and metric tests.
- `outputs/factor_analysis/` — current official factor-research results.
- `outputs/xgb_ranker/` — current official model results.
- `archive/` — preserved legacy artifacts; never read by the main pipeline.
- `docs/` — methodology, repository map, and cleanup record.

## Execution order

```bash
python 'raw data/fetch_and_clean(1).py'
python 'raw data/build_technical_factors.py'
python -m factor_analysis.build_weekly_factor_analysis
python -m ml.run_xgb_ranker_experiments
```

The factor builder writes `data/test_data_weekly.csv`. Factor analysis and ML both consume that same path through `ml.config.DATA_FILE`.

The first three complete years (2016–2018) are the only configuration-selection period. From 2019 onward, the selected factor set, objective, relevance bins, and hyperparameters remain frozen while models refit monthly on the full eligible trailing three-year window.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for research timing and [REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md) for file responsibilities.
