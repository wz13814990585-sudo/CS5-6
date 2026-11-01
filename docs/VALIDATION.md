# Validation results

Validation date: **2026-11-01 (Australia/Sydney)**. The current runtime, including the 2026-10-29 input/accounting changes, was executed on **macOS 14.5 arm64, Python 3.12.10** with the pinned project dependencies. See [the machine-readable record](validation_results.json) and [command logs and manifests](validation_runs/2026-11-01/README.md).

## Frozen Ensemble strategy replay

The complete default CLI replay passed in `runs/validation_20261101_replay/`.

- Loaded all 45 original frozen snapshots, trained no models, and checked their recorded hashes.
- Generated 13,517 stock-week predictions across 366 signal weeks. All component/Ensemble scores, percentiles, model IDs and ranks matched the reference exactly; maximum score error was 0.
- Executed only Top5_NoLoss13w / Common210 FullHistory: 210 weeks, initial capital 100,000, 10 bps per side and integer shares.
- Strategy metrics matched the historical reference with maximum absolute error 0.
- Independent selection/account verification passed 9,586 checks; maximum accounting error was 2.842170943040401e-14.
- Verified all six generated output hashes against the passed run manifest.

The original delivered replay under `FINAL_OUTPUTS/01_saved_model_replay/verified_replay/` is unchanged. Its timestamps remain those of the original run. New logs and manifests identify the current validation separately.

## Complete training demonstration

The full training-only CLI passed in `runs/validation_20261101_training/`.

- All three required input files were present and hashed: the corrected weekly panel, training ticker list and daily adjusted-close reference.
- Validated 27,533 rows across 66 training stocks and 521 signal weeks. Every target was checked against daily adjusted closes, including gap-adjacent and final-week labels.
- Fitted all 45 component snapshots using the 156 / 52 / 52-week windows and 26-week refits.
- Reloaded every new model and checked exact equality of its training-matrix scores before and after saving. Verified every model hash and both stages' output manifests.
- Produced no external predictions or external backtest. New experimental weights do not replace the original frozen strategy snapshots.

## Regression, environment and package checks

- All **87 regression tests passed**, with **0 failures and 0 skips**. These include the October 29 label-gap, final-label, partial-position and all-cash accounting cases.
- All **46 project Python files** passed static syntax parsing.
- Runtime dependency and processed-input readiness checks passed in the isolated `.venv` environment.
- The release inventory is refreshed after documentation/evidence updates. Run `python -B tools/check_release.py` for the final unpacked inventory check; it is distinct from numerical verification.

The original October 26 Windows validation record is preserved [separately](validation_history/2026-10-26.json). The current run does not repeat a Windows execution, raw data acquisition, original four-model training or generalisation evaluation.

## Reproduce these checks

Activate the project environment first. Use unused run IDs, because existing results are never overwritten.

```bash
source .venv/bin/activate
python -B tools/check_environment.py
python -B -m unittest discover -s pipeline_tests -v
python -B safecapital.py --run-id replay_check_new
python -B safecapital.py --retrain-v1 --profile full --run-id training_check_new
python -B tools/check_release.py
```

On Windows, activate `.venv\Scripts\Activate.ps1` instead. Predictions, portfolio simulation and the training demonstration are separate checks. These tests establish the supplied historical workflow's consistency, not future profitability or support for arbitrary new uploaded data.
