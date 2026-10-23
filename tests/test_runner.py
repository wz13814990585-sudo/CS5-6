"""Integration contracts. All subprocess probes are harmless; no model is trained."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT_PATHS = {
    'random_forest': 'models/random_forest/random_forest_standard_6y_26w.py',
    'ridge': 'models/ridge/train_ridge_5_7_11_45_6y26w.py',
    'xgboost': 'models/xgboost/train_xgboost_5_7_11_45_6y26w.py',
    'xgboost_ranker': 'models/xgboost_ranker/train_xgboostranker_optimized.py',
}

def get_runner():
    path = PROJECT / 'integration/runner.py'
    if not path.exists():
        raise AssertionError('The integration launcher has not been implemented')
    spec = importlib.util.spec_from_file_location('integration_runner_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def make_fixture(root, script_overrides=None):
    (root / 'integration').mkdir(parents=True)
    shutil.copy2(PROJECT / 'run.py', root / 'run.py')
    shutil.copy2(PROJECT / 'integration/runner.py', root / 'integration/runner.py')
    marker = root / 'MODEL_WAS_EXECUTED'
    probe = 'from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n'
    members = {path: probe.encode() for path in SCRIPT_PATHS.values()}
    for name in ['fetch_and_clean.py', 'build_technical_factors.py', 'build_external_factors.py', 'collect_sec_fundamentals.py']:
        members['data_processing/' + name] = probe.encode()
    members.update({path: code.encode() for path, code in (script_overrides or {}).items()})
    header = ['date', 'ticker', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'target', 'target2'] + ['f' + str(i) for i in range(45)]
    csv = ','.join(header) + '\n' + ','.join(['2020-01-03', 'AAA'] + ['1'] * 53) + '\n'
    members['data/test_45_factors_weekly.csv'] = csv.encode()
    members['reference_results/xgboost_ranker/baseline_results.csv'] = b'Dataset,Stage\n'
    records = []
    for rel, raw in members.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        records.append({'path': rel, 'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw), 'origins': []})
    manifest = {'format_version': 1, 'files': records, 'archives': [],
                'data_facts': {'rows': 1, 'columns': header, 'stocks': 1, 'weeks': 1,
                               'first_date': '2020-01-03', 'last_date': '2020-01-03'},
                'protocol': {'selection_boundary_unified': False}}
    (root / 'integration/source_manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return marker

class IntegrationTests(unittest.TestCase):
    def test_xgboost_wrappers_require_sklearn_before_starting(self):
        runner = get_runner()
        versions = {name: '2.0.0' for names in runner.REQUIRED.values() for name in names}
        versions['scikit-learn'] = None
        with patch.object(runner, 'dependency_versions', return_value=versions):
            for name in ('xgboost', 'xgboost_ranker'):
                with self.subTest(model=name), self.assertRaisesRegex(ValueError, 'scikit-learn'):
                    runner.require_dependencies([name])

    def test_no_arguments_does_not_start_work(self):
        # A default train action would turn this harmless help request into work.
        result = subprocess.run([sys.executable, str(PROJECT / 'run.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('usage:', result.stdout)

    def test_read_only_commands_never_execute_source_and_work_after_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / '搬移后的 项目'
            marker = make_fixture(root)
            before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            for args in [[], ['--help'], ['status'], ['verify'], ['check'], ['plan', '--model', 'all', '--output', 'runs/future'], ['data', '--step', 'all', '--dry-run', '--output', 'runs/data_future']]:
                result = subprocess.run([sys.executable, str(root / 'run.py'), *args], cwd=tmp,
                                        capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                self.assertEqual(result.returncode, 0, (args, result.stderr))
                self.assertFalse(marker.exists(), args)
            after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before, after)

    def test_model_plans_use_approved_native_arguments(self):
        runner = get_runner()
        jobs = runner.build_model_commands(PROJECT, PROJECT / 'runs/example', list(SCRIPT_PATHS), sys.executable)
        by_name = {j['module']: j['command'] for j in jobs}
        for name in ['ridge', 'xgboost']:
            args = by_name[name]
            self.assertEqual(args[args.index('--mode') + 1], 'rolling')
            self.assertEqual(args[args.index('--rolling-years') + 1], '6')
            self.assertEqual(args[args.index('--feature-set') + 1], 'all')
        rf = by_name['random_forest']
        self.assertEqual(rf[rf.index('--feature-set') + 1], 'all')
        self.assertNotIn('--check-only', rf)
        self.assertNotIn('--mode', rf)
        ranker = by_name['xgboost_ranker']
        self.assertEqual(ranker[ranker.index('--phase') + 1], 'all')
        self.assertNotIn('--feature-set', ranker)
        self.assertNotIn('--rolling-years', ranker)
        for args in by_name.values():
            self.assertEqual(args[1], '-u')
            self.assertTrue(Path(args[2]).is_absolute())
            self.assertTrue(Path(args[args.index('--input') + 1]).is_absolute())

    def test_output_paths_cannot_overwrite_or_escape_runs(self):
        runner = get_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'project'
            root.mkdir()
            (root / 'runs').mkdir()
            (root / 'runs/existing').mkdir()
            (root / 'runs/file').write_text('keep')
            (root / 'data').mkdir()
            (root / 'runs/link').symlink_to(root / 'data', target_is_directory=True)
            for path in ['runs/existing', 'runs/file', 'runs/link/child', 'data/child', '.', '..', str(Path(tmp) / 'outside')]:
                with self.subTest(path=path), self.assertRaises((ValueError, FileExistsError)):
                    runner.safe_output(root, path)
            self.assertEqual(runner.safe_output(root, 'runs/new'), (root / 'runs/new').resolve())
            self.assertFalse((root / 'runs/new').exists())

    def test_changed_or_missing_original_is_rejected(self):
        runner = get_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'project'
            make_fixture(root)
            self.assertTrue(runner.verify_sources(root)['ok'])
            for rel in [SCRIPT_PATHS['ridge'], 'data/test_45_factors_weekly.csv', 'reference_results/xgboost_ranker/baseline_results.csv']:
                p = root / rel
                original = p.read_bytes()
                p.write_bytes(original + b'changed')
                result = runner.verify_sources(root)
                self.assertFalse(result['ok'])
                self.assertIn(rel, json.dumps(result))
                p.write_bytes(original)
            (root / SCRIPT_PATHS['xgboost']).unlink()
            self.assertFalse(runner.verify_sources(root)['ok'])

    def test_failed_process_is_logged_and_exit_code_preserved(self):
        runner = get_runner()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            script = p / 'safe probe.py'
            script.write_text('import sys\nprint("probe failed")\nsys.exit(7)\n')
            code = runner.run_command([sys.executable, str(script)], p, p / 'probe.log')
            self.assertEqual(code, 7)
            self.assertIn('probe failed', (p / 'probe.log').read_text())
            code = runner.run_command([str(p / 'missing-python')], p, p / 'missing.log')
            self.assertNotEqual(code, 0)

    def test_staged_model_execution_preserves_sources_and_creates_fresh_native_outputs(self):
        runner = get_runner()
        # Stand-ins check the real launch arguments and output preconditions.
        # No scientific library or delivered model source is imported.
        probe = '''import sys
from pathlib import Path
args = sys.argv
def value(flag): return Path(args[args.index(flag) + 1])
assert value('--input').is_file()
assert value('--input').parent == Path.cwd()
for flag in ('--audit-dir', '--run-dir'):
    if flag in args:
        path = value(flag)
        assert not path.exists(), 'Native output directory was created too early'
        path.mkdir()
        (path / 'probe.txt').write_text('created by stand-in')
if '--baseline-results' in args:
    assert value('--baseline-results').is_file()
if '--output' in args:
    value('--output').write_text('probe result')
print('safe model stand-in completed')
'''
        with tempfile.TemporaryDirectory() as tmp:
            root = (Path(tmp) / 'project').resolve()
            make_fixture(root, {path: probe for path in SCRIPT_PATHS.values()})
            output = runner.safe_output(root, 'runs/staged')
            jobs = runner.build_model_commands(root, output, list(SCRIPT_PATHS), sys.executable)
            self.assertEqual(runner.execute_jobs(root, output, jobs, 'training', {}), 0)
            record = json.loads((output / 'run_manifest.json').read_text())
            self.assertEqual(record['status'], 'completed')
            self.assertEqual(len(record['results']), 4)
            self.assertTrue(runner.verify_sources(root)['ok'])
            for job in jobs:
                self.assertIn('stand-in completed', Path(job['log']).read_text())
                original = root / job['script_source']
                staged = Path(job['cwd']) / original.name
                self.assertEqual(original.read_bytes(), staged.read_bytes())

    def test_failed_job_stops_following_models_and_records_failure(self):
        runner = get_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = (Path(tmp) / 'project').resolve()
            marker = make_fixture(root, {SCRIPT_PATHS['random_forest']: 'import sys\nprint("intentional failure")\nsys.exit(7)\n'})
            output = runner.safe_output(root, 'runs/failed')
            jobs = runner.build_model_commands(root, output, list(SCRIPT_PATHS), sys.executable)
            self.assertEqual(runner.execute_jobs(root, output, jobs, 'training', {}), 7)
            record = json.loads((output / 'run_manifest.json').read_text())
            self.assertEqual(record['status'], 'failed')
            self.assertEqual(record['results'][0]['exit_code'], 7)
            self.assertEqual(len(record['results']), 1)
            self.assertFalse(marker.exists(), 'A later model ran after failure')
            self.assertTrue(runner.verify_sources(root)['ok'])

    def test_data_steps_share_one_isolated_workspace_in_order(self):
        runner = get_runner()
        with tempfile.TemporaryDirectory() as tmp:
            root = (Path(tmp) / 'project').resolve()
            overrides = {}
            for position, (name, script) in enumerate(runner.DATA_SCRIPTS.items()):
                overrides['data_processing/' + script] = (
                    'from pathlib import Path\n'
                    'assert Path("collect_sec_fundamentals.py").is_file()\n'
                    'assert Path("data/test_45_factors_weekly.csv").is_file()\n'
                    'p = Path("step_order.txt")\n'
                    'steps = p.read_text().splitlines() if p.exists() else []\n'
                    f'assert len(steps) == {position}\n'
                    f'p.write_text("\\n".join(steps + [{name!r}]) + "\\n")\n')
            make_fixture(root, overrides)
            output = runner.safe_output(root, 'runs/data_steps')
            jobs = runner.build_data_commands(output, 'all', sys.executable)
            self.assertEqual(runner.execute_jobs(root, output, jobs, 'data', {}), 0)
            self.assertEqual((output / 'workspace/step_order.txt').read_text().splitlines(), list(runner.DATA_SCRIPTS))
            self.assertFalse((root / 'step_order.txt').exists())
            self.assertTrue(runner.verify_sources(root)['ok'])

    def test_missing_sources_block_train_before_any_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'project'
            marker = make_fixture(root)
            (root / SCRIPT_PATHS['random_forest']).unlink()
            result = subprocess.run([sys.executable, str(root / 'run.py'), 'train', '--model', 'random_forest', '--output', 'runs/blocked'],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(marker.exists())
            self.assertFalse((root / 'runs/blocked').exists())

if __name__ == '__main__':
    unittest.main()
