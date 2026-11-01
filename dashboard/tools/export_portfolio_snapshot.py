"""Export existing historical holdings using the unchanged research backtest engine.

Run with the pinned model environment, not the lightweight web environment.
Never trains models or changes original research artifacts.
"""

from pathlib import Path
import sys
import hashlib
import json
import io
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
import numpy as np
from run_legacy_ensemble_backtest import load_engine, ENGINE_PATH
from pipeline.trading import independent_case
from dashboard.server.data import discover
from dashboard.server.inputs import load_source, bind

DEST = ROOT / "dashboard/data/cs5_6_equity"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def source_key(replay):
    return digest(
        "|".join(
            digest(replay.downloads[k]) for k in ("predictions", "equity", "summary")
        ).encode()
    )


def main():
    source = load_source(ROOT)
    engine = load_engine()
    train_path = ROOT / "external_validation/ensemble_ranker/inputs/train66.csv"
    training = sorted(
        pd.read_csv(train_path, usecols=["ticker"]).ticker.unique().tolist()
    )
    external = sorted({r["ticker"] for r in source.tables["factors"]})
    if len(training) != 66 or len(external) != 40 or set(training) & set(external):
        raise ValueError("Unexpected or overlapping training and external universes")
    prices = pd.read_csv(
        io.BytesIO(source.content["prices"]),
        parse_dates=["date"],
        float_precision="round_trip",
    )
    companies = {r["ticker"]: r["stock_name"] for r in source.tables["factors"]}
    snapshots = {}
    for run_id, replay in discover(ROOT)[0].items():
        bind(source, replay)
        key = source_key(replay)
        if key in snapshots:
            continue
        summary = replay.overview["summary"]
        if summary["strategy"] != "Top5_NoLoss13w" or summary["weeks"] != 210:
            raise ValueError("Unsupported research strategy or period")
        frozen = pd.read_csv(
            io.BytesIO(replay.downloads["predictions"]),
            parse_dates=["date"],
            float_precision="round_trip",
        )
        prediction = frozen[
            (frozen.date >= summary["first_signal"])
            & (frozen.date <= summary["last_signal"])
        ][["date", "ticker", "ensemble_ranking_score"]].rename(
            columns={"ensemble_ranking_score": "prediction"}
        )
        _, _, groups, calendar, context = engine.prepare(
            raw_frame=prices, prediction_frame=prediction
        )
        weekly, orders, holdings = engine.execute(
            calendar,
            groups,
            context,
            summary["strategy"],
            summary["initial_capital"],
            summary["cost_bps"],
            detail=True,
        )
        metrics = engine.performance(weekly, summary["initial_capital"])
        checks = independent_case(
            SimpleNamespace(
                **{
                    **metrics,
                    "capital": summary["initial_capital"],
                    "cost_bps": summary["cost_bps"],
                    "strategy": summary["strategy"],
                }
            ),
            weekly,
            orders,
            holdings,
            prices,
            prediction,
        )
        expected = pd.read_csv(
            io.BytesIO(replay.downloads["equity"]),
            parse_dates=["date"],
            float_precision="round_trip",
        )
        if weekly.date.tolist() != expected.date.tolist():
            raise ValueError("Replayed calendar differs")
        maximum_error = 0.0
        for col in (
            "start_capital",
            "end_capital",
            "net_return",
            "cash",
            "cash_ratio",
            "fees",
            "holdings",
            "shares",
        ):
            error = float(
                np.max(np.abs(weekly[col].to_numpy() - expected[col].to_numpy()))
            )
            maximum_error = max(maximum_error, error)
            if error > 1e-8:
                raise ValueError(f"Original result changed: {col}: {error}")
        for field in (
            "annualized_return",
            "total_return",
            "max_drawdown",
            "final_capital",
            "total_fees",
        ):
            if abs(metrics[field] - summary[field]) > 1e-8:
                raise ValueError(f"Metric differs: {field}")
        dates = {}
        for w in weekly.itertuples(index=False):
            date = w.date.strftime("%Y-%m-%d")
            h = holdings[holdings.date == w.date]
            opening_value = float(sum(h.shares * h.buy_proxy) + w.cash)
            ranks = {
                r["ticker"]: r["ensemble_predicted_rank"] for r in replay.rankings[date]
            }
            selected = engine.target_weights(
                summary["strategy"], groups[w.date], {}, w.date, context
            )
            held_by_ticker = {row.ticker: row for row in h.itertuples(index=False)}
            rows = []
            for ticker, target in selected.items():
                row = held_by_ticker.get(ticker)
                shares = int(row.shares) if row else 0
                price = float(context["open"][w.date][ticker])
                rows.append(
                    dict(
                        ticker=ticker,
                        stock_name=companies[ticker],
                        model_rank=ranks[ticker],
                        target_weight=float(target),
                        actual_weight=shares * price / opening_value,
                        shares=shares,
                        execution_price_proxy=price,
                        market_value_at_open=shares * price,
                    )
                )
            cash_weight = float(w.cash / opening_value)
            if abs(sum(r["actual_weight"] for r in rows) + cash_weight - 1) > 1e-10:
                raise ValueError("Allocation does not reconcile")
            dates[date] = dict(
                rows=rows,
                cash_weight=cash_weight,
                cash=float(w.cash),
                post_trade_open_value=opening_value,
                liquidated_at_period_end=bool(w.forced_window_liquidation),
            )
        snapshots[key] = {
            "source_hashes": {
                k: digest(replay.downloads[k])
                for k in ("predictions", "equity", "summary")
            },
            "input_hashes": source.hashes,
            "dates": dates,
            "verification": {
                "status": "passed",
                "maximum_weekly_error": maximum_error,
                "independent_accounting_checks": checks["checks"],
                "maximum_accounting_error": checks["maximum_absolute_error"],
            },
        }
    payload = {
        "module_id": "cs5_6_equity",
        "schema_version": 1,
        "training_tickers": training,
        "external_tickers": external,
        "training_file_sha256": digest(train_path.read_bytes()),
        "engine_sha256": digest(ENGINE_PATH.read_bytes()),
        "snapshots": snapshots,
    }
    content = (
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode()
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "portfolio.json").write_bytes(content)
    (DEST / "manifest.json").write_text(
        json.dumps(
            {
                "module_id": "cs5_6_equity",
                "schema_version": 1,
                "portfolio_sha256": digest(content),
                "bytes": len(content),
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "snapshots": len(snapshots),
                "signal_weeks_each": [len(v["dates"]) for v in snapshots.values()],
                "checks": [v["verification"] for v in snapshots.values()],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
