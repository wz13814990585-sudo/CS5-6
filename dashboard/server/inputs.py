"""Read original inputs only when their recorded identities match a replay."""

from dataclasses import dataclass
import csv
import hashlib
import io
import json
import math
from pathlib import Path

INPUT_FILES = {
    "factors": "external_validation/ensemble_ranker/inputs/test40.csv",
    "prices": "external_validation/shared_inputs/inputs/test40_with_prices.csv",
    "configuration": "external_validation/ensemble_ranker/model_configuration.json",
    "manifest": "external_validation/ensemble_ranker/saved_models_manifest.json",
}
LABELS = {
    "date": "Signal date",
    "ticker": "Ticker",
    "stock_name": "Company name",
    "revenue_growth_yoy": "Revenue growth YoY",
    "operating_profitability": "Operating profitability",
    "cashflow_to_assets": "Cash flow / assets",
    "debt_to_assets": "Debt / assets",
    "asset_growth_yoy": "Asset growth YoY",
    "buy_price": "Next-week open proxy",
    "sell_price": "Next-week close proxy",
}


@dataclass
class InputSource:
    content: dict[str, bytes]
    hashes: dict[str, str]
    configuration: dict
    tables: dict[str, list[dict]]
    columns: dict[str, list[str]]
    source_columns: dict[str, list[str]]
    dates: dict[str, list[str]]


def load_source(root: Path) -> InputSource:
    root = root.resolve()
    content = {}
    for key, name in INPUT_FILES.items():
        p = (root / name).resolve(strict=True)
        if not p.is_relative_to(root) or not p.is_file():
            raise ValueError("Unsafe input location")
        content[key] = p.read_bytes()
    hashes = {key: hashlib.sha256(value).hexdigest() for key, value in content.items()}
    manifest = json.loads(content["manifest"])
    for key, relative in [
        ("factors", "inputs/test40.csv"),
        ("configuration", "model_configuration.json"),
    ]:
        if hashes[key] != manifest["files"][relative]:
            raise ValueError("Input identity mismatch")
    configuration = json.loads(content["configuration"])
    features = list(
        dict.fromkeys(
            f
            for component in configuration["components"]
            for f in component["features"]
        )
    )
    columns = {
        "factors": ["date", "ticker", "stock_name", *features],
        "prices": ["date", "ticker", "stock_name", "buy_price", "sell_price"],
    }
    tables = {}
    source_columns = {}
    dates = {}
    for dataset in ("factors", "prices"):
        reader = csv.DictReader(io.StringIO(content[dataset].decode("utf-8-sig")))
        source_columns[dataset] = reader.fieldnames
        if not set(columns[dataset]).issubset(reader.fieldnames or []):
            raise ValueError("Input columns missing")
        rows = []
        keys = set()
        for original in reader:
            key = (original["date"], original["ticker"])
            if key in keys:
                raise ValueError("Duplicate input key")
            keys.add(key)
            row = {}
            for name in columns[dataset]:
                if name in ("date", "ticker", "stock_name"):
                    row[name] = original[name]
                else:
                    row[name] = float(original[name])
                    if not math.isfinite(row[name]):
                        raise ValueError("Invalid input value")
            rows.append(row)
        tables[dataset] = sorted(
            rows, key=lambda r: (-int(r["date"].replace("-", "")), r["ticker"])
        )
        dates[dataset] = sorted({r["date"] for r in rows})
    return InputSource(
        content, hashes, configuration, tables, columns, source_columns, dates
    )


def bind(source: InputSource, replay) -> dict:
    prediction = json.loads(replay.downloads["prediction-verification"])
    backtest = json.loads(replay.downloads["backtest-verification"])
    if (
        prediction.get("manifest_sha256") != source.hashes["manifest"]
        or backtest.get("price_sha256") != source.hashes["prices"]
    ):
        raise ValueError("Input identities do not match selected replay")
    predicted = {
        (date, row["ticker"]) for date, rows in replay.rankings.items() for row in rows
    }
    factor_keys = {(row["date"], row["ticker"]) for row in source.tables["factors"]}
    if not predicted.issubset(factor_keys):
        raise ValueError("Inputs do not cover predictions")
    backtest_dates = {row["date"] for row in replay.equity}
    expected_price_keys = {key for key in predicted if key[0] in backtest_dates}
    if not expected_price_keys.issubset(
        {(r["date"], r["ticker"]) for r in source.tables["prices"]}
    ):
        raise ValueError("Inputs do not cover backtest")
    aligned = {
        "factors": [
            r for r in source.tables["factors"] if (r["date"], r["ticker"]) in predicted
        ],
        "prices": [
            r
            for r in source.tables["prices"]
            if (r["date"], r["ticker"]) in expected_price_keys
        ],
    }
    datasets = []
    for key, title, purpose in [
        (
            "factors",
            "Model factor inputs",
            "Raw factors are converted to within-week stock percentiles before entering the model. Research labels are not used for prediction.",
        ),
        (
            "prices",
            "Backtest price inputs",
            "Next-week open/close price proxies are used for historical simulation. Earlier dates may also support the 13-week lookback filter.",
        ),
    ]:
        rows = source.tables[key]
        datasets.append(
            {
                "id": key,
                "title": title,
                "purpose": purpose,
                "source_file": INPUT_FILES[key],
                "sha256": source.hashes[key],
                "bytes": len(source.content[key]),
                "source_rows": len(rows),
                "source_dates": source.dates[key],
                "output_aligned_rows": len(aligned[key]),
                "output_dates": sorted({r["date"] for r in aligned[key]}),
                "ticker_count": len({r["ticker"] for r in rows}),
                "columns": [
                    {
                        "key": name,
                        "label": LABELS.get(name, name),
                        "type": "string"
                        if name in ("date", "ticker", "stock_name")
                        else "number",
                    }
                    for name in source.columns[key]
                ],
                "source_columns": source.source_columns[key],
                "omitted_columns": [
                    name
                    for name in source.source_columns[key]
                    if name not in source.columns[key]
                ],
            }
        )
    return {
        "source": source,
        "aligned": aligned,
        "catalog": {
            "available": True,
            "reason": None,
            "run_id": replay.info["id"],
            "datasets": datasets,
            "model": {
                "component_count": len(source.configuration["components"]),
                "snapshot_count": replay.info["models_loaded"],
                "manifest_sha256": source.hashes["manifest"],
                "configuration_sha256": source.hashes["configuration"],
                "feature_transform": source.configuration["feature_transform"],
            },
        },
    }
