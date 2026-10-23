from pathlib import Path
import ast, hashlib, json, sys
ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "工程文件清单.json").read_text())
for row in manifest["files"]:
    p = ROOT / row["path"]
    assert p.is_file(), f"Missing file: {p}"
    assert p.stat().st_size == row["bytes"], f"Size differs: {p}"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == row["sha256"], f"Hash differs: {p}"
for name in ["integer_backtest.py", "run_all.py", "ensemble_extension/complete_ensemble.py", "ensemble_extension/evaluate_extension.py", "ensemble_extension/verify_extension.py", "ensemble_extension/source/code/ranker_core.py", "ensemble_extension/source/code/prediction_helpers.py", "inputs/test40_with_prices.csv", "ensemble_extension/source/model_configuration.json"]:
    assert (ROOT / name).is_file(), name
npython = 0
for p in ROOT.rglob("*.py"):
    ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))
    npython += 1
assert len(list((ROOT / "ensemble_extension/source/models").glob("*.json"))) == 45
assert len(list((ROOT / "source/models").glob("five_factor_ranker_refit_*.json"))) == 9
import numpy, pandas, xgboost
from verify_integer import synthetic
synthetic()
print(json.dumps(dict(status="passed", files_checked=len(manifest["files"]), python_syntax_checked=npython, ensemble_weights=45, standalone_new_weights=9, integer_boundary_checks="passed", versions=dict(numpy=numpy.__version__,pandas=pandas.__version__,xgboost=xgboost.__version__)), ensure_ascii=False, indent=2))
