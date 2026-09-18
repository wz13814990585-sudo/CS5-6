import json

from ml.config import FACTOR_OUTPUT_DIR, TARGET_COLUMN
from ml.factor_sets import load_factor_sets


def test_all_exported_factor_sets_valid_unique_and_clean():
    sets = load_factor_sets(FACTOR_OUTPUT_DIR / "ml_factor_sets.json")
    required = {"core_5", "core_plus_fundamental", "core_plus_horizon", "extended", "strong_only",
                "moderate_and_strong", "top_3", "top_5", "top_8", "top_10", "top_15", "all_eligible"}
    assert required <= set(sets)
    for factors in sets.values():
        assert len(factors) == len(set(factors))
        assert TARGET_COLUMN not in factors
        assert not {"date", "ticker", "open", "close"}.intersection(factors)
        assert not any(f.startswith("macro_") for f in factors)


def test_factor_set_metadata_matches_feature_count():
    payload = json.loads((FACTOR_OUTPUT_DIR / "ml_factor_sets.json").read_text())
    for item in payload["factor_sets"].values():
        assert item["n_features"] == len(item["factors"])
