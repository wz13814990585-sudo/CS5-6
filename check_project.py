"""Read-only integrity checks. Does not import or execute any supplied model code."""
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check(root=ROOT):
    errors = []
    manifest = json.loads((root / 'integration/project_manifest.json').read_text(encoding='utf-8'))
    allowed_extra = {'integration/project_manifest.json', 'integration/static_verification.json'}
    listed = {entry['path'] for entry in manifest['files']}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    for rel in sorted(actual - listed - allowed_extra):
        errors.append('Unregistered file: ' + rel)
    checked = 0
    python_count = 0
    for entry in manifest['files']:
        rel = PurePosixPath(entry['path'])
        if rel.is_absolute() or '..' in rel.parts:
            errors.append('Unsafe manifest path: ' + entry['path'])
            continue
        p = root / rel
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
            errors.append('Unexpected symlink/path: ' + str(rel))
            continue
        if not p.is_file():
            errors.append('Missing: ' + str(rel))
            continue
        if p.stat().st_size != entry['size'] or digest(p) != entry['sha256']:
            errors.append('Changed: ' + str(rel))
        checked += 1
        if p.suffix == '.py':
            try:
                ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(rel))
                python_count += 1
            except (SyntaxError, UnicodeError) as exc:
                errors.append('Syntax/read error: ' + str(rel) + ': ' + str(exc))

    required = [
        'data/test_45_factors_weekly.csv',
        'data/external40/additional_40_five_factors_targets_final.xlsx',
        'factor_analysis/Factor_Analysis.py',
        'external_validation/standalone_ranker/inputs/train66.csv',
        'external_validation/standalone_ranker/inputs/test40_with_prices.csv',
        'external_validation/ensemble_ranker/inputs/train66.csv',
        'external_validation/ensemble_ranker/inputs/test40.csv',
        'backtesting/README.md',
        'backtesting/external40/integer_backtest.py',
        'backtesting/external40/run_all.py',
        'backtesting/external40/ensemble_extension/complete_ensemble.py',
        'backtesting/external40/ensemble_extension/evaluate_extension.py',
        'backtesting/external40/ensemble_extension/verify_extension.py',
        'backtesting/external40/inputs/test40_with_prices.csv',
        'backtesting/external40/prepared/predictions.csv',
        'backtesting/external40/prepared/old50_predictions.csv',
    ]
    for rel in required:
        if not (root / rel).is_file():
            errors.append('Required module input missing: ' + rel)
    single = root / 'external_validation/standalone_ranker'
    ensemble = root / 'external_validation/ensemble_ranker'
    singles = list((single / 'models').glob('five_factor_ranker_refit_*.json'))
    ensembles = list((ensemble / 'models').glob('model_*_refit_*.json'))
    if len(singles) != 9:
        errors.append('Expected 9 standalone refit models')
    if len(ensembles) != 45:
        errors.append('Expected 45 ensemble component/refit models')
    try:
        cfg = json.loads((single / 'models/configuration.json').read_text())
        if cfg['selected_candidate']['n_estimators'] != 150:
            errors.append('Formal standalone candidate must use 150 trees')
        expected_features = ['revenue_growth_yoy', 'operating_profitability', 'cashflow_to_assets', 'debt_to_assets', 'asset_growth_yoy']
        if cfg['features'] != expected_features:
            errors.append('Standalone frozen feature order changed')
        for p in singles:
            model = json.loads(p.read_text())['learner']
            if model['objective']['name'] != 'rank:pairwise':
                errors.append('Unexpected standalone objective: ' + p.name)
            trees = model['gradient_booster']['model']['trees']
            if len(trees) != 150:
                errors.append('Unexpected standalone tree count: ' + p.name)
        if digest(single / 'inputs/train66.csv') != digest(ensemble / 'inputs/train66.csv'):
            errors.append('The two external methods have different train66 input files')
    except (OSError, KeyError, ValueError, TypeError) as exc:
        errors.append('Frozen model metadata check: ' + str(exc))
    backtest = root / 'backtesting/external40'
    frozen_backtest_count = 0
    linked_model_files = 0
    try:
        source_manifest = json.loads((backtest / '工程文件清单.json').read_text())
        for entry in source_manifest['files']:
            rel = PurePosixPath(entry['path'])
            if rel.is_absolute() or '..' in rel.parts:
                errors.append('Unsafe backtest manifest path: ' + str(rel))
                continue
            p = backtest / rel
            if not p.is_file() or p.stat().st_size != entry['bytes'] or digest(p) != entry['sha256']:
                errors.append('Original backtest snapshot mismatch: ' + str(rel))
            frozen_backtest_count += 1
        for local, canonical in [(backtest / 'source', single), (backtest / 'ensemble_extension/source', ensemble)]:
            for p in sorted(local.rglob('*')):
                if not p.is_file():
                    continue
                rel = p.relative_to(local)
                if not (canonical / rel).is_file() or digest(p) != digest(canonical / rel):
                    errors.append('Backtest model asset differs from confirmed version: ' + str(rel))
                linked_model_files += 1
        if frozen_backtest_count != 1395 or linked_model_files != 95:
            errors.append('Unexpected backtest source/model asset count')
        if digest(backtest / 'inputs/test40_with_prices.csv') != digest(single / 'inputs/test40_with_prices.csv'):
            errors.append('Backtest prices differ from confirmed standalone input')
        old = json.loads((backtest / 'old_source/standalone_selection.json').read_text())
        if old['chosen_candidate']['n_estimators'] != 50:
            errors.append('Historical 50-tree control metadata changed')
    except (OSError, KeyError, ValueError, TypeError) as exc:
        errors.append('Backtest static asset check: ' + str(exc))
    return {
        'ok': not errors,
        'checked_files': checked,
        'python_syntax_checked': python_count,
        'standalone_refit_models': len(singles),
        'ensemble_component_refit_models': len(ensembles),
        'backtest_original_manifest_files': frozen_backtest_count,
        'backtest_model_assets_equal_confirmed': linked_model_files,
        'model_code_executed': False,
        'training_prediction_evaluation_backtest_run': False,
        'errors': errors,
    }


if __name__ == '__main__':
    try:
        result = check()
    except (OSError, ValueError, KeyError) as exc:
        result = {'ok': False, 'errors': [str(exc)], 'model_code_executed': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['ok'] else 1)
