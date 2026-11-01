"""Isolated cs5_6_equity adapter over immutable research results and offline allocations."""

import hashlib
import json
import math
from pathlib import Path

MODULE_ID = "cs5_6_equity"
MODULE_VERSION = "1.3.0"
API_PREFIX = "/api/cs5_6_equity/v1"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def source_key(replay):
    return digest(
        "|".join(
            digest(replay.downloads[k]) for k in ("predictions", "equity", "summary")
        ).encode()
    )


def load_archive(root: Path):
    directory = root / "dashboard/data/cs5_6_equity"
    for name in ("portfolio.json", "manifest.json"):
        path = directory / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Unsafe portfolio snapshot path")
    content = (directory / "portfolio.json").read_bytes()
    manifest = json.loads((directory / "manifest.json").read_bytes())
    if (
        manifest["module_id"] != MODULE_ID
        or manifest["portfolio_sha256"] != digest(content)
        or manifest["bytes"] != len(content)
    ):
        raise ValueError("Portfolio snapshot hash mismatch")
    archive = json.loads(content)
    if archive["module_id"] != MODULE_ID or archive["schema_version"] != 1:
        raise ValueError("Unsupported portfolio snapshot")
    if (
        len(set(archive["training_tickers"])) != 66
        or len(set(archive["external_tickers"])) != 40
        or set(archive["training_tickers"]) & set(archive["external_tickers"])
    ):
        raise ValueError("Invalid portfolio universes")
    from .schemas import Allocation

    for snapshot in archive["snapshots"].values():
        if snapshot["verification"]["status"] != "passed":
            raise ValueError("Unverified allocation")
        for date, value in snapshot["dates"].items():
            Allocation.model_validate(
                {
                    "status": "available",
                    "reason": None,
                    "signal_date": date,
                    "phase": "after_rebalance_at_next_open_proxy",
                    **value,
                }
            )
            if len({r["ticker"] for r in value["rows"]}) != len(value["rows"]):
                raise ValueError("Duplicate holding")
            if not math.isclose(
                sum(r["actual_weight"] for r in value["rows"]) + value["cash_weight"],
                1,
                abs_tol=1e-10,
            ):
                raise ValueError("Allocation does not reconcile")
    archive["artifact_sha256"] = digest(content)
    return archive


def contract(replay, inputs, archive, requested_date=None):
    summary = replay.overview["summary"]
    dates = [r["date"] for r in replay.equity]
    date = requested_date or dates[-1]
    snapshot = archive["snapshots"].get(source_key(replay)) if archive else None
    matched = bool(
        snapshot and inputs and snapshot["input_hashes"] == inputs["source"].hashes
    )
    available = bool(matched and date in dates and date in snapshot["dates"])
    if date not in dates:
        status, reason = "no_data", "No portfolio backtest exists for this signal date."
    elif not available:
        status, reason = (
            "unavailable",
            "A verified allocation snapshot matching this run and its inputs is unavailable.",
        )
    else:
        status, reason = "available", None
    allocation = {
        "status": status,
        "reason": reason,
        "signal_date": date,
        "phase": "after_rebalance_at_next_open_proxy",
        "rows": [],
        "cash_weight": None,
        "cash": None,
        "post_trade_open_value": None,
        "liquidated_at_period_end": None,
    }
    if available:
        allocation.update(snapshot["dates"][date])
    external = sorted({r["ticker"] for rows in replay.rankings.values() for r in rows})
    actual = sorted(r["ticker"] for r in replay.rankings.get(date, []))
    training = archive["training_tickers"] if matched else None
    return {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "status": "success"
        if available
        else "no_data"
        if status == "no_data"
        else "partial",
        "data_mode": "historical_simulation",
        "run_id": replay.info["id"],
        "model": {
            "id": "frozen_three_component_ensemble",
            "component_count": 3,
            "snapshot_count": replay.info["models_loaded"],
        },
        "strategy": {
            "id": summary["strategy"],
            "signal_frequency": "weekly",
            "maximum_stocks": 5,
            "target_weight_per_stock": 0.2,
        },
        "universe": {
            "training_tickers": training,
            "training_count": len(training) if training is not None else None,
            "external_tickers": external,
            "external_count": len(external),
            "signal_tickers": actual,
            "signal_count": len(actual),
            "asset_class": "equities",
            "includes_etfs": False,
            "shared_asset_selector": False,
        },
        "signal_date": date,
        "data_cutoff": {
            "factor_signal_date": date if actual else None,
            "latest_source_signal_date": inputs["source"].dates["factors"][-1]
            if inputs
            else None,
            "financial_publication_timestamp": None,
            "note": "Dates are dataset signal dates, not independently certified publication or availability timestamps.",
        },
        "backtest": {
            "start": summary["first_signal"],
            "end": summary["last_signal"],
            "weeks": summary["weeks"],
            "dates": dates,
            "scope": summary.get("scope", "Common210"),
            "window": summary.get("window", "FullHistory"),
        },
        "metrics": {
            key: summary[key]
            for key in (
                "annualized_return",
                "total_return",
                "max_drawdown",
                "sharpe",
                "initial_capital",
                "final_capital",
            )
        },
        "units": {
            "returns": "decimal_fraction",
            "weights": "decimal_fraction",
            "capital": "original_research_account_units",
            "currency": None,
            "currency_note": "The source result does not declare a currency code.",
        },
        "benchmark": {
            "status": "unavailable",
            "name": None,
            "annualized_return": None,
            "total_return": None,
            "series": None,
            "reason": "No independently verified benchmark series for this exact universe, period and execution convention is included.",
        },
        "assumptions": {
            "annualization_periods_per_year": 52,
            "annualized_return_formula": "(final_capital / initial_capital) ** (52 / weeks) - 1",
            "cost_bps_per_side": summary["cost_bps"],
            "execution": "next_week_open_close_price_proxies",
            "shares": "integer",
            "filter": "nonnegative_observable_trailing_13_week_return",
            "end_of_window_liquidation": True,
            "guaranteed_future_return": False,
        },
        "allocation": allocation,
        "provenance": {
            "run_manifest_sha256": replay.info["manifest_sha256"],
            "source_hashes": {
                k: digest(replay.downloads[k])
                for k in ("predictions", "equity", "summary")
            },
            "allocation_artifact_sha256": archive["artifact_sha256"]
            if matched
            else None,
            "research_engine_sha256": archive["engine_sha256"] if matched else None,
            "training_file_sha256": archive["training_file_sha256"]
            if matched
            else None,
            "input_hashes": snapshot["input_hashes"] if matched else None,
            "allocation_verification": snapshot["verification"] if matched else None,
            "derivation": "Offline export using the existing research execution engine; no model training or live predictions.",
        },
    }
