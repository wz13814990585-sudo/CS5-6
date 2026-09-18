"""计算项目定义的 45 个周频候选因子。

输入包含预热期的 data/clean_prices.csv；输出仅保留 2016--2025 十年建模期。
所有逐股票滚动计算均只使用当日和过去数据，截面因子只在同一交易日的
100 只股票之间计算。
"""

import gzip
import time
import zipfile
import argparse
from io import BytesIO, StringIO
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from collect_sec_fundamentals import FUNDAMENTAL_DEFINITIONS, collect_financial_factors, require_user_agent


DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "clean_basic_data.csv"
WEEKLY_OUTPUT_FILE = DATA_DIR / "test_data_weekly.csv"
DEFINITIONS_FILE = DATA_DIR / "factor_definitions.csv"
MODEL_START = pd.Timestamp("2015-09-01")
MODEL_END = pd.Timestamp("2026-09-01")
EPSILON = 1e-12
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10,DGS2,VIXCLS"
MAX_FRED_ATTEMPTS = 3

FACTOR_DEFINITIONS = [
    ("ret_1d", "ln(C(t) / C(t-1))"),
    ("ret_5d", "ln(C(t) / C(t-5))"),
    ("ret_20d", "ln(C(t) / C(t-20))"),
    ("ret_60d", "ln(C(t) / C(t-60))"),
    ("ret_120d", "ln(C(t) / C(t-120))"),
    ("momentum_20_5", "ln(C(t-5) / C(t-20))"),
    ("overnight_gap", "ln(O(t) / C(t-1))"),
    ("intraday_return", "ln(C(t) / O(t))"),
    ("ema20_distance", "C / EMA20 - 1"),
    ("ema60_distance", "C / EMA60 - 1"),
    ("ema20_60_spread", "EMA20 / EMA60 - 1"),
    ("rsi14_centered", "(RSI14 - 50) / 50"),
    ("macd_hist_atr", "MACD histogram / ATR14"),
    ("breakout_position_60", "(C - Low60) / (High60 - Low60)"),
    ("realized_vol_5", "std_5(ret_1d)"),
    ("realized_vol_20", "std_20(ret_1d)"),
    ("vol_ratio_5_20", "realized_vol_5 / realized_vol_20"),
    ("parkinson_vol_20", "sqrt(mean_20(ln(H/L)^2) / (4 ln(2)))"),
    ("overnight_vol_20", "std_20(overnight_gap)"),
    ("downside_vol_20", "sqrt(mean_20(min(ret_1d, 0)^2))"),
    ("volume_zscore_20", "(ln(V) - mean_20(ln(V))) / std_20(ln(V))"),
    ("volume_trend_5_20", "mean_5(V) / mean_20(V) - 1"),
    ("amihud_illiq_20", "mean_20(abs(ret_1d) / (raw Close * Volume))"),
    ("signed_volume_pressure_20", "sum_20(sign(ret_1d) * V) / sum_20(V)"),
    ("close_location_value", "(2C - H - L) / (H - L)"),
    ("body_range_ratio", "(C - O) / (H - L)"),
    ("cs_rank_ret20", "same-date percentile rank of ret_20d"),
    ("cs_rank_ret60", "same-date percentile rank of ret_60d"),
    ("cs_rank_vol20", "same-date percentile rank of realized_vol_20"),
    ("cs_rank_amihud20", "same-date percentile rank of amihud_illiq_20"),
]

INTERNAL_FACTORS = [
    "trend_r2_20", "return_autocorr_20", "volume_cv_20", "return_volume_corr_20", "gap_followthrough_20",
]
FINANCIAL_FACTORS = [name for name, _ in FUNDAMENTAL_DEFINITIONS]
MACRO_FACTORS = [
    "macro_vix_level", "macro_vix_change_5obs", "macro_yield_spread_10y_2y", "macro_dgs10_change_5obs",
]
ADDITIONAL_FACTOR_DEFINITIONS = [
    ("trend_r2_20", "OLS R² of adjusted close over the last 20 trading sessions"),
    ("return_autocorr_20", "corr(ret[t-19:t], ret[t-20:t-1])"),
    ("volume_cv_20", "std_20(volume, ddof=1) / mean_20(volume)"),
    ("return_volume_corr_20", "corr(simple return, log volume change) over 20 sessions"),
    ("gap_followthrough_20", "corr(overnight gap, intraday return) over 20 sessions"),
    *FUNDAMENTAL_DEFINITIONS,
    ("macro_vix_level", "Latest available FRED VIXCLS level"),
    ("macro_vix_change_5obs", "VIXCLS less its value five valid observations earlier"),
    ("macro_yield_spread_10y_2y", "(DGS10 - DGS2) / 100 on the same observation date"),
    ("macro_dgs10_change_5obs", "(DGS10 - DGS10 five valid observations earlier) / 100"),
]
NEW_FACTORS = INTERNAL_FACTORS + FINANCIAL_FACTORS + MACRO_FACTORS


