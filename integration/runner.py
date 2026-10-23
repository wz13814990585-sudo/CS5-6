"""Call preserved source scripts with explicit paths; never alter model rules."""
import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'random_forest': ('random_forest_standard_6y_26w.py', 'random_forest_5_7_11_45_6y26w_results.csv'),
    'ridge': ('train_ridge_5_7_11_45_6y26w.py', 'ridge_5_7_11_45_6y26w_results.csv'),
    'xgboost': ('train_xgboost_5_7_11_45_6y26w.py', 'xgboost_5_7_11_45_6y26w_results.csv'),
    'xgboost_ranker': ('train_xgboostranker_optimized.py', 'xgboostranker_optimized_results.csv'),
}
DATA_SCRIPTS = {'download': 'fetch_and_clean.py', 'technical': 'build_technical_factors.py',
                'external': 'build_external_factors.py'}
BASELINE = 'reference_results/xgboost_ranker/baseline_results.csv'
MODEL_DATA = 'data/test_45_factors_weekly.csv'
REQUIRED = {
    'random_forest': ['numpy', 'pandas', 'scipy', 'scikit-learn'],
    'ridge': ['numpy', 'pandas'],
    'xgboost': ['numpy', 'pandas', 'scipy', 'scikit-learn', 'xgboost'],
    'xgboost_ranker': ['numpy', 'pandas', 'scipy', 'scikit-learn', 'xgboost'],
    'download': ['numpy', 'pandas', 'yfinance'],
    'technical': ['numpy', 'pandas', 'exchange-calendars'],
    'external': ['numpy', 'pandas', 'exchange-calendars'],
}

def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def source_manifest(root):
    return json.loads((root / 'integration/source_manifest.json').read_text(encoding='utf-8'))

def source_path(root, rel):
    relative = PurePosixPath(rel)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Invalid source path: ' + str(rel))
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Source path escapes project: ' + str(rel))
    return path

def verify_sources(root):
    errors, checked = [], 0
    for record in source_manifest(root)['files']:
        rel = record['path']
        try:
            path = source_path(root, rel)
            if not path.is_file():
                errors.append(rel + ': missing file')
            elif sha(path) != record['sha256']:
                errors.append(rel + ': SHA256 differs from confirmed source')
            else:
                checked += 1
        except (OSError, ValueError) as exc:
            errors.append(rel + ': ' + str(exc))
    return {'ok': not errors, 'checked_files': checked, 'errors': errors}

def require_sources(root):
    result = verify_sources(root)
    if not result['ok']:
        raise ValueError('Original file verification failed: ' + '; '.join(result['errors']))
    return result

def inspect_data(root):
    expected = source_manifest(root)['data_facts']
    keys, stocks, dates = set(), set(), set()
    with (root / MODEL_DATA).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected['columns']:
            raise ValueError('Model input columns/order do not match the confirmed snapshot')
        for number, row in enumerate(reader, start=2):
            if None in row or any(v is None or not v.strip() for v in row.values()):
                raise ValueError(f'Missing/malformed CSV values at line {number}')
            datetime.strptime(row['date'], '%Y-%m-%d')
            key = (row['date'], row['ticker'])
            if key in keys:
                raise ValueError(f'Duplicate date+ticker at line {number}: {key}')
            for name, value in row.items():
                if name not in ('date', 'ticker') and not math.isfinite(float(value)):
                    raise ValueError(f'Non-finite {name} at line {number}')
            keys.add(key)
            stocks.add(row['ticker'])
            dates.add(row['date'])
    facts = {'rows': len(keys), 'columns': reader.fieldnames, 'stocks': len(stocks),
             'weeks': len(dates), 'first_date': min(dates), 'last_date': max(dates)}
    if facts != expected:
        raise ValueError('Model data statistics differ from the confirmed snapshot')
    return facts

def static_check(root):
    result = require_sources(root)
    scripts = [r['path'] for r in source_manifest(root)['files'] if r['path'].endswith('.py')]
    for rel in scripts:
        ast.parse((root / rel).read_text(encoding='utf-8-sig'), filename=rel)
    result.update({'source_scripts_parsed': len(scripts), 'data': inspect_data(root),
                   'models_executed': False, 'network_accessed': False,
                   'scope': 'Original hashes, Python syntax, input schema/counts/finite values/unique keys only; no metric or training verification',
                   'selection_boundary_unified': False})
    return result

