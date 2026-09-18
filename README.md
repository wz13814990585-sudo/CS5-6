# Weekly cross-sectional XGBRanker research pipeline

This project ranks stocks at each week-end using only information available by that close. The primary target is the following market week's adjusted Open-to-Close log return. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for timing, leakage controls, periods, and the SEC filing-date rule.

Build the local daily OHLCV source, then run the warmup-only factor analysis:

```bash
python 'raw data/fetch_and_clean(1).py'
python -m factor_analysis.build_weekly_factor_analysis
```

Run the complete frozen-configuration experiment:

```bash
python -m ml.run_xgb_ranker_experiments
```

The runner jointly selects the factor set, ranking objective, relevance bins, and controlled hyperparameters using chronological folds entirely within 2016–2018. It freezes that configuration before fitting monthly full-window rolling models from 2019 onward. Outputs are written beneath `outputs/factor_analysis` and `outputs/xgb_ranker`.
