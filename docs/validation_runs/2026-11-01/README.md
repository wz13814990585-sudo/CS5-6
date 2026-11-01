# Validation evidence: 2026-11-01

These records come from actual local runs of the checked-in runtime on macOS with the pinned dependencies. All four recorded commands exited successfully. Machine-specific project prefixes in archived JSON and console logs are replaced with `<project>/`; hashes and numerical values are unchanged.

- `commands.json`: commands, exit codes and measured execution times.
- `environment.json`: installed controlled runtime and required processed inputs.
- `regression.log`: all 87 regression tests passed, with no skips.
- `frozen_replay_manifest.json`, `prediction_verification.json`, `backtest_verification.json`: complete historical replay and independent accounting results.
- `training_manifest.json`, `training_data_audit.json`, `training_model_manifest.json`: preparation, all 45 newly fitted component models and their hashes/save-load verification.
- `frozen_replay.log`, `training_full.log`: command output.

Generated CSVs and newly trained model files remain in the local `runs/validation_20261101_replay/` and `runs/validation_20261101_training/` directories, excluded from Git. The manifest hashes identify them. No new training weights replace the frozen strategy snapshots. Original delivered evidence under `FINAL_OUTPUTS/` is unchanged. Re-run the commands with a new run ID to create a fresh independent check.
