

from __future__ import annotations

import argparse
import math
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy.stats import rankdata, spearmanr


MIN_STOCKS = 30
REDUNDANCY_LIMIT = 0.75

FACTOR_FAMILIES = OrderedDict(
    {
        "Return / momentum": [
            "ret_1d", "ret_5d", "ret_20d", "ret_60d", "ret_120d",
            "momentum_20_5",
        ],
        "Gap / intraday": ["overnight_gap", "intraday_return"],
        "Trend": [
            "ema20_distance", "ema60_distance", "ema20_60_spread",
            "rsi14_centered", "macd_hist_atr", "breakout_position_60",
            "trend_r2_20",
        ],
        "Volatility": [
            "realized_vol_5", "realized_vol_20", "vol_ratio_5_20",
            "parkinson_vol_20", "overnight_vol_20", "downside_vol_20",
        ],
        "Volume / liquidity": [
            "volume_zscore_20", "volume_trend_5_20", "amihud_illiq_20",
            "signed_volume_pressure_20", "volume_cv_20",
            "return_volume_corr_20",
        ],
        "Candle / location": [
            "close_location_value", "body_range_ratio", "gap_followthrough_20",
        ],
        "Cross-sectional rank": [
            "cs_rank_ret20", "cs_rank_ret60", "cs_rank_vol20",
            "cs_rank_amihud20",
        ],
        "Persistence": ["return_autocorr_20"],
        "Fundamental": [
            "revenue_growth_yoy", "gross_margin_change_yoy",
            "operating_profitability", "cashflow_to_assets", "debt_to_assets",
            "asset_growth_yoy",
        ],
    }
)

MACRO_FACTORS = [
    "macro_vix_level",
    "macro_vix_change_5obs",
    "macro_yield_spread_10y_2y",
    "macro_dgs10_change_5obs",
]

TARGETS = {1: "fwd_1w_return", 4: "fwd_4w_return", 12: "fwd_12w_return"}


def factor_list() -> list[str]:
    return [factor for items in FACTOR_FAMILIES.values() for factor in items]


def family_of(factor: str) -> str:
    for family, items in FACTOR_FAMILIES.items():
        if factor in items:
            return family
    raise KeyError(f"No family configured for factor: {factor}")


def clean_number(value):
    if value is None:
        return np.nan
    try:
        number = float(value)
    except (TypeError, ValueError):
        return np.nan
    return number if np.isfinite(number) else np.nan


def read_weekly_data(path: Path) -> pd.DataFrame:
    """Read the original CSV; XLSX/Weekly Data remains an optional fallback."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        # utf-8-sig removes the BOM present in the supplied original CSV.
        df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    elif suffix in {".xlsx", ".xlsm"}:
        wb = load_workbook(path, read_only=True, data_only=True, keep_links=False)
        if "Weekly Data" not in wb.sheetnames:
            raise ValueError("The input workbook does not contain a 'Weekly Data' sheet.")
        ws = wb["Weekly Data"]
        rows = ws.iter_rows(values_only=True)
        headers = list(next(rows))
        records = [row[: len(headers)] for row in rows]
        wb.close()
        df = pd.DataFrame.from_records(records, columns=headers)
        df = df.loc[:, ~df.columns.duplicated()].copy()
    else:
        raise ValueError("Input must be the original .csv file or an .xlsx workbook.")

    # The original CSV has 54 source columns. These four columns are created here.
    for column in ["adj_open_calc", *TARGETS.values()]:
        if column not in df.columns:
            df[column] = np.nan

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["ticker"] = df["ticker"].astype("string")
    df = df.dropna(subset=["date", "ticker"]).copy()
    if df.duplicated(["date", "ticker"]).any():
        examples = df.loc[df.duplicated(["date", "ticker"], keep=False), ["date", "ticker"]].head()
        raise ValueError(f"Duplicate date/ticker rows found:\n{examples}")

    numeric_columns = [c for c in df.columns if c not in {"date", "ticker"}]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)
    return df


def calculate_forward_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Use the shared market-week index; missing exact target weeks stay blank."""
    out = df.copy()
    weeks = pd.Index(sorted(out["date"].dropna().unique()), name="date")
    week_lookup = pd.Series(np.arange(len(weeks), dtype=int), index=weeks)
    out["week_id"] = out["date"].map(week_lookup).astype(int)
    out["source_row"] = np.arange(len(out), dtype=int)

    keyed = out.set_index(["ticker", "week_id"])
    close_by_key = keyed["adj_close"]
    row_by_key = keyed["source_row"]

    for horizon, target in TARGETS.items():
        future_keys = pd.MultiIndex.from_arrays(
            [out["ticker"].array, (out["week_id"] + horizon).array],
            names=["ticker", "week_id"],
        )
        future_close = close_by_key.reindex(future_keys).to_numpy(dtype=float)
        future_row = row_by_key.reindex(future_keys).to_numpy(dtype=float)
        current_close = out["adj_close"].to_numpy(dtype=float)
        valid = (
            np.isfinite(current_close) & np.isfinite(future_close)
            & (current_close > 0) & (future_close > 0)
        )
        values = np.full(len(out), np.nan)
        values[valid] = np.log(future_close[valid] / current_close[valid])
        out[target] = values
        out[f"_{target}_row"] = future_row

    close = out["close"].to_numpy(dtype=float)
    adjusted_close = out["adj_close"].to_numpy(dtype=float)
    open_price = out["open"].to_numpy(dtype=float)
    valid_open = np.isfinite(open_price) & np.isfinite(close) & np.isfinite(adjusted_close) & (close != 0)
    adjusted_open = np.full(len(out), np.nan)
    adjusted_open[valid_open] = open_price[valid_open] * adjusted_close[valid_open] / close[valid_open]
    out["adj_open_calc"] = adjusted_open
    return out


