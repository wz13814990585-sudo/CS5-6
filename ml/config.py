"""Central configuration for factor research and XGBRanker experiments."""

from __future__ import annotations

from pathlib import Path

TARGET_COLUMN = "target_next_week_oc_return"
TARGET_OBSERVATION_DATE = "target_observation_date"

DEVELOPMENT_START = "2016-01-01"
DEVELOPMENT_END = "2021-12-31"
VALIDATION_START = "2022-01-01"
VALIDATION_END = "2023-12-31"
FINAL_TEST_START = "2024-01-01"
FINAL_TEST_END = "2026-12-31"

TRAIN_YEARS = 3
VALIDATION_WEEKS = 13
REFIT_FREQUENCY = "monthly"
PREDICTION_FREQUENCY = "weekly"
MIN_STOCKS = 30
MIN_COVERAGE_RATIO = 0.50
N_RELEVANCE_BINS = 10
RANDOM_STATE = 5703
REDUNDANCY_LIMIT = 0.75
MAX_FORWARD_FACTORS = 15
MIN_RANK_IC_IMPROVEMENT = 0.001

DATA_FILE = Path("factor_analysis/test_data_weekly.csv")
FACTOR_OUTPUT_DIR = Path("outputs/factor_analysis")
XGB_OUTPUT_DIR = Path("outputs/xgb_ranker")

FACTOR_FAMILIES = {
    "return_momentum": ["ret_1d", "ret_5d", "ret_20d", "ret_60d", "ret_120d", "momentum_20_5"],
    "gap_intraday": ["overnight_gap", "intraday_return"],
    "trend": ["ema20_distance", "ema60_distance", "ema20_60_spread", "rsi14_centered", "macd_hist_atr", "breakout_position_60", "trend_r2_20"],
    "volatility": ["realized_vol_5", "realized_vol_20", "vol_ratio_5_20", "parkinson_vol_20", "overnight_vol_20", "downside_vol_20"],
    "volume_liquidity": ["volume_zscore_20", "volume_trend_5_20", "amihud_illiq_20", "signed_volume_pressure_20", "volume_cv_20", "return_volume_corr_20"],
    "candle_location": ["close_location_value", "body_range_ratio", "gap_followthrough_20"],
    "cross_sectional_rank": ["cs_rank_ret20", "cs_rank_ret60", "cs_rank_vol20", "cs_rank_amihud20"],
    "persistence": ["return_autocorr_20"],
    "fundamental": ["revenue_growth_yoy", "gross_margin_change_yoy", "operating_profitability", "cashflow_to_assets", "debt_to_assets", "asset_growth_yoy"],
}
MACRO_FACTORS = ["macro_vix_level", "macro_vix_change_5obs", "macro_yield_spread_10y_2y", "macro_dgs10_change_5obs"]
DUPLICATE_REPRESENTATIONS = {
    "cs_rank_ret20": "ret_20d", "cs_rank_ret60": "ret_60d",
    "cs_rank_vol20": "realized_vol_20", "cs_rank_amihud20": "amihud_illiq_20",
}
RAW_MARKET_COLUMNS = {"open", "high", "low", "close", "adj_close", "volume", "daily_return"}
METADATA_COLUMNS = {"date", "ticker", "week_id", "source_row", TARGET_OBSERVATION_DATE}
FORBIDDEN_FEATURE_COLUMNS = RAW_MARKET_COLUMNS | METADATA_COLUMNS | set(MACRO_FACTORS) | {
    TARGET_COLUMN, "fwd_1w_close_to_close", "fwd_4w_close_to_close", "fwd_12w_close_to_close",
    "adj_open_calc", "relevance_label", "ranking_score", "actual_return",
}

XGB_RANKER_PARAM_CANDIDATES = [
    {"max_depth": 2, "learning_rate": 0.05, "n_estimators": 200, "min_child_weight": 5,
     "subsample": 0.85, "colsample_bytree": 0.85, "reg_alpha": 0.1, "reg_lambda": 5.0, "gamma": 0.0},
    {"max_depth": 3, "learning_rate": 0.03, "n_estimators": 400, "min_child_weight": 5,
     "subsample": 0.85, "colsample_bytree": 1.0, "reg_alpha": 0.0, "reg_lambda": 5.0, "gamma": 0.1},
    {"max_depth": 5, "learning_rate": 0.03, "n_estimators": 400, "min_child_weight": 10,
     "subsample": 0.7, "colsample_bytree": 0.85, "reg_alpha": 1.0, "reg_lambda": 10.0, "gamma": 0.1},
]


def stock_factors() -> list[str]:
    return [f for values in FACTOR_FAMILIES.values() for f in values]


def factor_family(factor: str) -> str:
    return next((family for family, values in FACTOR_FAMILIES.items() if factor in values), "unknown")
