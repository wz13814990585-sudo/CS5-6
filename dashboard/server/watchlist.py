"""Read-only joins for presentation watchlists. Never alter a research universe."""

import csv
import io
import json

from .portfolio import MODULE_ID, MODULE_VERSION, contract

FEATURES = (
    "revenue_growth_yoy",
    "operating_profitability",
    "cashflow_to_assets",
    "debt_to_assets",
    "asset_growth_yoy",
)


def stock_catalog(replay, inputs):
    tickers = sorted({r["ticker"] for rows in replay.rankings.values() for r in rows})
    names = {}
    if inputs:
        for row in inputs["source"].tables["factors"]:
            names.setdefault(row["ticker"], row["stock_name"])
    dates = [r["date"] for r in replay.equity]
    return {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "run_id": replay.info["id"],
        "stocks": [
            {"ticker": ticker, "stock_name": names.get(ticker)} for ticker in tickers
        ],
        "backtest_dates": dates,
        "ranking_dates": sorted(replay.rankings),
        "default_date": dates[-1],
        "watchlist_changes_strategy": False,
    }


def normalize_tickers(raw, supported):
    values = list(dict.fromkeys(x.strip().upper() for x in raw.split(",") if x.strip()))
    if not values:
        raise ValueError("Select at least one supported stock.")
    if len(values) > len(supported):
        raise ValueError("Too many stocks for this research universe.")
    unknown = [x for x in values if x not in supported]
    if unknown:
        raise ValueError("Unsupported stocks: " + ", ".join(unknown))
    return values


def inspect_stocks(replay, inputs, archive, date, tickers):
    portfolio = contract(replay, inputs, archive, date)
    catalog = stock_catalog(replay, inputs)
    names = {r["ticker"]: r["stock_name"] for r in catalog["stocks"]}
    requested = normalize_tickers(tickers, names)
    rankings = {r["ticker"]: r for r in replay.rankings.get(date, [])}
    allocation = portfolio["allocation"]
    holdings = {r["ticker"]: r for r in allocation["rows"]}
    tables = {
        dataset: {
            r["ticker"]: r for r in inputs["aligned"][dataset] if r["date"] == date
        }
        if inputs
        else {}
        for dataset in ("factors", "prices")
    }
    rows = []
    for ticker in requested:
        factor, price = tables["factors"].get(ticker), tables["prices"].get(ticker)
        ranking = rankings.get(ticker)
        selection = (
            allocation["status"]
            if allocation["status"] != "available"
            else "no_data"
            if ranking is None
            else "selected"
            if ticker in holdings
            else "not_selected"
        )
        rows.append(
            {
                "ticker": ticker,
                "stock_name": (factor or price or {}).get("stock_name", names[ticker]),
                "factors_status": "unavailable"
                if inputs is None
                else "available"
                if factor
                else "no_data",
                "factors": {key: factor[key] for key in FEATURES} if factor else None,
                "prices_status": "unavailable"
                if inputs is None
                else "available"
                if price
                else "no_data",
                "prices": {key: price[key] for key in ("buy_price", "sell_price")}
                if price
                else None,
                "ranking": ranking,
                "selection_status": selection,
                "allocation": holdings.get(ticker) if selection == "selected" else None,
                # Saved outputs do not contain per-stock rejection reasons.
                "exclusion_reason": None,
            }
        )
    status = (
        "no_data"
        if not any(r["ranking"] for r in rows)
        else (
            "success"
            if all(
                r["ranking"]
                and r["factors"]
                and r["prices"]
                and r["selection_status"] in ("selected", "not_selected")
                for r in rows
            )
            else "partial"
        )
    )
    return {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "run_id": replay.info["id"],
        "signal_date": date,
        "status": status,
        "data_mode": "historical_simulation",
        "requested_tickers": requested,
        "supported_stock_count": len(names),
        "watchlist_changes_strategy": False,
        "rows": rows,
        "strategy_context": {
            "strategy": portfolio["strategy"],
            "metrics_scope": "original_strategy_full_backtest",
            "metrics": portfolio["metrics"],
            "backtest": {
                k: v for k, v in portfolio["backtest"].items() if k != "dates"
            },
            "allocation_status": allocation["status"],
            "liquidated_at_period_end": allocation["liquidated_at_period_end"],
            "units": portfolio["units"],
            "assumptions": portfolio["assumptions"],
        },
        "provenance": {
            **portfolio["provenance"],
            "input_hashes": inputs["source"].hashes if inputs else None,
        },
    }


def export_stocks(result, format):
    if format == "json":
        return (
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        ).encode()
    fields = [
        "module_id",
        "module_version",
        "run_id",
        "signal_date",
        "ticker",
        "stock_name",
        "selection_status",
        "ensemble_predicted_rank",
        "ensemble_ranking_score",
        "model_1_percentile",
        "model_2_percentile",
        "model_3_percentile",
        "factors_status",
        *FEATURES,
        "prices_status",
        "buy_price",
        "sell_price",
        "target_weight",
        "actual_weight",
        "shares",
        "exclusion_reason",
        "strategy_id",
        "watchlist_changes_strategy",
        "weight_units",
        "currency",
        "predictions_sha256",
        "factors_sha256",
        "prices_sha256",
        "allocation_sha256",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    p = result["provenance"]
    for row in result["rows"]:
        flat = {
            **{
                k: result[k]
                for k in ("module_id", "module_version", "run_id", "signal_date")
            },
            **{
                k: row[k]
                for k in (
                    "ticker",
                    "stock_name",
                    "selection_status",
                    "factors_status",
                    "prices_status",
                    "exclusion_reason",
                )
            },
            **{k: v for k, v in (row["ranking"] or {}).items() if k in fields},
            **(row["factors"] or {}),
            **(row["prices"] or {}),
            **{
                k: (row["allocation"] or {}).get(k)
                for k in ("target_weight", "actual_weight", "shares")
            },
            "strategy_id": result["strategy_context"]["strategy"]["id"],
            "watchlist_changes_strategy": False,
            "weight_units": "decimal_fraction",
            "currency": result["strategy_context"]["units"]["currency"],
            "predictions_sha256": p["source_hashes"]["predictions"],
            "factors_sha256": (p.get("input_hashes") or {}).get("factors"),
            "prices_sha256": (p.get("input_hashes") or {}).get("prices"),
            "allocation_sha256": p["allocation_artifact_sha256"],
        }
        # Keep CSV strings literal if a future company name resembles a formula.
        writer.writerow(
            {
                k: "'" + v
                if isinstance(v, str) and v.startswith(("=", "+", "-", "@"))
                else v
                for k, v in flat.items()
            }
        )
    return stream.getvalue().encode("utf-8-sig")
