# Research pipeline architecture

Daily Yahoo OHLCV supplies the shared market calendar. Each W-FRI week has one common decision date: its final actual market session. A ticker missing on that date is excluded rather than falling back to an earlier session. A terminal Monday–Wednesday partial week is removed; a legitimate Thursday-ending holiday week remains.

The canonical weekly factor artifact is `data/test_data_weekly.csv`: `raw data/build_technical_factors.py` writes it, and factor analysis plus ML read the same path from `ml.config.DATA_FILE`.

The target is constructed independently from daily rows: `log(next week last adjusted close / next week first adjusted open)`, where adjusted open is `open * adj_close / close`. X at the end of week t is joined to the exact `market_week_id + 1`; missing weeks never jump to t+2. `target_observation_date` is the target week's final market session.

`factor_analysis.build_weekly_factor_analysis` performs date-local Rank IC, quintile, stability, coverage, and redundancy analysis only in the first three complete modeling years, 2016–2018. Technical baselines require 80% coverage. Fundamental factors use a separate 50% rule and appear only in explicitly named extension sets. Cross-sectional rank copies are analyzed but excluded from the default admissible pool.

`ml.run_xgb_ranker_experiments` jointly compares factor sets, objectives, relevance bins, and controlled parameters through expanding chronological folds inside 2016–2018. One configuration is frozen. From 2019 onward, the first prediction date of each month fits a new model on the full eligible trailing three-year window; recent weeks are not held out. Labels must be observable before refit. Scores are called ranking scores, never predicted returns, and no post-warmup result can alter the frozen configuration.

The SEC collector uses the latest filing date needed by a derived factor, then delays availability to the next observed market day before an as-of backward merge. This is a conservative filing-availability rule. It does not model intraday SEC acceptance timestamps, amendments, or survivorship in the static stock universe, so those limitations remain explicit.
