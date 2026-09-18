"""Load and validate machine-readable factor-set definitions."""

from __future__ import annotations

import json
from pathlib import Path

from .data import validate_feature_columns


def load_factor_sets(path: Path, available_columns=None) -> dict[str, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sets = {name: item["factors"] for name, item in payload["factor_sets"].items()}
    if available_columns is not None:
        for factors in sets.values():
            validate_feature_columns(factors, available_columns)
    return sets


def save_forward_selected(path: Path, factors: list[str]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["factor_sets"]["forward_selected"] = {
        "factors": factors, "n_features": len(factors),
        "selection_method": "development-only chronological model-based forward selection",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
