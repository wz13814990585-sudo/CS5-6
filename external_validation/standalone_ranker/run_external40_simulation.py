from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRanker


ROOT = Path(__file__).resolve().parent
TRAIN_FILE = ROOT / "inputs" / "train66.csv"
TEST_FILE = ROOT / "inputs" / "test40_with_prices.csv"
OUT = ROOT / "outputs"

FEATURES = [
    "revenue_growth_yoy",
    "operating_profitability",
    "cashflow_to_assets",
    "debt_to_assets",
    "asset_growth_yoy",
]

TRAINING_WEEKS = 312       # six years
REFIT_WEEKS = 26           # half-yearly refit
TOP_K = 5
FEE_RATE = 0.001           # 10 bps per side
INITIAL_CAPITAL = 100_000.0
RANDOM_STATE = 5703

# Hyperparameters are selected only from the 66-stock Development history.
DEV_START = pd.Timestamp("2022-09-02")
DEV_END = pd.Timestamp("2024-08-30")
FINAL_TEST_START = pd.Timestamp("2025-09-05")
FINAL_TEST_END = pd.Timestamp("2026-08-21")


def candidate_grid() -> list[dict]:
    result = []
    for depth, child, trees in itertools.product([2, 3], [5, 20], [50, 150, 300]):
        result.append({
            "candidate_id": len(result) + 1,
            "max_depth": depth,
            "min_child_weight": child,
            "n_estimators": trees,
        })
    return result


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(TRAIN_FILE, parse_dates=["date"], float_precision="round_trip")
    test = pd.read_csv(TEST_FILE, parse_dates=["date"], float_precision="round_trip")

    # The handoff training file names the continuous target ``target``;
    # the price-augmented external file names it ``target1``.
    train = train.rename(columns={"target": "target1"}).copy()
    required_train = {"date", "ticker", "target1", *FEATURES}
    required_test = {"date", "ticker", "target1", "buy_price", "sell_price", *FEATURES}
    missing_train = sorted(required_train - set(train.columns))
    missing_test = sorted(required_test - set(test.columns))
    if missing_train or missing_test:
        raise RuntimeError(f"Missing training columns={missing_train}; test columns={missing_test}")

    train = train.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)
    test = test.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)
    train = train.dropna(subset=FEATURES + ["target1"]).copy()
    test = test.dropna(subset=FEATURES + ["target1", "buy_price", "sell_price"]).copy()

    overlap = sorted(set(train.ticker) & set(test.ticker))
    if overlap:
        raise RuntimeError(f"Training/test ticker overlap detected: {overlap[:10]}")
    return train, test


def weekly_rank_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    grouped = out.groupby("date", sort=False)
    for feature in FEATURES:
        out[f"rank__{feature}"] = grouped[feature].rank(method="average", pct=True)
    return out


RANK_FEATURES = [f"rank__{feature}" for feature in FEATURES]


def relevance_labels(frame: pd.DataFrame) -> np.ndarray:
    # Five relevance levels (0--4), assigned within each training week.
    ranks = frame.groupby("date", sort=False)["target1"].rank(method="average", ascending=True)
    sizes = frame.groupby("date", sort=False)["target1"].transform("count")
    labels = np.floor((ranks - 1.0) * 5 / sizes).clip(0, 4)
    return labels.astype(np.int32).to_numpy()


