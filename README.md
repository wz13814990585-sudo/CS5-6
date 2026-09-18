# Weekly cross-sectional XGBRanker research pipeline

This project ranks stocks at each week-end using only information available by that close. The primary target is the following market week's adjusted Open-to-Close log return. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for timing, leakage controls, periods, and the SEC filing-date rule.

Run the corrected development-only factor analysis:

```bash
python -m factor_analysis.build_weekly_factor_analysis
```

Run a fast four-set smoke experiment or the complete experiment:

```bash
python -m ml.run_xgb_ranker_experiments --quick --run-forward-selection
python -m ml.run_xgb_ranker_experiments --full
python -m ml.optimize_ranker
```

Useful switches include `--factor-set core_5`, `--objective rank:pairwise`, `--skip-tuning`, and `--common-sample`. Both common-sample and native-coverage results are always exported. Outputs are written beneath `outputs/factor_analysis` and `outputs/xgb_ranker`.