def adjusted_ohlc(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """将 Yahoo 的未复权 OHLC 转成与 Adj Close 一致的价格尺度。"""
    adjustment = frame["adj_close"] / frame["close"]
    return (
        frame["open"] * adjustment,
        frame["high"] * adjustment,
        frame["low"] * adjustment,
        frame["adj_close"],
    )


def calculate_one_ticker(frame: pd.DataFrame) -> pd.DataFrame:
    """在单只股票的有序日频记录上计算前 26 个时序因子。"""
    result = pd.DataFrame(index=frame.index)
    open_price, high_price, low_price, close_price = adjusted_ohlc(frame)
    raw_close = frame["close"]
    volume = frame["volume"].astype(float)
    log_close = np.log(close_price)

    result["ret_1d"] = log_close.diff()
    for window in (5, 20, 60, 120):
        result[f"ret_{window}d"] = log_close - log_close.shift(window)
    result["momentum_20_5"] = log_close.shift(5) - log_close.shift(20)
    result["overnight_gap"] = np.log(open_price / close_price.shift(1))
    result["intraday_return"] = np.log(close_price / open_price)

    ema20 = close_price.ewm(span=20, adjust=False, min_periods=20).mean()
    ema60 = close_price.ewm(span=60, adjust=False, min_periods=60).mean()
    result["ema20_distance"] = close_price / ema20 - 1
    result["ema60_distance"] = close_price / ema60 - 1
    result["ema20_60_spread"] = ema20 / ema60 - 1

    price_change = close_price.diff()
    average_gain = price_change.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    average_loss = (-price_change.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    relative_strength = average_gain / (average_loss + EPSILON)
    result["rsi14_centered"] = ((100 - 100 / (1 + relative_strength)) - 50) / 50

    macd_line = close_price.ewm(span=12, adjust=False, min_periods=26).mean() - close_price.ewm(
        span=26, adjust=False, min_periods=26
    ).mean()
    macd_histogram = macd_line - macd_line.ewm(span=9, adjust=False, min_periods=9).mean()
    true_range = pd.concat(
        [high_price - low_price, (high_price - close_price.shift(1)).abs(), (low_price - close_price.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    atr14 = true_range.rolling(14, min_periods=14).mean()
    result["macd_hist_atr"] = macd_histogram / (atr14 + EPSILON)

    high60 = high_price.rolling(60, min_periods=60).max()
    low60 = low_price.rolling(60, min_periods=60).min()
    result["breakout_position_60"] = (close_price - low60) / (high60 - low60 + EPSILON)

    result["realized_vol_5"] = result["ret_1d"].rolling(5, min_periods=5).std()
    result["realized_vol_20"] = result["ret_1d"].rolling(20, min_periods=20).std()
    result["vol_ratio_5_20"] = result["realized_vol_5"] / (result["realized_vol_20"] + EPSILON)
    result["parkinson_vol_20"] = np.sqrt(
        np.log(high_price / low_price).pow(2).rolling(20, min_periods=20).mean() / (4 * np.log(2))
    )
    result["overnight_vol_20"] = result["overnight_gap"].rolling(20, min_periods=20).std()
    result["downside_vol_20"] = np.sqrt(result["ret_1d"].clip(upper=0).pow(2).rolling(20, min_periods=20).mean())

    log_volume = np.log(volume.where(volume > 0))
    log_volume_mean = log_volume.rolling(20, min_periods=20).mean()
    log_volume_std = log_volume.rolling(20, min_periods=20).std()
    result["volume_zscore_20"] = (log_volume - log_volume_mean) / (log_volume_std + EPSILON)
    result["volume_trend_5_20"] = volume.rolling(5, min_periods=5).mean() / volume.rolling(20, min_periods=20).mean() - 1
    result["amihud_illiq_20"] = (result["ret_1d"].abs() / (raw_close * volume)).rolling(20, min_periods=20).mean()
    result["signed_volume_pressure_20"] = (
        np.sign(result["ret_1d"]) * volume
    ).rolling(20, min_periods=20).sum() / (volume.rolling(20, min_periods=20).sum() + EPSILON)
    result["close_location_value"] = (2 * close_price - high_price - low_price) / (high_price - low_price + EPSILON)
    result["body_range_ratio"] = (close_price - open_price) / (high_price - low_price + EPSILON)
    return result


def keep_last_trading_day_of_week(data: pd.DataFrame) -> pd.DataFrame:
    """Keep rows only on the shared final market session of each W-FRI week.

    A ticker missing on the common decision date is excluded; it never falls
    back to an earlier ticker-specific session. A terminal Mon-Wed partial week
    is also excluded because its final market session is not yet known.
    """
    weekly = data.sort_values(["ticker", "date"]).copy()
    weekly["_trading_week"] = weekly["date"].dt.to_period("W-FRI")
    market = (weekly[["date", "_trading_week"]].drop_duplicates()
              .groupby("_trading_week", as_index=False)["date"].max()
              .rename(columns={"date": "_decision_date"}).sort_values("_trading_week"))
    if len(market):
        last = market.iloc[-1]
        if last._decision_date < last._trading_week.end_time.normalize() and last._decision_date.weekday() <= 2:
            market = market.iloc[:-1]
    weekly = weekly.merge(market, on="_trading_week", how="inner", validate="many_to_one")
    weekly = weekly.loc[weekly["date"] == weekly["_decision_date"]].copy()
    weekly["market_week_id"] = pd.Categorical(
        weekly["_trading_week"], categories=market["_trading_week"], ordered=True).codes
    return weekly.drop(columns=["_trading_week", "_decision_date"]).sort_values(
        ["ticker", "date"]).reset_index(drop=True)


def calculate_internal_one_ticker(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate five additional internal factors on consecutive daily sessions."""
    open_price = frame["open"] * (frame["adj_close"] / frame["close"])
    close_price = frame["adj_close"]
    volume = frame["volume"].astype(float)
    result = pd.DataFrame(index=frame.index)
    returns = close_price.pct_change()
    session_complete = lambda window: frame["session_id"].sub(frame["session_id"].shift(window - 1)).eq(window - 1)

    x = np.arange(20, dtype=float)
    sum_y = close_price.rolling(20, min_periods=20).sum()
    sst = close_price.pow(2).rolling(20, min_periods=20).sum() - sum_y.pow(2) / 20
    sum_xy = close_price.rolling(20, min_periods=20).apply(lambda values: float(np.dot(x, values)), raw=True)
    trend_r2 = (sum_xy - x.mean() * sum_y).pow(2) / (float(((x - x.mean()) ** 2).sum()) * sst)
    result["trend_r2_20"] = trend_r2.where(session_complete(20) & (sst > EPSILON)).clip(0, 1)
    result["return_autocorr_20"] = returns.rolling(20, min_periods=20).corr(returns.shift(1)).where(session_complete(22))

    volume_mean = volume.rolling(20, min_periods=20).mean()
    result["volume_cv_20"] = (volume.rolling(20, min_periods=20).std(ddof=1) / volume_mean).where(
        session_complete(20) & (volume_mean > 0)
    )
    volume_change = np.log(volume.where(volume > 0)).diff()
    result["return_volume_corr_20"] = returns.rolling(20, min_periods=20).corr(volume_change).where(session_complete(21))
    gap = open_price / close_price.shift(1) - 1
    intraday = close_price / open_price - 1
    result["gap_followthrough_20"] = gap.rolling(20, min_periods=20).corr(intraday).where(session_complete(21))
    for name in ("return_autocorr_20", "return_volume_corr_20", "gap_followthrough_20"):
        result[name] = result[name].clip(-1, 1)
    return result


def internal_factors(weekly: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily internal signals and select exactly the weekly output keys."""
    calendar = pd.DatetimeIndex(prices["date"].drop_duplicates().sort_values())
    daily = prices.sort_values(["ticker", "date"]).copy()
    daily["session_id"] = calendar.get_indexer(pd.DatetimeIndex(daily["date"]))
    values = daily.groupby("ticker", group_keys=False, sort=False).apply(calculate_internal_one_ticker, include_groups=False)
    calculated = pd.concat([daily[["date", "ticker"]], values.reindex(daily.index)], axis=1)
    return weekly[["date", "ticker"]].merge(calculated, on=["date", "ticker"], how="left", validate="one_to_one")


def next_market_day(dates: pd.Series, market_dates: pd.Series) -> pd.Series:
    """Use the next observed trading day as a conservative public-data proxy."""
    calendar = pd.DatetimeIndex(pd.to_datetime(market_dates).dropna().unique()).sort_values()
    positions = calendar.searchsorted(pd.DatetimeIndex(pd.to_datetime(dates)), side="right")
    return pd.Series([calendar[p] if p < len(calendar) else pd.NaT for p in positions], index=dates.index)


def fetch_fred() -> pd.DataFrame:
    """Fetch DGS10, DGS2 and VIXCLS, accepting FRED's zipped graph response."""
    last_error: Exception | None = None
    request = Request(FRED_URL, headers={"User-Agent": "SafeCapitalCoursework/1.0", "Accept-Encoding": "identity"})
    for attempt in range(MAX_FRED_ATTEMPTS):
        try:
            with urlopen(request, timeout=30) as response:
                payload = response.read()
                if "zip" in response.headers.get("Content-Type", "").lower() or payload.startswith(b"PK\\x03\\x04"):
                    with zipfile.ZipFile(BytesIO(payload)) as archive:
                        tables = [pd.read_csv(archive.open(name)) for name in archive.namelist() if name.lower().endswith(".csv")]
                    raw = tables[0]
                    for table in tables[1:]:
                        raw = raw.merge(table, on="observation_date", how="outer")
                    break
                if response.headers.get("Content-Encoding", "").lower() == "gzip":
                    payload = gzip.decompress(payload)
                raw = pd.read_csv(StringIO(payload.decode("utf-8")))
                raw = raw.rename(columns={raw.columns[0]: "observation_date"})
                break
        except Exception as error:
            last_error = error
            if attempt + 1 == MAX_FRED_ATTEMPTS:
                raise RuntimeError(f"FRED request failed after {MAX_FRED_ATTEMPTS} attempts: {last_error}") from error
            time.sleep(1.5 * (attempt + 1))
    raw["observation_date"] = pd.to_datetime(raw["observation_date"], errors="coerce")
    for name in ("DGS10", "DGS2", "VIXCLS"):
        raw[name] = pd.to_numeric(raw[name], errors="coerce")
    return raw.dropna(subset=["observation_date"]).sort_values("observation_date")


def macro_factors(weekly: pd.DataFrame, market_dates: pd.Series) -> pd.DataFrame:
    """Calculate four FRED factors and align them with the weekly dates."""
    raw = fetch_fred()
    vix = raw.loc[raw["VIXCLS"].notna(), ["observation_date", "VIXCLS"]].copy()
    vix["macro_vix_level"] = vix["VIXCLS"]
    vix["macro_vix_change_5obs"] = vix["VIXCLS"].diff(5)
    vix["available_at"] = next_market_day(vix["observation_date"], market_dates)
    yields = raw.loc[raw["DGS10"].notna(), ["observation_date", "DGS10", "DGS2"]].copy()
    yields["macro_yield_spread_10y_2y"] = ((yields["DGS10"] - yields["DGS2"]) / 100).where(yields["DGS2"].notna())
    yields["macro_dgs10_change_5obs"] = yields["DGS10"].diff(5) / 100
    yields["available_at"] = next_market_day(yields["observation_date"], market_dates)
    output = pd.DataFrame({"date": pd.to_datetime(sorted(weekly["date"].unique()))})
    for events, name in ((vix, "macro_vix_level"), (vix, "macro_vix_change_5obs"), (yields, "macro_yield_spread_10y_2y"), (yields, "macro_dgs10_change_5obs")):
        output[name] = pd.merge_asof(
            output[["date"]], events[["available_at", name]].dropna(subset=["available_at"]).sort_values("available_at"),
            left_on="date", right_on="available_at", direction="backward",
        )[name]
    return output


def write_factor_definitions() -> None:
    """Write all 45 candidate-factor definitions without refreshing market data."""
    DATA_DIR.mkdir(exist_ok=True)
    definitions = pd.DataFrame(
        FACTOR_DEFINITIONS + ADDITIONAL_FACTOR_DEFINITIONS,
        columns=["factor", "calculation"],
    )
    if definitions["factor"].duplicated().any() or len(definitions) != 45:
        raise RuntimeError("The factor definition must exactly contain 45 non-repetitive names.")
    definitions.to_csv(DEFINITIONS_FILE, index=False, encoding="utf-8-sig")


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} cannot be found. Please run fetch_and_clean.py first。")
    prices = pd.read_csv(INPUT_FILE, parse_dates=["date"])
    required = {"date", "ticker", "open", "high", "low", "close", "adj_close", "volume"}
    if missing := required - set(prices.columns):
        raise ValueError(f"Missing fields in the input data: {sorted(missing)}")

    prices = prices.sort_values(["ticker", "date"]).reset_index(drop=True)
    time_series_names = [name for name, _ in FACTOR_DEFINITIONS[:26]]
    factors = (
        prices.groupby("ticker", group_keys=False, sort=False)
        .apply(calculate_one_ticker, include_groups=False)
        [time_series_names]
        .reindex(prices.index)
    )
    dataset = pd.concat([prices, factors], axis=1)

    # 仅在同一日期、具备有效数值的股票中计算截面百分位排名。
    dataset["cs_rank_ret20"] = dataset.groupby("date")["ret_20d"].rank(pct=True, method="average")
    dataset["cs_rank_ret60"] = dataset.groupby("date")["ret_60d"].rank(pct=True, method="average")
    dataset["cs_rank_vol20"] = dataset.groupby("date")["realized_vol_20"].rank(pct=True, method="average")
    dataset["cs_rank_amihud20"] = dataset.groupby("date")["amihud_illiq_20"].rank(pct=True, method="average")

    # 预热期只服务于计算，不进入十年建模样本。
    dataset = dataset.loc[dataset["date"].between(MODEL_START, MODEL_END)].reset_index(drop=True)
    weekly_dataset = keep_last_trading_day_of_week(dataset)
    print("Calculate five newly added internal factors...")
    internal = internal_factors(weekly_dataset, prices)
    print("Download FRED's macro data and calculate four macro factors...")
    macro = macro_factors(weekly_dataset, prices["date"])
    print("Download the SEC financial data and calculate six financial factors...")
    require_user_agent()
    financial, sec_log = collect_financial_factors(weekly_dataset, prices["date"])

    final = weekly_dataset.merge(internal, on=["date", "ticker"], how="left", validate="one_to_one")
    final = final.merge(financial, on=["date", "ticker"], how="left", validate="one_to_one")
    final = final.merge(macro, on="date", how="left", validate="many_to_one")
    if len(final) != len(weekly_dataset) or final.duplicated(["date", "ticker"]).any():
        raise RuntimeError("The new factor merge has changed the original date+ticker key. Not written to the output file.")
    values = final[NEW_FACTORS].to_numpy(dtype=float, na_value=np.nan)
    if not np.isfinite(values[~np.isnan(values)]).all():
        raise RuntimeError("Infinite values appear in the newly added factors; Not written to the output file.")

    DATA_DIR.mkdir(exist_ok=True)
    final.to_csv(WEEKLY_OUTPUT_FILE, index=False, encoding="utf-8-sig")
    write_factor_definitions()

    factor_names = [name for name, _ in FACTOR_DEFINITIONS] + NEW_FACTORS
    complete = final.dropna(subset=factor_names)
    print(f"The frequency training data has been saved：{WEEKLY_OUTPUT_FILE}")
    print(f"line number: {len(final)}; The complete number of 45-factor rows: {len(complete)}")
    print("The number of valid records of the newly added factor: ")
    print(final[NEW_FACTORS].notna().sum().to_string())
    print(f"SEC succeed: {(sec_log['status'] == 'success').sum()}/{weekly_dataset['ticker'].nunique()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the weekly 45-factor candidate panel.")
    parser.add_argument("--definitions-only", action="store_true", help="Only refresh technical_factor_definitions.csv.")
    arguments = parser.parse_args()
    if arguments.definitions_only:
        write_factor_definitions()
        print(f"Forty-five factor definitions have been saved: {DEFINITIONS_FILE}")
    else:
        main()