def preprocess(train: pd.DataFrame, pred: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Cross-sectional ranks are calculated separately in each universe, as in
    # the supplied ensemble handoff. No test target enters this transform.
    return weekly_rank_features(train), weekly_rank_features(pred)


def fit_predict(train: pd.DataFrame, pred: pd.DataFrame, candidate: dict) -> np.ndarray:
    train, pred = preprocess(train, pred)
    ordered = train.sort_values(["date", "ticker"], kind="stable")
    groups = ordered.groupby("date", sort=False).size().to_numpy(dtype=np.uint32)
    model = XGBRanker(
        objective="rank:pairwise",
        tree_method="hist",
        eval_metric="ndcg@10",
        learning_rate=0.04,
        subsample=0.9,
        colsample_bytree=1.0,
        reg_alpha=0.0,
        reg_lambda=2.0,
        gamma=0.0,
        random_state=RANDOM_STATE,
        n_jobs=1,
        **{k: candidate[k] for k in ("max_depth", "min_child_weight", "n_estimators")},
    )
    model.fit(
        ordered[RANK_FEATURES].to_numpy(dtype=np.float32),
        relevance_labels(ordered),
        group=groups,
        verbose=False,
    )
    return model.predict(pred[RANK_FEATURES].to_numpy(dtype=np.float32))


def preceding_training_dates(train_dates: list[pd.Timestamp], fit_date: pd.Timestamp) -> list[pd.Timestamp] | None:
    available = [date for date in train_dates if date < fit_date]
    if len(available) < TRAINING_WEEKS:
        return None
    return available[-TRAINING_WEEKS:]


def rolling_predictions(
    train: pd.DataFrame,
    prediction_universe: pd.DataFrame,
    candidate: dict,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    train_dates = sorted(pd.to_datetime(train.date.unique()))
    pred_dates = sorted(pd.to_datetime(prediction_universe.date.unique()))
    eligible = [date for date in pred_dates if start <= date <= end]
    if not eligible:
        return pd.DataFrame()

    parts = []
    # Refit on the first eligible week and then every 26 prediction weeks.
    for offset in range(0, len(eligible), REFIT_WEEKS):
        fit_date = eligible[offset]
        block_dates = eligible[offset: offset + REFIT_WEEKS]
        history_dates = preceding_training_dates(train_dates, fit_date)
        if history_dates is None:
            continue
        history = train[train.date.isin(history_dates)].copy()
        block = prediction_universe[prediction_universe.date.isin(block_dates)].copy()
        if history.empty or block.empty:
            continue
        block["prediction"] = fit_predict(history, block, candidate)
        block["refit_date"] = fit_date
        block["candidate_id"] = candidate["candidate_id"]
        parts.append(block)

    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out["rank"] = out.groupby("date")["prediction"].rank(method="first", ascending=False)
    return out


def rank_ic(pred: pd.DataFrame) -> pd.Series:
    values = []
    for _, group in pred.groupby("date", sort=True):
        if len(group) >= 2 and group.prediction.nunique() > 1 and group.target1.nunique() > 1:
            values.append(group.prediction.corr(group.target1, method="spearman"))
    return pd.Series(values, dtype=float)


def annualized(weekly_returns: pd.Series | np.ndarray) -> float:
    values = pd.Series(weekly_returns).dropna()
    if values.empty or (values <= -1).any():
        return float("nan")
    return float(np.expm1(np.log1p(values).mean() * 52))


def evaluation_metrics(pred: pd.DataFrame) -> dict:
    ric = rank_ic(pred)
    top, market = [], []
    for _, group in pred.groupby("date", sort=True):
        if len(group) < TOP_K:
            continue
        top.append(float(np.expm1(group.nlargest(TOP_K, "prediction").target1).mean()))
        market.append(float(np.expm1(group.target1).mean()))
    excess = np.asarray(top) - np.asarray(market)
    return {
        "weeks": int(pred.date.nunique()),
        "rows": int(len(pred)),
        "mean_rank_ic": float(ric.mean()) if len(ric) else float("nan"),
        "rank_icir": float(ric.mean() / ric.std(ddof=1)) if len(ric) > 1 and ric.std(ddof=1) > 0 else float("nan"),
        "positive_rank_ic_pct": float((ric > 0).mean()) if len(ric) else float("nan"),
        "top5_annualized_excess": annualized(excess),
    }


def select_candidate(train: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    records = []
    for candidate in candidate_grid():
        print(f"Development candidate {candidate['candidate_id']}/12", flush=True)
        pred = rolling_predictions(train, train, candidate, DEV_START, DEV_END)
        records.append({**candidate, **evaluation_metrics(pred)})
    scores = pd.DataFrame(records)
    scores["passes_gate"] = (
        (scores.mean_rank_ic > 0)
        & (scores.rank_icir >= 0.05)
        & (scores.positive_rank_ic_pct >= 0.50)
    )
    eligible = scores[scores.passes_gate & scores.top5_annualized_excess.notna()]
    if eligible.empty:
        # Keep the package runnable and make the fallback explicit in the CSV.
        selected = scores.sort_values(
            ["top5_annualized_excess", "mean_rank_ic", "rank_icir", "candidate_id"],
            ascending=[False, False, False, True],
        ).iloc[0]
        selection_rule = "fallback_highest_development_top5_excess_no_candidate_passed_gate"
    else:
        selected = eligible.sort_values(
            ["top5_annualized_excess", "mean_rank_ic", "rank_icir", "candidate_id"],
            ascending=[False, False, False, True],
        ).iloc[0]
        selection_rule = "development_gate_then_highest_top5_excess"
    scores["selected"] = scores.candidate_id.eq(selected.candidate_id)
    scores["selection_rule"] = selection_rule
    selected_dict = next(c for c in candidate_grid() if c["candidate_id"] == int(selected.candidate_id))
    return scores, selected_dict


def simulate(pred: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    weeks, trades = [], []
    cash = INITIAL_CAPITAL
    for signal_date, group in pred.groupby("date", sort=True):
        picks = group.sort_values(["rank", "ticker"], kind="stable").head(TOP_K)
        if len(picks) < TOP_K:
            continue
        start_cash = cash
        allocation = start_cash / TOP_K
        buy_gross = buy_fees = 0.0
        positions = []
        for row in picks.itertuples(index=False):
            shares = int(np.floor(allocation / (float(row.buy_price) * (1 + FEE_RATE))))
            gross = shares * float(row.buy_price)
            fee = gross * FEE_RATE
            buy_gross += gross
            buy_fees += fee
            positions.append((row, shares, gross, fee))
        sell_gross = sell_fees = 0.0
        for row, shares, gross, buy_fee in positions:
            value = shares * float(row.sell_price)
            fee = value * FEE_RATE
            sell_gross += value
            sell_fees += fee
            trades.append({
                "signal_date": signal_date,
                "ticker": row.ticker,
                "rank": row.rank,
                "prediction": row.prediction,
                "buy_price": row.buy_price,
                "shares": shares,
                "sell_price": row.sell_price,
                "buy_fee": buy_fee,
                "sell_fee": fee,
                "net_trade_pnl": value - fee - gross - buy_fee,
            })
        cash = start_cash - buy_gross - buy_fees + sell_gross - sell_fees
        weeks.append({
            "signal_date": signal_date,
            "start_capital": start_cash,
            "end_capital": cash,
            "weekly_net_return": cash / start_cash - 1,
            "buy_fees": buy_fees,
            "sell_fees": sell_fees,
            "selected_tickers": ",".join(picks.ticker),
        })
    weekly = pd.DataFrame(weeks)
    if weekly.empty:
        return weekly, pd.DataFrame(trades)
    weekly["peak_capital"] = weekly.end_capital.cummax()
    weekly["drawdown"] = weekly.end_capital / weekly.peak_capital - 1
    return weekly, pd.DataFrame(trades)


def summary_rows(weekly: pd.DataFrame) -> list[dict]:
    rows = []
    final_test = weekly[
        (pd.to_datetime(weekly.signal_date) >= FINAL_TEST_START)
        & (pd.to_datetime(weekly.signal_date) <= FINAL_TEST_END)
    ].copy()
    for label, frame in [("external_prediction_period", weekly), ("final_test_51_weeks", final_test)]:
        if frame.empty:
            continue
        rows.append({
            "period": label,
            "start_date": str(frame.iloc[0].signal_date.date()),
            "end_date": str(frame.iloc[-1].signal_date.date()),
            "weeks": int(len(frame)),
            "initial_capital": INITIAL_CAPITAL,
            "final_capital": float(frame.iloc[-1].end_capital),
            "total_return": float(frame.iloc[-1].end_capital / INITIAL_CAPITAL - 1),
            "annualized_return": annualized(frame.weekly_net_return),
            "max_drawdown": float(frame.drawdown.min()),
            "total_fees": float(frame.buy_fees.sum() + frame.sell_fees.sum()),
        })
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    train, test = load_inputs()
    print(f"Training universe: {train.ticker.nunique()} tickers; test universe: {test.ticker.nunique()} tickers", flush=True)
    scores, selected = select_candidate(train)
    scores.to_csv(OUT / "development_candidate_scores.csv", index=False)
    print(f"Selected Development candidate: {selected}", flush=True)

    pred = rolling_predictions(train, test, selected, test.date.min(), test.date.max())
    pred.to_csv(OUT / "external_test_predictions.csv", index=False)
    test_metrics = evaluation_metrics(pred)
    pd.DataFrame([test_metrics]).to_csv(OUT / "external_test_metrics.csv", index=False)

    weekly, trades = simulate(pred)
    weekly.to_csv(OUT / "weekly_nav.csv", index=False)
    trades.to_csv(OUT / "trade_ledger.csv", index=False)
    pd.DataFrame(summary_rows(weekly)).to_csv(OUT / "simulation_summary.csv", index=False)

    manifest = {
        "model": "standalone 5-factor XGBRanker",
        "training_tickers": int(train.ticker.nunique()),
        "external_test_tickers": int(test.ticker.nunique()),
        "ticker_overlap": int(len(set(train.ticker) & set(test.ticker))),
        "training_window_weeks": TRAINING_WEEKS,
        "refit_interval_weeks": REFIT_WEEKS,
        "features": FEATURES,
        "development_selection_only": True,
        "selected_candidate": selected,
        "simulation": {
            "top_k": TOP_K,
            "integer_shares": True,
            "fee_rate_each_side": FEE_RATE,
            "initial_capital": INITIAL_CAPITAL,
            "buy_price": "next-week first-trading-day open proxy in test40_with_prices.csv",
            "sell_price": "next-week last-trading-day close proxy in test40_with_prices.csv",
        },
        "note": "The 40-stock labels and prices are never used to fit or select the model.",
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print("Completed. The model was fitted only on train66 and evaluated/simulated on external test40.", flush=True)


if __name__ == "__main__":
    main()
