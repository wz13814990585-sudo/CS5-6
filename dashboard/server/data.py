"""Load immutable, hash-verified replay snapshots. Never execute model code."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

DOWNLOADS = {
    "predictions": "saved_model_predictions.csv",
    "equity": "backtest/weekly_capital.csv",
    "summary": "backtest/summary.csv",
    "prediction-verification": "prediction_verification.json",
    "backtest-verification": "backtest/verification.json",
}
STRING_COLUMNS = {
    "date",
    "ticker",
    "model",
    "scope",
    "window",
    "strategy",
    "first_signal",
    "last_signal",
}


def table(content: bytes) -> list[dict]:
    rows = []
    for raw in csv.DictReader(io.StringIO(content.decode("utf-8-sig"))):
        row = {}
        for key, value in raw.items():
            if key in STRING_COLUMNS or key.endswith("_id"):
                row[key] = value
            else:
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError("Non-finite result")
                row[key] = int(number) if number.is_integer() else number
        rows.append(row)
    return rows


@dataclass
class Replay:
    info: dict
    overview: dict
    equity: list[dict]
    rankings: dict[str, list[dict]]
    downloads: dict[str, bytes]


def load_replay(folder: Path, run_id: str, delivered: bool = False) -> Replay:
    folder = folder.resolve(strict=True)
    manifest_bytes = (folder / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (
        manifest.get("status") != "passed"
        or manifest.get("mode") != "frozen_model_inference"
    ):
        raise ValueError("Not a passed frozen replay")
    if manifest.get("stage") != "complete":
        raise ValueError("Incomplete replay")
    files = manifest["files"]
    if not set(DOWNLOADS.values()).issubset(files):
        raise ValueError("Missing result artifacts")
    verified = {}
    for name, expected in files.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", name):
            raise ValueError("Unsafe artifact name")
        if name.startswith("/") or any(p in ("", ".", "..") for p in name.split("/")):
            raise ValueError("Unsafe artifact path")
        path = (folder / name).resolve(strict=True)
        if not path.is_relative_to(folder) or not path.is_file():
            raise ValueError("Artifact escapes result folder")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("Result hash mismatch")
        verified[name] = content
    for name in ("prediction_verification.json", "backtest/verification.json"):
        if json.loads(verified[name]).get("status") != "passed":
            raise ValueError("Verification did not pass")
    summaries = table(verified[DOWNLOADS["summary"]])
    equity = table(verified[DOWNLOADS["equity"]])
    predictions = table(verified[DOWNLOADS["predictions"]])
    if len(summaries) != 1 or len(predictions) != manifest["prediction_rows"]:
        raise ValueError("Unexpected result coverage")
    summary = summaries[0]
    if len(equity) != summary["weeks"] or not equity:
        raise ValueError("Unexpected backtest coverage")
    if equity != sorted(equity, key=lambda r: r["date"]) or len(
        {r["date"] for r in equity}
    ) != len(equity):
        raise ValueError("Invalid equity calendar")
    rankings: dict[str, list[dict]] = {}
    keys = set()
    for row in predictions:
        date.fromisoformat(row["date"])
        key = row["date"], row["ticker"]
        if key in keys:
            raise ValueError("Duplicate prediction")
        keys.add(key)
        rankings.setdefault(row["date"], []).append(row)
    if len(rankings) != manifest["prediction_weeks"]:
        raise ValueError("Unexpected prediction calendar")
    for rows in rankings.values():
        rows.sort(key=lambda r: r["ensemble_predicted_rank"])
        if [r["ensemble_predicted_rank"] for r in rows] != list(
            range(1, len(rows) + 1)
        ):
            raise ValueError("Invalid prediction ranks")
    peak = summary["initial_capital"]
    for row in equity:
        date.fromisoformat(row["date"])
        peak = max(peak, row["end_capital"])
        row["drawdown"] = row["end_capital"] / peak - 1
    finished = manifest["finished_utc"]
    datetime.fromisoformat(finished.replace("Z", "+00:00"))
    info = {
        "id": run_id,
        "label": "随项目交付的验证结果" if delivered else "本地历史回放",
        "finished_utc": finished,
        "status": "passed",
        "models_loaded": manifest["models_loaded"],
        "prediction_rows": len(predictions),
        "prediction_weeks": len(rankings),
        "backtest_weeks": len(equity),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }
    overview = {
        "run": info,
        "summary": summary,
        "dates": sorted(rankings),
        "prediction_first_date": min(rankings),
        "prediction_last_date": max(rankings),
        "ticker_count": len({r["ticker"] for r in predictions}),
        "ranking_notice": "策略过滤前的模型排名，不是实际持仓或买卖指令。",
    }
    downloads = {kind: verified[name] for kind, name in DOWNLOADS.items()}
    downloads["manifest"] = manifest_bytes
    return Replay(info, overview, equity, rankings, downloads)


def discover(root: Path, explicit: Path | None = None) -> tuple[dict[str, Replay], int]:
    if explicit is not None:
        # Explicit configuration is fail-closed, never silently substitutes another run.
        return {"configured": load_replay(explicit, "configured")}, 0
    candidates = [
        (
            "delivered",
            root / "FINAL_OUTPUTS/01_saved_model_replay/verified_replay",
            True,
        )
    ]
    runs = root / "runs"
    if runs.is_dir():
        for folder in sorted(runs.iterdir()):
            if (
                folder.is_dir()
                and not folder.is_symlink()
                and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", folder.name)
            ):
                candidates.append((folder.name, folder, False))
    valid = {}
    rejected = 0
    for run_id, folder, delivered in candidates:
        try:
            # Training and checks directories are outside this API's scope.
            manifest = json.loads((folder / "manifest.json").read_bytes())
            if manifest.get("mode") != "frozen_model_inference":
                continue
            replay = load_replay(folder, run_id, delivered)
            valid[run_id] = replay
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            if (folder / "manifest.json").exists():
                rejected += 1
    return dict(
        sorted(
            valid.items(), key=lambda item: item[1].info["finished_utc"], reverse=True
        )
    ), rejected
