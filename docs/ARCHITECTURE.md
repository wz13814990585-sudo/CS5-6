# Research pipeline architecture

The source weekly panel is read by `ml.data`. Before assigning the shared market-week index, a terminal Monday–Wednesday snapshot is conservatively removed because it cannot represent a completed W-FRI trading week; terminal Thursdays are retained for Friday-market-holiday cases. The primary label is `log(next adjusted close / next adjusted open)`. A ticker must have a row at exactly `week_id + 1`; otherwise the label is missing. Adjusted open is `open * adj_close / close`. Close-to-close labels remain diagnostics only.

`factor_analysis.build_weekly_factor_analysis` performs date-local Rank IC, quintile, stability, coverage, and redundancy analysis on the development period only (2016–2021). The VIX regime median and all factor directions are also learned only there. Cross-sectional rank copies are analyzed but excluded from the default admissible pool. The resulting JSON is the only factor-set contract consumed by ML.

`ml.run_xgb_ranker_experiments` tunes only against chronological validation (2022–2023), freezes each configuration, then runs a three-year rolling window with monthly refits and weekly predictions on the locked 2024–2026 test. A training label is admitted only when its `target_observation_date` is no later than the refit date. Scores are called ranking scores, never predicted returns.

The SEC collector uses the latest filing date needed by a derived factor, then delays availability to the next observed market day before an as-of backward merge. This is a conservative filing-availability rule. It does not model intraday SEC acceptance timestamps, amendments, or survivorship in the static stock universe, so those limitations remain explicit.
