"""Development-only factor analysis for next-week open-to-close stock ranking."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ml.config import (
    DATA_FILE, DUPLICATE_REPRESENTATIONS, FACTOR_OUTPUT_DIR, FUNDAMENTAL_MIN_COVERAGE_RATIO,
    MIN_STOCKS, REDUNDANCY_LIMIT, TARGET_COLUMN, TECHNICAL_MIN_COVERAGE_RATIO,
    WARMUP_END, WARMUP_START, factor_family, stock_factors,
)
from ml.data import add_exact_week_targets, load_weekly_panel, manual_target_samples


def pair_spearman(x: pd.Series, y: pd.Series, minimum: int = MIN_STOCKS) -> float:
    pair = pd.concat([x, y], axis=1).dropna()
    if len(pair) < minimum or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return np.nan
    return float(spearmanr(pair.iloc[:, 0], pair.iloc[:, 1]).statistic)


def calculate_forward_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible public name for the corrected exact-week builder."""
    return add_exact_week_targets(df)


def weekly_factor_metrics(df: pd.DataFrame, factors: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    date_rows, quintile_rows = [], []
    for date, group in df.groupby("date", sort=True):
        for factor in factors:
            pair = group[[factor, TARGET_COLUMN]].dropna()
            ic = pair_spearman(pair[factor], pair[TARGET_COLUMN])
            date_rows.append({"date": date, "factor": factor, "rank_ic": ic, "number_of_stocks": len(pair)})
            if len(pair) < MIN_STOCKS or pair[factor].nunique() < 5:
                continue
            ranked = pair.sort_index().copy()
            ranks = ranked[factor].rank(method="first") - 1
            ranked["quintile"] = np.minimum((ranks * 5 // len(ranks)).astype(int) + 1, 5)
            means = ranked.groupby("quintile")[TARGET_COLUMN].mean()
            row = {"date": date, "factor": factor}
            row.update({f"q{i}": means.get(i, np.nan) for i in range(1, 6)})
            quintile_rows.append(row)
    return pd.DataFrame(date_rows), pd.DataFrame(quintile_rows)


def correlation_matrix(df: pd.DataFrame, factors: list[str]) -> pd.DataFrame:
    matrices = [g[factors].corr(method="spearman", min_periods=MIN_STOCKS).to_numpy()
                for _, g in df.groupby("date", sort=True)]
    with np.errstate(all="ignore"):
        values = np.nanmedian(np.stack(matrices), axis=0)
    np.fill_diagonal(values, 1.0)
    return pd.DataFrame(values, index=factors, columns=factors)


def summarize_factors(development, by_date, quintiles, correlation, factors) -> pd.DataFrame:
    dates = pd.DatetimeIndex(sorted(development["date"].unique()))
    midpoint = dates[len(dates) // 2]
    vix_by_date = development.groupby("date")["macro_vix_level"].first()
    vix_median = vix_by_date.median()
    rows = []
    for factor in factors:
        d = by_date.loc[by_date["factor"] == factor].dropna(subset=["rank_ic"])
        ic = d.set_index("date")["rank_ic"]
        q = quintiles.loc[quintiles["factor"] == factor]
        qmeans = q[[f"q{i}" for i in range(1, 6)]].mean() if len(q) else pd.Series(dtype=float)
        spread = qmeans.get("q5", np.nan) - qmeans.get("q1", np.nan)
        monotonicity = pair_spearman(pd.Series(range(1, 6)), pd.Series([qmeans.get(f"q{i}", np.nan) for i in range(1, 6)]), 3)
        values = development[factor]
        weekly_coverage = development.assign(_ok=values.notna()).groupby("date")["_ok"].sum()
        observed = int(values.notna().sum())
        mean_ic, std = ic.mean(), ic.std(ddof=1)
        early, late = ic.loc[ic.index < midpoint].mean(), ic.loc[ic.index >= midpoint].mean()
        low_dates, high_dates = vix_by_date.index[vix_by_date <= vix_median], vix_by_date.index[vix_by_date > vix_median]
        others = correlation.loc[factor].drop(index=factor).abs()
        rows.append({
            "factor": factor, "family": factor_family(factor), "eligible_weeks": len(ic),
            "mean_rank_ic": mean_ic, "median_rank_ic": ic.median(), "ic_std": std,
            "icir": mean_ic / std if np.isfinite(std) and std else np.nan,
            "annualized_icir": mean_ic / std * math.sqrt(52) if np.isfinite(std) and std else np.nan,
            "positive_ic_ratio": (ic > 0).mean(), "negative_ic_ratio": (ic < 0).mean(),
            "direction": "positive" if mean_ic >= 0 else "negative",
            **{f"q{i}": qmeans.get(f"q{i}", np.nan) for i in range(1, 6)},
            "q5_q1": spread, "direction_adjusted_top_bottom": abs(spread), "monotonicity": monotonicity,
            "coverage": observed / len(development), "missing_rate": 1 - observed / len(development),
            "average_stocks_per_eligible_week": weekly_coverage[weekly_coverage > 0].mean(),
            "minimum_stocks_per_eligible_week": weekly_coverage[weekly_coverage > 0].min(),
            "early_mean_ic": early, "late_mean_ic": late,
            "low_vix_mean_ic": ic.reindex(low_dates).mean(), "high_vix_mean_ic": ic.reindex(high_dates).mean(),
            "max_abs_correlation": others.max(),
        })
    result = pd.DataFrame(rows)
    same_time = np.sign(result["early_mean_ic"]) == np.sign(result["late_mean_ic"])
    same_regime = np.sign(result["low_vix_mean_ic"]) == np.sign(result["high_vix_mean_ic"])
    result["evidence_score"] = (
        (result["mean_rank_ic"].abs() >= .006).astype(int) + (result["icir"].abs() >= .30).astype(int)
        + (result["direction_adjusted_top_bottom"] >= .00035).astype(int)
        + (result["monotonicity"].abs() >= .60).astype(int) + same_time.astype(int)
        + same_regime.astype(int) + (result["coverage"] >= result["family"].map(
            lambda family: FUNDAMENTAL_MIN_COVERAGE_RATIO if family == "fundamental" else TECHNICAL_MIN_COVERAGE_RATIO)).astype(int)
    )
    result["evidence_flag"] = np.select(
        [result["evidence_score"] >= 6, result["evidence_score"] >= 4], ["Strong", "Moderate"], default="Weak")
    return result


def ranked_admissible(summary: pd.DataFrame) -> pd.DataFrame:
    thresholds = summary["family"].map(
        lambda family: FUNDAMENTAL_MIN_COVERAGE_RATIO if family == "fundamental" else TECHNICAL_MIN_COVERAGE_RATIO)
    result = summary.loc[(~summary["factor"].isin(DUPLICATE_REPRESENTATIONS)) & (summary["coverage"] >= thresholds)].copy()
    result["abs_icir"], result["abs_mean_ic"] = result["icir"].abs(), result["mean_rank_ic"].abs()
    result["abs_spread"] = result["direction_adjusted_top_bottom"].abs()
    return result.sort_values(["evidence_score", "abs_icir", "abs_mean_ic", "abs_spread", "factor"],
                              ascending=[False, False, False, False, True], kind="stable")


def select_factor_sets(summary: pd.DataFrame, corr: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    ordered = ranked_admissible(summary)
    baseline = ordered.loc[ordered["family"] != "fundamental"].copy()
    core, used_families = [], set()
    for factor in baseline["factor"]:
        family = factor_family(factor)
        if family != "fundamental" and family not in used_families and all(abs(corr.at[factor, c]) < REDUNDANCY_LIMIT for c in core):
            core.append(factor); used_families.add(family)
        if len(core) == 5: break
    for factor in baseline["factor"]:
        if len(core) == 5: break
        if factor not in core and factor_family(factor) != "fundamental" and all(abs(corr.at[factor, c]) < REDUNDANCY_LIMIT for c in core):
            core.append(factor)
    fundamentals = ordered.loc[ordered["family"] == "fundamental", "factor"].tolist()
    fundamental = fundamentals[0] if fundamentals else None
    extras = [f for f in baseline["factor"] if f not in core and factor_family(f) != "cross_sectional_rank"]
    horizon = extras[0] if extras else None
    extended = list(dict.fromkeys(core + ([fundamental] if fundamental else []) + ([horizon] if horizon else [])))
    all_factors = baseline["factor"].tolist()
    strong = baseline.loc[baseline["evidence_flag"] == "Strong", "factor"].tolist() or all_factors[:3]
    moderate = baseline.loc[baseline["evidence_flag"].isin(["Strong", "Moderate"]), "factor"].tolist() or all_factors[:5]
    sets = {
        "core_5": core, "core_plus_fundamental": list(dict.fromkeys(core + ([fundamental] if fundamental else []))),
        "core_plus_horizon": list(dict.fromkeys(core + ([horizon] if horizon else []))), "extended": extended,
        "strong_only": strong, "moderate_and_strong": moderate,
        **{f"top_{n}": all_factors[:n] for n in (3, 5, 8, 10, 15)}, "all_eligible": all_factors,
    }
    roles = {f: [] for f in summary["factor"]}
    for f in core: roles[f].append("core")
    if fundamental: roles[fundamental].append("optional_fundamental")
    if horizon: roles[horizon].append("optional_horizon")
    selection = summary.copy()
    selection["final_role"] = selection["factor"].map(lambda f: ";".join(roles[f]) if roles[f] else "candidate")
    selection["selection_reason"] = selection.apply(
        lambda r: "Duplicate rank representation excluded from default sets" if r.factor in DUPLICATE_REPRESENTATIONS
        else "Below family-specific warmup coverage requirement" if r.coverage < (
            FUNDAMENTAL_MIN_COVERAGE_RATIO if r.family == "fundamental" else TECHNICAL_MIN_COVERAGE_RATIO)
        else "Warmup-only evidence ordering; compact core also applies family diversity and redundancy", axis=1)
    return sets, selection


def calculate_multifactor(df, factor_sets, selection) -> pd.DataFrame:
    directions = selection.set_index("factor")["direction"].map({"positive": 1, "negative": -1}).to_dict()
    rows = []
    for name, factors in factor_sets.items():
        ics, spreads, counts = [], [], []
        for _, group in df.groupby("date", sort=True):
            usable = group.dropna(subset=[TARGET_COLUMN]).copy()
            if len(usable) < MIN_STOCKS: continue
            ranks = usable[factors].rank(pct=True)
            for factor in factors: ranks[factor] *= directions.get(factor, 1)
            pair = pd.DataFrame({"score": ranks.mean(axis=1), "target": usable[TARGET_COLUMN]}).dropna()
            ic = pair_spearman(pair.score, pair.target)
            if np.isfinite(ic): ics.append(ic)
            if len(pair) >= MIN_STOCKS:
                pair = pair.sort_values("score"); k = max(1, len(pair) // 5)
                spreads.append(pair.tail(k).target.mean() - pair.head(k).target.mean()); counts.append(len(pair))
        values = pd.Series(ics, dtype=float)
        rows.append({"factor_set_name": name, "number_of_features": len(factors), "feature_list": json.dumps(factors),
                     "mean_rank_ic": values.mean(), "median_rank_ic": values.median(),
                     "icir": values.mean()/values.std() if len(values)>1 and values.std() else np.nan,
                     "positive_ic_ratio": (values>0).mean(), "top_bottom_spread": np.mean(spreads), "average_stocks": np.mean(counts)})
    return pd.DataFrame(rows)


def run_factor_analysis(input_path: Path, output_dir: Path) -> dict[str, list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("[1/6] Loading weekly data", flush=True)
    data = add_exact_week_targets(load_weekly_panel(input_path))
    factors = [f for f in stock_factors() if f in data]
    development = data.loc[data["date"].between(WARMUP_START, WARMUP_END)].copy()
    print("[2/6] Validating exact next-week open-to-close target", flush=True)
    samples = manual_target_samples(data, 20)
    if not np.allclose(samples["calculated_target"], samples["manual_target"], rtol=1e-12, atol=1e-12):
        raise AssertionError("Manual target validation failed")
    samples.to_csv(output_dir / "target_validation_samples.csv", index=False)
    print(samples.to_string(index=False), flush=True)
    print("[3/6] Running first-three-year warmup factor analysis", flush=True)
    by_date, quintiles = weekly_factor_metrics(development, factors)
    corr = correlation_matrix(development, factors)
    summary = summarize_factors(development, by_date, quintiles, corr, factors)
    factor_sets, selection = select_factor_sets(summary, corr)
    print("[4/6] Exporting factor evidence and correlation", flush=True)
    by_date.to_csv(output_dir / "factor_metrics_by_date.csv", index=False)
    yearly = by_date.assign(year=by_date["date"].dt.year).groupby(["year", "factor"], as_index=False).agg(
        mean_rank_ic=("rank_ic", "mean"), median_rank_ic=("rank_ic", "median"), rank_ic_std=("rank_ic", "std"),
        positive_ic_ratio=("rank_ic", lambda x: (x.dropna() > 0).mean()), eligible_weeks=("rank_ic", "count"))
    yearly.to_csv(output_dir / "factor_metrics_by_year.csv", index=False)
    corr.rename_axis("factor").reset_index().to_csv(output_dir / "factor_correlation.csv", index=False)
    selection.to_csv(output_dir / "factor_selection_summary.csv", index=False)
    selection.to_csv(output_dir / "warmup_single_factor_summary.csv", index=False)
    by_date.to_csv(output_dir / "warmup_factor_metrics_by_date.csv", index=False)
    corr.rename_axis("factor").reset_index().to_csv(output_dir / "warmup_factor_correlation.csv", index=False)
    print("[5/6] Building corrected-target factor combinations", flush=True)
    calculate_multifactor(development, factor_sets, selection).to_csv(output_dir / "multifactor_summary.csv", index=False)
    payload = {"target": TARGET_COLUMN, "warmup_period": {"start": WARMUP_START, "end": WARMUP_END},
               "selection_order": "evidence_score desc, |ICIR| desc, |Mean Rank IC| desc, |Q5-Q1| desc, factor asc; core adds family diversity and |rho| limit",
               "redundancy_limit": REDUNDANCY_LIMIT, "factor_sets": {
                   name: {"factors": values, "n_features": len(values), "selection_method": "warmup_only_deterministic_evidence"}
                   for name, values in factor_sets.items()}}
    (output_dir / "ml_factor_sets.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("[6/6] Factor analysis complete", flush=True)
    print(f"Valid primary targets: {data[TARGET_COLUMN].notna().sum():,}; missing: {data[TARGET_COLUMN].isna().sum():,}")
    return factor_sets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA_FILE)
    parser.add_argument("--output-dir", type=Path, default=FACTOR_OUTPUT_DIR)
    args = parser.parse_args()
    run_factor_analysis(args.input, args.output_dir)


if __name__ == "__main__":
    main()
