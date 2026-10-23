from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRanker


FEATURES = [
    "revenue_growth_yoy",
    "operating_profitability",
    "cashflow_to_assets",
    "debt_to_assets",
    "asset_growth_yoy",
]
RANK_FEATURES = [f"rank__{x}" for x in FEATURES]
TRAINING_WEEKS = 312
REFIT_WEEKS = 26
RANDOM_STATE = 5703
SELECTED = {"candidate_id": 2, "max_depth": 2, "min_child_weight": 5, "n_estimators": 150}


def load_train(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["date"], float_precision="round_trip")
    frame = frame.rename(columns={"target": "target1"})
    required = {"date", "ticker", "target1", *FEATURES}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return frame.dropna(subset=FEATURES + ["target1"]).sort_values(["date", "ticker"], kind="stable")


def add_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    groups = frame.groupby("date", sort=False)
    for feature in FEATURES:
        frame[f"rank__{feature}"] = groups[feature].rank(method="average", pct=True)
    return frame


def labels(frame: pd.DataFrame) -> np.ndarray:
    ranks = frame.groupby("date", sort=False).target1.rank(method="average", ascending=True)
    sizes = frame.groupby("date", sort=False).target1.transform("count")
    return np.floor((ranks - 1.0) * 5 / sizes).clip(0, 4).astype(np.int32).to_numpy()


def fit_model(history: pd.DataFrame) -> XGBRanker:
    ordered = add_ranks(history).sort_values(["date", "ticker"], kind="stable")
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
        max_depth=SELECTED["max_depth"],
        min_child_weight=SELECTED["min_child_weight"],
        n_estimators=SELECTED["n_estimators"],
    )
    model.fit(ordered[RANK_FEATURES].to_numpy(dtype=np.float32), labels(ordered), group=groups, verbose=False)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit the frozen five-factor XGBRanker models on the 66-stock universe.")
    parser.add_argument("--train-file", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("models"), type=Path)
    args = parser.parse_args()
    train = load_train(args.train_file)
    dates = sorted(pd.to_datetime(train.date.unique()))
    # The refit dates correspond to the external 40-stock prediction schedule.
    refit_dates = [pd.Timestamp(x) for x in [
        "2022-08-26", "2023-02-24", "2023-08-25", "2024-02-23", "2024-08-23",
        "2025-02-21", "2025-08-22", "2026-02-20", "2026-08-21",
    ]]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for index, refit_date in enumerate(refit_dates, 1):
        available = [date for date in dates if date < refit_date]
        if len(available) < TRAINING_WEEKS:
            raise ValueError(f"Not enough history before {refit_date.date()}")
        history_dates = available[-TRAINING_WEEKS:]
        history = train[train.date.isin(history_dates)].copy()
        model_id = f"five_factor_ranker_refit_{index:02d}_{refit_date:%Y%m%d}"
        model = fit_model(history)
        model.save_model(args.output_dir / f"{model_id}.json")
        records.append({
            "model_id": model_id,
            "refit_date": refit_date.date().isoformat(),
            "training_start_date": pd.Timestamp(history_dates[0]).date().isoformat(),
            "training_end_date": pd.Timestamp(history_dates[-1]).date().isoformat(),
            "training_weeks": TRAINING_WEEKS,
            "training_tickers": int(history.ticker.nunique()),
            "candidate_id": SELECTED["candidate_id"],
            "max_depth": SELECTED["max_depth"],
            "min_child_weight": SELECTED["min_child_weight"],
            "n_estimators": SELECTED["n_estimators"],
        })
        print(f"saved {model_id}", flush=True)
    pd.DataFrame(records).to_csv(args.output_dir / "model_manifest.csv", index=False)
    (args.output_dir / "configuration.json").write_text(json.dumps({
        "model": "standalone five-factor XGBRanker",
        "training_tickers": 66,
        "external_test_tickers": 40,
        "training_window_weeks": TRAINING_WEEKS,
        "refit_interval_weeks": REFIT_WEEKS,
        "features": FEATURES,
        "selected_candidate": SELECTED,
        "random_state": RANDOM_STATE,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