def dependency_versions():
    versions = {}
    for name in sorted({name for names in REQUIRED.values() for name in names}):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions

def require_dependencies(modules):
    versions = dependency_versions()
    missing = sorted({name for module in modules for name in REQUIRED[module] if versions[name] is None})
    if missing:
        raise ValueError('Missing dependencies in this Python environment: ' + ', '.join(missing) + '. See requirements files; nothing installed automatically.')
    if 'xgboost_ranker' in modules and int(versions['xgboost'].split('.')[0]) < 2:
        raise ValueError('The supplied Ranker requires xgboost >= 2')
    return versions

def safe_output(root, value=None):
    root = root.resolve()
    anchor = root / 'runs'
    if anchor.is_symlink():
        raise ValueError('runs/ must not be a symbolic link')
    value = value or ('runs/run_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    raw = Path(value)
    path = (raw if raw.is_absolute() else root / raw)
    if path.exists() or path.is_symlink():
        raise FileExistsError('Output must be a new directory: ' + str(path))
    path = path.resolve()
    if path == anchor or not path.is_relative_to(anchor):
        raise ValueError('Output must be a new child of this project\'s runs/ directory')
    # Refuse even aliases pointing back inside runs; execution paths stay explicit.
    for parent in (raw if raw.is_absolute() else root / raw).parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError('Output parents must not be symbolic links')
    return path

def build_model_commands(root, output, names, python):
    jobs = []
    for name in names:
        script, result = MODELS[name]
        module_dir = output / name
        workspace = module_dir / 'workspace'
        command = [str(python), '-u', str(workspace / script), '--input', str(workspace / 'test_45_factors_weekly.csv')]
        if name == 'xgboost_ranker':
            command += ['--baseline-results', str(workspace / 'baseline_results.csv'),
                        '--run-dir', str(module_dir / 'frozen_run'), '--phase', 'all']
        else:
            command += ['--output', str(module_dir / result), '--feature-set', 'all']
            if name in ('ridge', 'xgboost'):
                command += ['--mode', 'rolling', '--rolling-years', '6']
            if name == 'ridge':
                command += ['--audit-dir', str(module_dir / 'audit')]
        jobs.append({'module': name, 'command': command, 'cwd': str(workspace),
                     'script_source': f'models/{name}/{script}', 'log': str(module_dir / 'run.log')})
    return jobs

def build_data_commands(output, step, python):
    workspace = output / 'workspace'
    steps = list(DATA_SCRIPTS) if step == 'all' else [step]
    return [{'module': name, 'command': [str(python), '-u', str(workspace / DATA_SCRIPTS[name])],
             'cwd': str(workspace), 'script_source': 'data_processing/' + DATA_SCRIPTS[name],
             'log': str(output / (name + '.log'))} for name in steps]

def run_command(command, cwd, log):
    """Stream output to the console and log; preserve a failed child's exit status."""
    with Path(log).open('w', encoding='utf-8') as handle:
        try:
            with subprocess.Popen(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, encoding='utf-8', errors='replace',
                                  env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUNBUFFERED': '1'}) as process:
                for line in process.stdout:
                    print(line, end='', flush=True)
                    handle.write(line)
                    handle.flush()
                return process.wait()
        except OSError as exc:
            message = 'Could not start process: ' + str(exc)
            print(message, file=sys.stderr)
            handle.write(message + '\n')
            return 127

def execute_jobs(root, output, jobs, kind, versions):
    # safe_output was checked before dependency inspection; recheck at creation.
    output = safe_output(root, output)
    output.mkdir(parents=True, exist_ok=False)
    record = {'status': 'running', 'kind': kind, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'python': sys.version, 'executable': sys.executable, 'dependencies': versions,
              'source_manifest_sha256': sha(root / 'integration/source_manifest.json'),
              'input_sha256': sha(root / MODEL_DATA), 'commands': jobs,
              'protocol': source_manifest(root)['protocol'], 'results': [],
              'reference_results_replaced': False}
    path = output / 'run_manifest.json'
    def save():
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save()
    try:
        if kind == 'data':
            workspace = output / 'workspace'
            workspace.mkdir()
            shutil.copytree(root / 'data', workspace / 'data')
            for source in (root / 'data_processing').glob('*.py'):
                shutil.copy2(source, workspace / source.name)
        else:
            for job in jobs:
                workspace = Path(job['cwd'])
                workspace.mkdir(parents=True)
                source = root / job['script_source']
                shutil.copy2(source, workspace / source.name)
                shutil.copy2(root / MODEL_DATA, workspace / 'test_45_factors_weekly.csv')
                if job['module'] == 'xgboost_ranker':
                    shutil.copy2(root / BASELINE, workspace / 'baseline_results.csv')
                # Ridge audit/ and Ranker frozen_run/ must remain absent here.
        for job in jobs:
            code = run_command(job['command'], job['cwd'], job['log'])
            record['results'].append({'module': job['module'], 'exit_code': code, 'log': job['log']})
            save()
            if code != 0:
                record['status'] = 'failed'
                record['finished_utc'] = datetime.now(timezone.utc).isoformat()
                save()
                return code if code > 0 else 1
        record['source_integrity_after'] = require_sources(root)
        record['status'] = 'completed'
        record['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save()
        return 0
    except BaseException as exc:
        record['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        record['error'] = str(exc)
        record['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save()
        raise

def main(argv=None, root=None):
    root = Path(root or ROOT).resolve()
    parser = argparse.ArgumentParser(description='Five confirmed packages: preserve sources; inspect first, explicitly run later.')
    sub = parser.add_subparsers(dest='action')
    for action in ('status', 'verify', 'check'):
        sub.add_parser(action)
    for action in ('plan', 'train'):
        p = sub.add_parser(action)
        p.add_argument('--model', choices=['all', *MODELS], default='all')
        p.add_argument('--output', help='New directory under runs/ (default: timestamp)')
    p = sub.add_parser('data')
    p.add_argument('--step', choices=['all', *DATA_SCRIPTS], required=True)
    p.add_argument('--output', help='New directory under runs/ (default: timestamp)')
    p.add_argument('--dry-run', action='store_true', help='Print commands only; no files or network')
    args = parser.parse_args(argv)
    try:
        if args.action is None:
            parser.print_help()
            return 0
        if args.action == 'status':
            emit({'scope': 'Five confirmed source packages only', 'models': list(MODELS),
                  'protocol': source_manifest(root)['protocol'], 'dependencies': dependency_versions(),
                  'missing_modules': ['single_factor_analysis', 'unified_evaluation_backtest', 'integer_share_simulation'],
                  'training_performed_by_status': False})
            return 0
        if args.action == 'verify':
            result = verify_sources(root)
            emit(result)
            return 0 if result['ok'] else 1
        if args.action == 'check':
            emit(static_check(root))
            return 0
        require_sources(root)
        output = safe_output(root, args.output)
        if args.action in ('plan', 'train'):
            names = list(MODELS) if args.model == 'all' else [args.model]
            jobs = build_model_commands(root, output, names, sys.executable)
            if args.action == 'plan':
                emit({'output': str(output), 'executed': False, 'commands': jobs})
                return 0
            versions = require_dependencies(names)
            return execute_jobs(root, output, jobs, 'training', versions)
        jobs = build_data_commands(output, args.step, sys.executable)
        if args.dry_run:
            emit({'output': str(output), 'executed': False, 'commands': jobs,
                  'note': 'Individual steps start from the confirmed input snapshot; all chains download, technical, external. Canonical data is never replaced.'})
            return 0
        versions = require_dependencies([j['module'] for j in jobs])
        if args.step in ('all', 'external') and not os.environ.get('SEC_USER_AGENT', '').strip():
            raise ValueError('SEC_USER_AGENT is required before external/all data execution; see original source README/comments.')
        return execute_jobs(root, output, jobs, 'data', versions)
    except (OSError, ValueError, KeyError, SyntaxError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