def pair_spearman(x: pd.Series, y: pd.Series, minimum: int = MIN_STOCKS) -> float:
    pair = pd.concat([x, y], axis=1).dropna()
    if len(pair) < minimum or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return np.nan
    result = spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
    return float(result.statistic) if np.isfinite(result.statistic) else np.nan


def fast_spearman_against_target(factor_matrix: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Pairwise Spearman correlations of many factor columns against one target."""
    output = np.full(factor_matrix.shape[1], np.nan)
    target_finite = np.isfinite(target)
    for col in range(factor_matrix.shape[1]):
        x = factor_matrix[:, col]
        valid = np.isfinite(x) & target_finite
        if valid.sum() < MIN_STOCKS:
            continue
        xv = x[valid]
        yv = target[valid]
        if np.unique(xv).size < 2 or np.unique(yv).size < 2:
            continue
        xr = rankdata(xv, method="average")
        yr = rankdata(yv, method="average")
        xr -= xr.mean()
        yr -= yr.mean()
        denominator = math.sqrt(float(np.dot(xr, xr) * np.dot(yr, yr)))
        if denominator:
            output[col] = float(np.dot(xr, yr) / denominator)
    return output


def weekly_ic_and_quintiles(
    df: pd.DataFrame, factors: list[str], weeks: pd.DatetimeIndex
) -> tuple[dict[int, pd.DataFrame], pd.DataFrame]:
    ic = {
        horizon: pd.DataFrame(index=weeks, columns=factors, dtype=float)
        for horizon in TARGETS
    }
    quintile_sum = {factor: np.zeros(5, dtype=float) for factor in factors}
    quintile_count = {factor: np.zeros(5, dtype=int) for factor in factors}

    for date, group in df.groupby("date", sort=True):
        factor_matrix = group[factors].to_numpy(dtype=float)
        for horizon, target in TARGETS.items():
            values = fast_spearman_against_target(
                factor_matrix, group[target].to_numpy(dtype=float)
            )
            ic[horizon].loc[date, factors] = values

        target_values = group[TARGETS[1]].to_numpy(dtype=float)
        for factor in factors:
            factor_values = group[factor].to_numpy(dtype=float)
            valid = np.isfinite(factor_values) & np.isfinite(target_values)
            x = factor_values[valid]
            y = target_values[valid]
            n = len(x)
            if n < MIN_STOCKS or np.unique(x).size < 5:
                continue
            ranks = pd.Series(x).rank(method="first").to_numpy(dtype=int)
            q = np.minimum(((ranks - 1) * 5 // n).astype(int), 4)
            sums = np.bincount(q, weights=y, minlength=5)
            counts = np.bincount(q, minlength=5)
            means = np.divide(sums, counts, out=np.full(5, np.nan), where=counts > 0)
            good = np.isfinite(means)
            quintile_sum[factor][good] += means[good]
            quintile_count[factor][good] += 1

    rows = []
    for factor in factors:
        qvals = np.divide(
            quintile_sum[factor], quintile_count[factor],
            out=np.full(5, np.nan), where=quintile_count[factor] > 0,
        )
        monotonicity = pair_spearman(
            pd.Series(np.arange(1, 6), dtype=float), pd.Series(qvals), minimum=3
        )
        rows.append(
            {
                "Category": family_of(factor), "Factor": factor,
                "Q1": qvals[0], "Q2": qvals[1], "Q3": qvals[2],
                "Q4": qvals[3], "Q5": qvals[4],
                "Q5-Q1": qvals[4] - qvals[0],
                "Monotonicity rho": monotonicity,
            }
        )
    return ic, pd.DataFrame(rows)


def summarize_single_factors(ic1: pd.DataFrame, quintiles: pd.DataFrame) -> pd.DataFrame:
    q = quintiles.set_index("Factor")
    rows = []
    for factor in ic1.columns:
        s = ic1[factor].dropna()
        mean_ic = s.mean() if len(s) else np.nan
        std_ic = s.std(ddof=1) if len(s) > 1 else np.nan
        rows.append(
            {
                "Category": family_of(factor), "Factor": factor,
                "Eligible Weeks": int(s.count()),
                "Mean Rank IC": mean_ic,
                "Median Rank IC": s.median() if len(s) else np.nan,
                "IC Std": std_ic,
                "Annualized ICIR": mean_ic / std_ic * math.sqrt(52)
                if np.isfinite(std_ic) and std_ic != 0 else np.nan,
                "Positive IC %": (s > 0).mean() if len(s) else np.nan,
                "Q5-Q1": q.at[factor, "Q5-Q1"],
                "Direction": "Higher factor -> higher future return"
                if mean_ic >= 0 else "Lower factor -> higher future return",
            }
        )
    return pd.DataFrame(rows)


def calculate_ic_decay(ic: dict[int, pd.DataFrame], factors: list[str]) -> pd.DataFrame:
    rows = []
    for factor in factors:
        row = {"Category": family_of(factor), "Factor": factor}
        for horizon in (1, 4, 12):
            s = ic[horizon][factor].dropna()
            mean = s.mean() if len(s) else np.nan
            std = s.std(ddof=1) if len(s) > 1 else np.nan
            row[f"{horizon}W Mean IC"] = mean
            row[f"{horizon}W ICIR"] = mean / std * math.sqrt(52) if np.isfinite(std) and std != 0 else np.nan
            row[f"{horizon}W Weeks"] = int(s.count())
        rows.append(row)
    return pd.DataFrame(rows)


def calculate_macro(df: pd.DataFrame, weeks: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for date, group in df.groupby("date", sort=True):
        valid_return = group[TARGETS[1]].dropna()
        row = {
            "Date": date,
            "Equal-weight fwd_1w": valid_return.mean() if len(valid_return) >= MIN_STOCKS else np.nan,
        }
        for macro in MACRO_FACTORS:
            values = group[macro].dropna()
            row[macro] = values.iloc[0] if len(values) else np.nan
        rows.append(row)
    weekly = pd.DataFrame(rows).set_index("Date").reindex(weeks).reset_index()

    result = []
    for macro in MACRO_FACTORS:
        pair = weekly[[macro, "Equal-weight fwd_1w"]].dropna()
        result.append(
            {
                "Macro Factor": macro,
                "Weeks": len(pair),
                "Spearman": pair_spearman(pair[macro], pair["Equal-weight fwd_1w"], minimum=20),
                "Pearson": pair[macro].corr(pair["Equal-weight fwd_1w"]) if len(pair) >= 20 else np.nan,
                "Direction": "Positive relationship"
                if pair[macro].corr(pair["Equal-weight fwd_1w"]) >= 0 else "Negative relationship",
                "Method": "Time-series correlation against the weekly equal-weight 1W forward return.",
            }
        )
    return weekly, pd.DataFrame(result)


def calculate_stability(
    ic1: pd.DataFrame, macro_weekly: pd.DataFrame, factors: list[str]
) -> tuple[pd.DataFrame, float]:
    vix = macro_weekly.set_index("Date")["macro_vix_level"].reindex(ic1.index)
    vix_median = float(vix.median())
    early = ic1.index.year <= 2020
    late = ic1.index.year >= 2021
    low = vix <= vix_median
    high = vix > vix_median
    rows = []
    for factor in factors:
        s = ic1[factor]
        early_mean = s.loc[early].mean()
        late_mean = s.loc[late].mean()
        low_mean = s.loc[low].mean()
        high_mean = s.loc[high].mean()
        rows.append(
            {
                "Category": family_of(factor), "Factor": factor,
                "Overall Mean IC": s.mean(),
                "2015-2020 Mean IC": early_mean,
                "2021-2026 Mean IC": late_mean,
                "Low VIX Mean IC": low_mean,
                "High VIX Mean IC": high_mean,
                "Early-Late Gap": abs(early_mean - late_mean),
                "Low-High VIX Gap": abs(low_mean - high_mean),
            }
        )
    return pd.DataFrame(rows), vix_median


def calculate_factor_correlation(df: pd.DataFrame, factors: list[str]) -> pd.DataFrame:
    matrices = []
    for _, group in df.groupby("date", sort=True):
        matrices.append(group[factors].corr(method="spearman", min_periods=MIN_STOCKS).to_numpy())
    with np.errstate(all="ignore"):
        median = np.nanmedian(np.stack(matrices), axis=0)
    np.fill_diagonal(median, 1.0)
    return pd.DataFrame(median, index=factors, columns=factors)


def same_nonzero_sign(a: float, b: float) -> bool:
    return np.isfinite(a) and np.isfinite(b) and a != 0 and b != 0 and np.sign(a) == np.sign(b)


def build_factor_selection(
    summary: pd.DataFrame,
    quintiles: pd.DataFrame,
    decay: pd.DataFrame,
    stability: pd.DataFrame,
    correlation: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], str | None, str | None]:
    result = summary.merge(
        quintiles[["Factor", "Monotonicity rho"]], on="Factor", how="left"
    ).merge(
        stability[
            ["Factor", "2015-2020 Mean IC", "2021-2026 Mean IC", "Low VIX Mean IC", "High VIX Mean IC"]
        ], on="Factor", how="left"
    ).merge(
        decay[["Factor", "4W Mean IC", "12W Mean IC"]], on="Factor", how="left"
    )

    max_rho = []
    for factor in result["Factor"]:
        values = correlation.loc[factor].drop(index=factor, errors="ignore").abs()
        max_rho.append(values.max())
    result["Max |rho|"] = max_rho

    def score(row) -> int:
        tests = [
            abs(row["Mean Rank IC"]) >= 0.006,
            abs(row["Annualized ICIR"]) >= 0.30,
            abs(row["Q5-Q1"]) >= 0.00035,
            abs(row["Monotonicity rho"]) >= 0.60,
            same_nonzero_sign(row["2015-2020 Mean IC"], row["2021-2026 Mean IC"]),
            same_nonzero_sign(row["Low VIX Mean IC"], row["High VIX Mean IC"]),
            max(abs(row["4W Mean IC"]), abs(row["12W Mean IC"])) >= 0.008,
        ]
        return int(sum(bool(x) for x in tests))

    result["Evidence Score"] = result.apply(score, axis=1)
    result["Evidence Flag"] = np.select(
        [result["Evidence Score"] >= 6, result["Evidence Score"] >= 4],
        ["Strong", "Moderate"], default="Weak",
    )
    result["Abs ICIR"] = result["Annualized ICIR"].abs()
    result["Abs Mean IC"] = result["Mean Rank IC"].abs()
    result["Horizon Strength"] = result[["4W Mean IC", "12W Mean IC"]].abs().max(axis=1)

    technical = result[
        ~result["Category"].isin(["Fundamental", "Cross-sectional rank"])
    ].sort_values(
        ["Evidence Score", "Abs ICIR", "Abs Mean IC"], ascending=False
    )

    core: list[str] = []
    used_families: set[str] = set()

    def compatible(candidate: str) -> bool:
        return all(abs(correlation.at[candidate, chosen]) < REDUNDANCY_LIMIT for chosen in core)

    # First pass: evidence score >=4, one representative per family.
    for _, row in technical.iterrows():
        factor = row["Factor"]
        family = row["Category"]
        if row["Evidence Score"] < 4 or family in used_families or not compatible(factor):
            continue
        core.append(factor)
        used_families.add(family)
        if len(core) == 5:
            break

    # Second pass: fill remaining slots while retaining the redundancy screen.
    if len(core) < 5:
        for factor in technical["Factor"]:
            if factor in core or not compatible(factor):
                continue
            core.append(factor)
            if len(core) == 5:
                break

    # Last-resort fill; this is deterministic and is disclosed in Selection Reason.
    if len(core) < 5:
        for factor in technical["Factor"]:
            if factor not in core:
                core.append(factor)
            if len(core) == 5:
                break

    def best_optional(candidates: pd.DataFrame, sort_columns: list[str]) -> str | None:
        ordered = candidates.sort_values(sort_columns, ascending=False)
        for factor in ordered["Factor"]:
            if factor in core:
                continue
            if all(abs(correlation.at[factor, c]) < REDUNDANCY_LIMIT for c in core):
                return factor
        return ordered["Factor"].iloc[0] if len(ordered) else None

    fundamental_optional = best_optional(
        result[result["Category"] == "Fundamental"],
        ["Evidence Score", "Abs ICIR", "Abs Mean IC"],
    )
    horizon_pool = result[
        (~result["Category"].isin(["Fundamental", "Cross-sectional rank"]))
        & (~result["Factor"].isin(core))
    ]
    horizon_optional = best_optional(
        horizon_pool, ["Horizon Strength", "Evidence Score", "Abs ICIR"]
    )

    roles = {}
    for factor in core:
        roles[factor] = "Core"
    if fundamental_optional:
        roles[fundamental_optional] = "Optional fundamental"
    if horizon_optional and horizon_optional not in roles:
        roles[horizon_optional] = "Optional horizon"

    def reason(row) -> str:
        factor = row["Factor"]
        if factor in core:
            return (
                f"Selected as the {row['Category']} representative; ranked on evidence score, "
                f"|ICIR| and |Mean IC| with a {REDUNDANCY_LIMIT:.2f} pairwise-correlation screen."
            )
        if factor == fundamental_optional:
            return "Best fundamental extension after the same evidence and redundancy review."
        if factor == horizon_optional:
            return "Best excluded technical extension by 4W/12W IC strength after redundancy review."
        if row["Category"] == "Cross-sectional rank":
            return "Excluded because it duplicates the ordering of an underlying raw factor."
        return "Not selected for the compact set after evidence, stability, horizon and redundancy review."

    result["Final Role"] = result["Factor"].map(roles).fillna("Exclude")
    result["Use in Multi-Factor?"] = np.where(result["Final Role"] == "Exclude", "No", "Yes")
    result["Selection Reason"] = result.apply(reason, axis=1)
    result["Direction Sign"] = np.where(result["Mean Rank IC"] >= 0, 1, -1)
    result["Direction"] = np.where(
        result["Direction Sign"] > 0,
        "Higher factor -> higher expected return",
        "Lower factor -> higher expected return",
    )

    columns = [
        "Category", "Factor", "Direction", "Mean Rank IC", "Annualized ICIR",
        "Positive IC %", "Q5-Q1", "Monotonicity rho", "2015-2020 Mean IC",
        "2021-2026 Mean IC", "Low VIX Mean IC", "High VIX Mean IC",
        "4W Mean IC", "12W Mean IC", "Max |rho|", "Evidence Score",
        "Evidence Flag", "Final Role", "Use in Multi-Factor?", "Selection Reason",
        "Direction Sign",
    ]
    return result[columns], core, fundamental_optional, horizon_optional


def calculate_multifactor(
    df: pd.DataFrame,
    selection: pd.DataFrame,
    core: list[str],
    fundamental_optional: str | None,
    horizon_optional: str | None,
    weeks: pd.DatetimeIndex,
) -> tuple[pd.DataFrame, pd.DataFrame, OrderedDict[str, list[str]]]:
    variants: OrderedDict[str, list[str]] = OrderedDict()
    variants["Core 5"] = core
    if fundamental_optional:
        variants["Core 5 + Fundamental"] = core + [fundamental_optional]
    if horizon_optional:
        variants["Core 5 + Horizon"] = core + [horizon_optional]
    extended = core + [x for x in [fundamental_optional, horizon_optional] if x and x not in core]
    if len(extended) > len(core):
        variants[f"Extended {len(extended)}"] = extended

    direction = selection.set_index("Factor")["Direction Sign"].to_dict()
    audit_rows = []
    for date, group in df.groupby("date", sort=True):
        row = {"Date": date}
        for name, factors in variants.items():
            base = group[[*factors, *TARGETS.values()]].copy()
            complete = base[factors].dropna()
            n = len(complete)
            row[f"{name} N"] = n
            if n < MIN_STOCKS:
                for horizon in TARGETS:
                    row[f"{name} {horizon}W IC"] = np.nan
                row[f"{name} 1W Q5-Q1"] = np.nan
                continue

            ranks = complete[factors].rank(method="average", pct=True)
            for factor in factors:
                if direction[factor] < 0:
                    ranks[factor] = 1.0 - ranks[factor] + 1.0 / n
            composite = ranks.mean(axis=1)

            for horizon, target in TARGETS.items():
                row[f"{name} {horizon}W IC"] = pair_spearman(
                    composite, group.loc[composite.index, target]
                )

            pair = pd.concat([composite.rename("score"), group.loc[composite.index, TARGETS[1]]], axis=1).dropna()
            if len(pair) >= MIN_STOCKS and pair["score"].nunique() >= 5:
                pair["quintile"] = pd.qcut(pair["score"].rank(method="first"), 5, labels=False) + 1
                means = pair.groupby("quintile", observed=True)[TARGETS[1]].mean()
                row[f"{name} 1W Q5-Q1"] = means.get(5, np.nan) - means.get(1, np.nan)
            else:
                row[f"{name} 1W Q5-Q1"] = np.nan
        audit_rows.append(row)

    audit = pd.DataFrame(audit_rows).set_index("Date").reindex(weeks).reset_index()
    summary_rows = []
    for name, factors in variants.items():
        row = {
            "Combination": name,
            "Included Factors": " ".join(
                ("+" if direction[f] > 0 else "-") + f for f in factors
            ),
            "Avg Stocks/Week": audit[f"{name} N"].replace(0, np.nan).mean(),
            "1W Q5-Q1": audit[f"{name} 1W Q5-Q1"].mean(),
        }
        for horizon in TARGETS:
            s = audit[f"{name} {horizon}W IC"].dropna()
            mean = s.mean() if len(s) else np.nan
            std = s.std(ddof=1) if len(s) > 1 else np.nan
            row[f"{horizon}W Mean IC"] = mean
            row[f"{horizon}W ICIR"] = mean / std * math.sqrt(52) if np.isfinite(std) and std != 0 else np.nan
            row[f"{horizon}W Positive %"] = (s > 0).mean() if len(s) else np.nan
        summary_rows.append(row)
    return pd.DataFrame(summary_rows), audit, variants


def excel_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, np.generic):
        return value.item()
    return value


def build_workbook(
    output_path: Path,
    df: pd.DataFrame,
    ic: dict[int, pd.DataFrame],
    quintiles: pd.DataFrame,
    summary: pd.DataFrame,
    decay: pd.DataFrame,
    macro_weekly: pd.DataFrame,
    macro_results: pd.DataFrame,
    stability: pd.DataFrame,
    vix_median: float,
    correlation: pd.DataFrame,
    selection: pd.DataFrame,
    multifactor_summary: pd.DataFrame,
    multifactor_audit: pd.DataFrame,
    variants: OrderedDict[str, list[str]],
) -> None:
    import xlsxwriter

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(
        output_path,
        {"constant_memory": True, "nan_inf_to_errors": False, "use_future_functions": True},
    )
    workbook.set_properties(
        {
            "title": "Corrected Weekly Factor Analysis",
            "subject": "Weekly close-to-close targets and factor selection",
            "author": "Ruifen Zheng",
            "comments": "Generated directly from the original weekly CSV by build_weekly_factor_analysis_from_csv.py",
        }
    )

    navy = "#17365D"
    blue = "#1F4E78"
    light_blue = "#D9EAF7"
    light_green = "#E2F0D9"
    light_amber = "#FFF2CC"
    light_red = "#FCE4D6"
    grey = "#E7E6E6"
    text = "#222222"

    fmt = {
        "title": workbook.add_format({"bold": True, "font_size": 14, "font_color": navy}),
        "note": workbook.add_format({"italic": True, "font_color": "#666666", "text_wrap": True}),
        "header": workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": blue, "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True}),
        "subheader": workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": navy, "border": 1, "align": "center", "valign": "vcenter"}),
        "text": workbook.add_format({"font_color": text, "valign": "vcenter"}),
        "text_wrap": workbook.add_format({"font_color": text, "valign": "top", "text_wrap": True}),
        "date": workbook.add_format({"num_format": "yyyy-mm-dd", "align": "center"}),
        "number": workbook.add_format({"num_format": "0.000000"}),
        "percent": workbook.add_format({"num_format": "0.00%"}),
        "integer": workbook.add_format({"num_format": "0"}),
        "selected": workbook.add_format({"bg_color": light_green, "font_color": text}),
        "optional": workbook.add_format({"bg_color": light_amber, "font_color": text}),
        "excluded": workbook.add_format({"bg_color": grey, "font_color": text}),
        "warning": workbook.add_format({"bg_color": light_red, "font_color": "#9C0006", "bold": True}),
        "formula": workbook.add_format({"num_format": "0.000000", "font_color": "#000000"}),
        "raw_number": workbook.add_format({"num_format": "0.000000", "font_color": "#0000FF"}),
    }

    def write_value(ws, row, col, value, cell_format=None):
        value = excel_value(value)
        if value is None:
            ws.write_blank(row, col, None, cell_format)
        elif isinstance(value, (pd.Timestamp,)):
            ws.write_datetime(row, col, value.to_pydatetime(), cell_format or fmt["date"])
        elif hasattr(value, "year") and hasattr(value, "month") and not isinstance(value, str):
            ws.write_datetime(row, col, value, cell_format or fmt["date"])
        else:
            ws.write(row, col, value, cell_format)

    def write_analysis_sheet(name, title, note, frame, widths=None, percent_cols=None):
        ws = workbook.add_worksheet(name)
        ws.hide_gridlines(2)
        ws.write(0, 0, title, fmt["title"])
        ws.write(1, 0, note, fmt["note"])
        ws.set_row(1, 34)
        ws.freeze_panes(4, 2 if "Factor" in frame.columns else 1)
        for c, header in enumerate(frame.columns):
            ws.write(3, c, header, fmt["header"])
        for r, row in enumerate(frame.itertuples(index=False, name=None), start=4):
            for c, value in enumerate(row):
                header = frame.columns[c]
                cell_format = None
                if "Date" == header:
                    cell_format = fmt["date"]
                elif percent_cols and header in percent_cols:
                    cell_format = fmt["percent"]
                elif isinstance(value, (float, np.floating)):
                    cell_format = fmt["number"]
                elif isinstance(value, (int, np.integer)):
                    cell_format = fmt["integer"]
                write_value(ws, r, c, value, cell_format)
        if len(frame):
            ws.autofilter(3, 0, 3 + len(frame), len(frame.columns) - 1)
        for c, width in enumerate(widths or [18] * len(frame.columns)):
            ws.set_column(c, c, width)
        return ws

    # Weekly Data: formulas are visible and carry their Python-calculated cached values.
    weekly_headers = [
        c for c in df.columns
        if c not in {"week_id", "source_row"} and not c.startswith("_fwd_")
    ]
    ws = workbook.add_worksheet("Weekly Data")
    ws.freeze_panes(1, 2)
    ws.hide_gridlines(2)
    for c, header in enumerate(weekly_headers):
        ws.write(0, c, header, fmt["header"])
    header_pos = {h: i for i, h in enumerate(weekly_headers)}
    for out_row, record in df.iterrows():
        excel_row = out_row + 2
        for c, header in enumerate(weekly_headers):
            value = record[header]
            if header == "date":
                write_value(ws, out_row + 1, c, value, fmt["date"])
            elif header == "ticker":
                write_value(ws, out_row + 1, c, value, fmt["text"])
            elif header == "adj_open_calc":
                formula = f'=IFERROR(C{excel_row}*G{excel_row}/F{excel_row},"")'
                cached = None if pd.isna(value) else float(value)
                ws.write_formula(out_row + 1, c, formula, fmt["formula"], cached)
            elif header in TARGETS.values():
                future = record[f"_{header}_row"]
                if pd.isna(future) or pd.isna(value):
                    ws.write_blank(out_row + 1, c, None, fmt["formula"])
                else:
                    future_excel_row = int(future) + 2
                    formula = f"=LN(G{future_excel_row}/G{excel_row})"
                    ws.write_formula(out_row + 1, c, formula, fmt["formula"], float(value))
            else:
                write_value(ws, out_row + 1, c, value, fmt["raw_number"] if c >= 2 else None)
    ws.autofilter(0, 0, len(df), len(weekly_headers) - 1)
    ws.set_column(0, 0, 12)
    ws.set_column(1, 1, 12)
    ws.set_column(2, len(weekly_headers) - 1, 15)

    # Weekly Rank IC sheets.
    for horizon in (1, 4, 12):
        frame = ic[horizon].reset_index().rename(columns={"date": "Date"})
        write_analysis_sheet(
            f"Weekly Rank IC {horizon}W",
            f"Weekly Rank IC - {horizon}W",
            f"Cross-sectional Spearman correlation for each week and factor. Minimum {MIN_STOCKS} valid stocks.",
            frame,
            widths=[12] + [16] * (len(frame.columns) - 1),
        )

    quintiles_out = quintiles.copy()
    quintiles_out["Direction"] = np.where(
        summary.set_index("Factor").loc[quintiles_out["Factor"], "Mean Rank IC"].to_numpy() >= 0,
        "Higher factor -> higher future return",
        "Lower factor -> higher future return",
    )
    write_analysis_sheet(
        "Quintile Analysis",
        "Quintile Analysis",
        "Each week, stocks are split into five equal groups by factor rank. Q1-Q5 are equal-weight means across eligible weeks.",
        quintiles_out,
        widths=[20, 28] + [14] * 7 + [36],
    )

    write_analysis_sheet(
        "Single Factor Summary",
        "Single Factor Summary",
        "Summary of the corrected 1W weekly Rank IC and quintile evidence.",
        summary,
        widths=[20, 28, 14, 16, 16, 14, 16, 14, 14, 38],
        percent_cols={"Positive IC %"},
    )
    write_analysis_sheet(
        "IC Decay",
        "IC Decay",
        "The same factor is evaluated against corrected 1W, 4W and 12W close-to-close targets.",
        decay,
        widths=[20, 28] + [15] * 9,
    )
    write_analysis_sheet(
        "Macro Weekly Calc",
        "Macro Weekly Calculation",
        "Macro variables are common across stocks, so this sheet uses weekly time-series observations.",
        macro_weekly,
        widths=[12, 20] + [24] * 4,
    )
    write_analysis_sheet(
        "Macro Factors",
        "Macro Factor Analysis",
        "Time-series Spearman and Pearson correlations against the weekly equal-weight corrected 1W return.",
        macro_results,
        widths=[30, 12, 16, 16, 24, 58],
    )
    write_analysis_sheet(
        "Stability",
        "Factor Stability",
        f"Time split: 2015-2020 vs 2021-2026. VIX split uses sample median {vix_median:.4f}.",
        stability,
        widths=[20, 28] + [18] * 7,
    )

    corr_out = correlation.copy()
    corr_out.insert(0, "Factor", corr_out.index)
    corr_out = corr_out.reset_index(drop=True)
    corr_ws = write_analysis_sheet(
        "Factor Correlation",
        "Factor Correlation Matrix",
        "Median of weekly cross-sectional Spearman correlations. Used for the redundancy screen.",
        corr_out,
        widths=[28] + [13] * (len(corr_out.columns) - 1),
    )
    corr_ws.conditional_format(4, 1, 3 + len(corr_out), len(corr_out.columns) - 1, {
        "type": "3_color_scale", "min_color": "#F8696B", "mid_color": "#FFEB84", "max_color": "#63BE7B"
    })

    # Method and source documentation.
    method_rows = [
        ["Section", "Item", "Definition / rule"],
        ["Target", "X_t", "Factor values observed at the unified market week-t close."],
        ["Target", "1W", "fwd_1w_return = LN(AdjClose[t+1] / AdjClose[t])."],
        ["Target", "4W", "fwd_4w_return = LN(AdjClose[t+4] / AdjClose[t])."],
        ["Target", "12W", "fwd_12w_return = LN(AdjClose[t+12] / AdjClose[t])."],
        ["Target", "Exact horizon", "t+h is based on the sorted shared market-week calendar. If that exact ticker/week row is missing, the target is blank."],
        ["Target", "Adjusted open", "adj_open_calc is retained for reference only and is not used by the corrected forward targets."],
        ["Rank IC", "Weekly Spearman", f"Each week and factor uses cross-sectional Spearman correlation with at least {MIN_STOCKS} valid stocks."],
        ["Quintile", "Q1-Q5", "Stocks are split into five equal groups within each week; group returns are then averaged equally across weeks."],
        ["ICIR", "Annualization", "Mean weekly IC / sample standard deviation of weekly IC x SQRT(52)."],
        ["Stability", "Time split", "Mean weekly IC for 2015-2020 and 2021-2026."],
        ["Stability", "VIX split", "Mean weekly IC below/at versus above the sample median weekly VIX."],
        ["Redundancy", "Factor correlation", "Median weekly cross-sectional Spearman correlation; Core selection uses pairwise |rho| < 0.75 where possible."],
        ["Evidence score", "Seven tests", "|Mean IC| >= 0.006; |ICIR| >= 0.30; |Q5-Q1| >= 0.00035; |monotonicity| >= 0.60; stable time sign; stable VIX sign; max(|4W IC|, |12W IC|) >= 0.008."],
        ["Selection", "Core 5", "Automated ranking by evidence score, |ICIR| and |Mean IC|, with one factor per family first and a redundancy screen."],
        ["Multi-factor", "Composite score", "Equal-weight mean of weekly cross-sectional percentile ranks. Negative-direction factors are reverse ranked."],
        ["Calculation", "Python", "The original 54-column CSV is read directly; all targets and downstream results are rebuilt by build_weekly_factor_analysis_from_csv.py."],
    ]
    method_ws = workbook.add_worksheet("Method")
    method_ws.hide_gridlines(2)
    for r, row in enumerate(method_rows):
        for c, value in enumerate(row):
            method_ws.write(r, c, value, fmt["header"] if r == 0 else fmt["text_wrap"])
    method_ws.set_column(0, 0, 18)
    method_ws.set_column(1, 1, 24)
    method_ws.set_column(2, 2, 110)
    method_ws.set_row(0, 28)
    for r in range(1, len(method_rows)):
        method_ws.set_row(r, 34)
    method_ws.freeze_panes(1, 0)

    source_rows = [["Group", "Columns", "How obtained"]]
    source_rows.append(["Raw market data", "date, ticker, open, high, low, close, adj_close, volume", "Original source values read directly from the weekly CSV."])
    for family, items in FACTOR_FAMILIES.items():
        source_rows.append([family, ", ".join(items), "Existing factor observations retained from Weekly Data."])
    source_rows.append(["Macro", ", ".join(MACRO_FACTORS), "Macro series retained from Weekly Data and analyzed as a time series."])
    source_ws = workbook.add_worksheet("Factor Source")
    source_ws.hide_gridlines(2)
    for r, row in enumerate(source_rows):
        for c, value in enumerate(row):
            source_ws.write(r, c, value, fmt["header"] if r == 0 else fmt["text_wrap"])
    source_ws.set_column(0, 0, 24)
    source_ws.set_column(1, 1, 95)
    source_ws.set_column(2, 2, 60)
    source_ws.freeze_panes(1, 0)

    selection_display = selection.drop(columns=["Direction Sign"]).copy()
    selection_ws = write_analysis_sheet(
        "Factor Selection",
        "Factor Selection",
        "Core and optional factors are selected reproducibly from the corrected single-factor evidence, stability, horizon strength and redundancy checks.",
        selection_display,
        widths=[20, 28, 38] + [16] * 12 + [14, 16, 24, 16, 65],
        percent_cols={"Positive IC %"},
    )
    role_col = selection_display.columns.get_loc("Final Role")
    for r, role in enumerate(selection_display["Final Role"], start=4):
        row_format = fmt["selected"] if role == "Core" else fmt["optional"] if role.startswith("Optional") else fmt["excluded"]
        selection_ws.set_row(r, None, row_format)

    # Multi-factor summary and weekly audit on a single sheet.
    mf = workbook.add_worksheet("Multi-Factor Analysis")
    mf.hide_gridlines(2)
    mf.write(0, 0, "Multi-Factor Analysis", fmt["title"])
    mf.write(1, 0, "Equal-weight, direction-aligned weekly percentile ranks using the automatically selected factors.", fmt["note"])
    mf.write(3, 0, "Combination", fmt["header"])
    mf.write(3, 1, "Included Factors", fmt["header"])
    mf.write(3, 2, "Purpose", fmt["header"])
    for r, (name, items) in enumerate(variants.items(), start=4):
        signs = selection.set_index("Factor")["Direction Sign"].to_dict()
        factor_text = " ".join(("+" if signs[x] > 0 else "-") + x for x in items)
        purpose = "Primary baseline" if name == "Core 5" else "Extension / sensitivity test"
        mf.write(r, 0, name)
        mf.write(r, 1, factor_text)
        mf.write(r, 2, purpose)

    summary_start = 4 + len(variants) + 2
    for c, header in enumerate(multifactor_summary.columns):
        mf.write(summary_start, c, header, fmt["header"])
    for r, row in enumerate(multifactor_summary.itertuples(index=False, name=None), start=summary_start + 1):
        for c, value in enumerate(row):
            cell_format = fmt["percent"] if multifactor_summary.columns[c].endswith("Positive %") else fmt["number"] if isinstance(value, (float, np.floating)) else None
            write_value(mf, r, c, value, cell_format)

    audit_start = summary_start + 2 + len(multifactor_summary) + 2
    mf.write(audit_start, 0, "Weekly audit", fmt["subheader"])
    for c, header in enumerate(multifactor_audit.columns):
        mf.write(audit_start + 1, c, header, fmt["header"])
    for r, row in enumerate(multifactor_audit.itertuples(index=False, name=None), start=audit_start + 2):
        for c, value in enumerate(row):
            write_value(mf, r, c, value, fmt["date"] if c == 0 else fmt["number"])
    mf.freeze_panes(audit_start + 2, 1)
    mf.set_column(0, 0, 26)
    mf.set_column(1, 1, 115)
    mf.set_column(2, max(2, len(multifactor_audit.columns) - 1), 18)

    workbook.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", nargs="?", type=Path, default=Path("test_data_weekly.csv"),
        help="Original weekly CSV (default: test_data_weekly.csv)",
    )
    parser.add_argument(
        "output", nargs="?", type=Path,
        default=Path("weekly_factor_analysis_from_original_csv.xlsx"),
        help="Output XLSX path (default: weekly_factor_analysis_from_original_csv.xlsx)",
    )
    args = parser.parse_args()

    factors = factor_list()
    print("1/10 Reading the original weekly CSV...", flush=True)
    data = read_weekly_data(args.input)
    missing = [c for c in [*factors, *MACRO_FACTORS, "adj_close"] if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    print("2/10 Correcting 1W, 4W and 12W targets...", flush=True)
    data = calculate_forward_returns(data)
    weeks = pd.DatetimeIndex(sorted(data["date"].unique()), name="Date")

    print("3/10 Calculating weekly Rank IC and quintiles...", flush=True)
    ic, quintiles = weekly_ic_and_quintiles(data, factors, weeks)
    summary = summarize_single_factors(ic[1], quintiles)
    decay = calculate_ic_decay(ic, factors)

    print("4/10 Calculating macro analysis...", flush=True)
    macro_weekly, macro_results = calculate_macro(data, weeks)

    print("5/10 Calculating stability...", flush=True)
    stability, vix_median = calculate_stability(ic[1], macro_weekly, factors)

    print("6/10 Calculating factor correlation matrix...", flush=True)
    correlation = calculate_factor_correlation(data, factors)

    print("7/10 Selecting factors...", flush=True)
    selection, core, fundamental_optional, horizon_optional = build_factor_selection(
        summary, quintiles, decay, stability, correlation
    )
    print(f"    Core 5: {core}", flush=True)
    print(f"    Optional fundamental: {fundamental_optional}", flush=True)
    print(f"    Optional horizon: {horizon_optional}", flush=True)

    print("8/10 Calculating multi-factor combinations...", flush=True)
    multifactor_summary, multifactor_audit, variants = calculate_multifactor(
        data, selection, core, fundamental_optional, horizon_optional, weeks
    )

    print("9/10 Writing workbook...", flush=True)
    build_workbook(
        args.output, data, ic, quintiles, summary, decay, macro_weekly,
        macro_results, stability, vix_median, correlation, selection,
        multifactor_summary, multifactor_audit, variants,
    )

    print("10/10 Validation summary", flush=True)
    print(f"    Rows: {len(data):,}", flush=True)
    print(f"    Tickers: {data['ticker'].nunique():,}", flush=True)
    print(f"    Weeks: {data['date'].nunique():,}", flush=True)
    for horizon, target in TARGETS.items():
        print(f"    Valid {horizon}W targets: {data[target].notna().sum():,}", flush=True)
    print(f"    Output: {args.output.resolve()}", flush=True)


if __name__ == "__main__":
    main()
