# Ensemble Training Demonstration V1

V1 is the legacy identifier of this training-method workflow. It is not a whole-project version or a second external strategy evaluation. Only the three Ensemble components are fitted. There are no standalone external Rankers, external predictions, external backtests or comparisons with the frozen Ensemble.

Reproduction starts from the supplied processed weekly data. Raw data acquisition and reconstruction are outside this delivery's scope.

## Commands

```bash
python safecapital.py --retrain-v1 --profile smoke
python safecapital.py --retrain-v1 --profile full
```

Choose one profile: smoke fits the latest snapshot for each component (3 files); full fits 15 snapshots for each component (45 files). `--run-id NAME` selects a new output folder. Existing folders cannot be overwritten. `--stage check` checks readiness; `--stage prepare` writes only prepared training inputs. The normal default runs preparation and training together. There is no resume/recovery interface; start a fresh run after interruption.

## Data and method

The training demonstration requires three supplied files:

| Input (project-relative) | Purpose |
|---|---|
| `data/reproducible/train66_corrected_complete.csv` | Weekly factors, adjusted closes and next-week labels for 66 training stocks across 521 signal weeks, 2016-09-02 through 2026-08-21 |
| `data/reproducible/train_universe.csv` | Validate the 66 distinct training tickers |
| `data/clean_basic_data.csv` | Daily adjusted-close reference for checking every training label, including the final week and rows before missing weekly observations |

All three files enter the input identity recorded in the run manifest. The daily reference is restricted to training tickers during label verification. External test stocks and external execution-price panels are not used by this workflow.

Preparation validates keys, finite factors, the training universe and consecutive NYSE weeks. It checks adjacent weekly returns where available, then verifies every target as `ln(daily adjusted close on label_end_date / weekly adjusted close)`. This includes the 16 rows before missing weekly observations and the final signal week. The daily file is already supplied; no raw-data acquisition is required.

The component training windows are 156 / 52 / 52 weeks with chronological refits every 26 weeks. Training labels must be observable at the refit signal date. Factor values are ranked within each training week. The original component definitions and training implementation are in `external_validation/ensemble_ranker/code/ranker_core.py`. V1 uses one training thread and seed 5703.

Each fitted JSON model is reloaded and its scores on the training matrix are compared exactly with those before saving. This checks model serialization; it does not evaluate external performance. The Ensemble combination rule is the equal-weight mean of its three components' weekly percentile scores and has no separate fitted tree file.

## Outputs

| Output | Role |
|---|---|
| `prepare/train.csv` | Validated weekly training panel with week indices and label-end dates |
| `prepare/calendar.csv` | Training calendar |
| `prepare/data_audit.json` | Coverage, input identity and preparation checks |
| `train/models/` | Three or 45 newly fitted component snapshots |
| `train/model_manifest.json` | Features, parameters, chronological windows, model hashes and training provenance |
| `manifest.json`, `run.log` | Execution status, environment, source/input/output hashes and progress |

The default frozen replay continues to use its original 45 snapshots. Training artifacts cannot replace those files automatically. Fixed hyperparameters and a fixed seed do not guarantee identical tree fitting across environments, which is why the strategy result uses frozen models plus exact prediction and account checks. See the [root README](../README.md) and [validation record](VALIDATION.md).
