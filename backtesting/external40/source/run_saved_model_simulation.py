from __future__ import annotations

import argparse
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
TOP_K = 5
FEE_RATE = 0.001
INITIAL_CAPITAL = 100_000.0


def add_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    groups = frame.groupby("date", sort=False)
    for feature in FEATURES:
        frame[f"rank__{feature}"] = groups[feature].rank(method="average", pct=True)
    return frame


def load_test(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["date"], float_precision="round_trip")
    required = {"date", "ticker", "target1", "buy_price", "sell_price", *FEATURES}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return frame.dropna(subset=FEATURES + ["buy_price", "sell_price"]).sort_values(["date", "ticker"], kind="stable")


def predict(test: pd.DataFrame, model_dir: Path) -> pd.DataFrame:
    manifest = pd.read_csv(model_dir / "model_manifest.csv", parse_dates=["refit_date"])
    dates = sorted(pd.to_datetime(test.date.unique()))
    parts = []
    for i, row in manifest.iterrows():
        start = row.refit_date
        end = manifest.iloc[i + 1].refit_date - pd.Timedelta(days=1) if i + 1 < len(manifest) else dates[-1]
        block = test[(test.date >= start) & (test.date <= end)].copy()
        if block.empty:
            continue
        block = add_ranks(block)
        model = XGBRanker(n_jobs=1)
        model.load_model(model_dir / f"{row.model_id}.json")
        block["prediction"] = model.predict(block[RANK_FEATURES].to_numpy(dtype=np.float32))
        block["refit_date"] = start
        parts.append(block)
    if not parts:
        raise ValueError("No test rows matched the saved model refit dates")
    out = pd.concat(parts, ignore_index=True)
    out["rank"] = out.groupby("date")["prediction"].rank(method="first", ascending=False)
    return out


def simulate(pred: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    weekly, trades = [], []
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
            trades.append({"signal_date": signal_date, "ticker": row.ticker, "rank": row.rank,
                           "buy_price": row.buy_price, "shares": shares, "sell_price": row.sell_price,
                           "buy_fee": buy_fee, "sell_fee": fee,
                           "net_trade_pnl": value - fee - gross - buy_fee})
        cash = start_cash - buy_gross - buy_fees + sell_gross - sell_fees
        weekly.append({"signal_date": signal_date, "start_capital": start_cash, "end_capital": cash,
                       "weekly_net_return": cash / start_cash - 1, "buy_fees": buy_fees,
                       "sell_fees": sell_fees, "selected_tickers": ",".join(picks.ticker)})
    nav = pd.DataFrame(weekly)
    if not nav.empty:
        nav["peak_capital"] = nav.end_capital.cummax()
        nav["drawdown"] = nav.end_capital / nav.peak_capital - 1
    return nav, pd.DataFrame(trades)


def main() -> None:
    parser = argparse.ArgumentParser(description="Use the saved 66-stock-trained Ranker models on the external 40-stock file.")
    parser.add_argument("--test-file", required=True, type=Path)
    parser.add_argument("--model-dir", default=Path("models"), type=Path)
    parser.add_argument("--output-dir", default=Path("outputs"), type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    test = load_test(args.test_file)
    pred = predict(test, args.model_dir)
    nav, trades = simulate(pred)
    pred.to_csv(args.output_dir / "external_test_predictions.csv", index=False)
    nav.to_csv(args.output_dir / "weekly_nav.csv", index=False)
    trades.to_csv(args.output_dir / "trade_ledger.csv", index=False)
    print(f"Predictions: {len(pred):,} rows; {pred.ticker.nunique()} external test stocks")
    print(f"Simulation weeks: {len(nav):,}; final capital: {nav.end_capital.iloc[-1]:.2f}" if not nav.empty else "No simulation rows")


if __name__ == "__main__":
    main()
