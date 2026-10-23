"""Replay the saved walk-forward models, or retrain the frozen configuration.

This entry point reproduces the supplied 66-train/40-test historical experiment.
It does not perform parameter search, portfolio construction or trading.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from xgboost import XGBRanker

import ranker_core as core
from prediction_helpers import load_test, training_window, score_block
import build_evaluation as evaluation

ROOT = Path(__file__).resolve().parent.parent


def run(args):
    train, train_audit = core.load_data(ROOT / "inputs/train66.csv")
    test, test_audit = load_test(ROOT / "inputs/test40.csv", train)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = out / "prediction_source"
    for name in ("predictions", "audit"):
        (source / name).mkdir(parents=True)
    if args.mode == "train":
        (out / "models").mkdir()
    reference = evaluation.read_csv(ROOT / "outputs/current/predictions/stock_rankings.csv", ["date"])
    components, windows, comparisons = {}, [], []
    for number, spec in enumerate(core.COMPONENTS, 1):
        blocks = []
        for refit in range(core.FORMAL_START_WEEK, core.TOTAL_EXPECTED_WEEKS, core.REFIT_INTERVAL_WEEKS):
            end = min(refit + core.REFIT_INTERVAL_WEEKS, core.TOTAL_EXPECTED_WEEKS) - 1
            training = training_window(train, spec, refit)
            block = test[test.week_index.between(refit, end)]
            model_id = f"{spec.component_id}_refit_{refit:04d}"
            if args.mode == "train":
                model = core.fit_ranker(training, spec, args.n_jobs)
                model.save_model(out / "models" / f"{model_id}.json")
            else:
                model = XGBRanker(n_jobs=args.n_jobs)
                model.load_model(ROOT / "models" / f"{model_id}.json")
            predicted = score_block(model, spec, block)
            predicted["component_id"] = spec.component_id
            predicted["model_id"] = model_id
            predicted["refit_week"] = refit
            blocks.append(predicted)
            compared = predicted.merge(reference[["date", "ticker", f"model_{number}_raw_score"]], on=["date", "ticker"], validate="one_to_one")
            error = float((compared.raw_ranking_score - compared[f"model_{number}_raw_score"]).abs().max())
            if args.mode == "replay":
                np.testing.assert_array_equal(compared.raw_ranking_score, compared[f"model_{number}_raw_score"])
            comparisons.append({"model_id": model_id, "compared_rows": len(compared), "maximum_raw_score_error": error,
                                "passed": error <= 1e-7, "reference": "packaged current unseen40 predictions"})
            windows.append({"model_id": model_id, "refit_week": refit, "refit_date": block.date.min(),
                            "training_start_week": int(training.week_index.min()), "training_end_week": int(training.week_index.max()),
                            "training_start_date": training.date.min(), "training_end_date": training.date.max(),
                            "maximum_training_label_end_week": int(training.label_end_week.max()),
                            "training_weeks": training.week_index.nunique(), "training_rows": len(training),
                            "training_tickers": training.ticker.nunique(), "test_ticker_overlap": 0,
                            "features": json.dumps(spec.features), "hyperparameters": json.dumps(spec.params, sort_keys=True),
                            "training_label": "weekly_relevance_0_to_4", "start_date": block.date.min(), "end_date": block.date.max(),
                            "prediction_weeks": block.date.nunique(), "prediction_rows": len(block)})
            print(f"{args.mode}: {model_id}; maximum score difference={error:.3g}", flush=True)
        components[spec.component_id] = pd.concat(blocks, ignore_index=True)
    combined = core.build_ensemble(components).merge(test[["date", "ticker", "stock_name"]], on=["date", "ticker"], validate="one_to_one")
    combined = combined.rename(columns={"target": "actual_next_week_log_return", "actual_rank": "actual_rank_ticker_tiebreak"})
    combined["actual_rank_average"] = combined.groupby("date").actual_next_week_log_return.rank(method="average", ascending=False)
    combined["actual_relevance_0_to_4"] = combined.groupby("date").actual_next_week_log_return.transform(evaluation.labels_from_target)
    combined = combined[reference.columns]
    if args.mode == "replay":
        pd.testing.assert_frame_equal(combined, reference, check_dtype=False, check_exact=True)
    evaluation.write_csv(source / "predictions/stock_rankings.csv", combined)
    for name, frame in [("training_windows.csv", pd.DataFrame(windows)), ("training_data_audit.csv", train_audit),
                        ("data_audit.csv", test_audit), ("original_model_reproduction.csv", pd.DataFrame(comparisons))]:
        evaluation.write_csv(source / "audit" / name, frame)
    evaluation.write_json(source / "run_manifest.json", {"train_tickers": sorted(train.ticker.unique()), "test_tickers": sorted(test.ticker.unique()),
                                                        "mode": args.mode, "test_targets_used_for_training": False})
    evaluation.build(SimpleNamespace(source=source, output=out / "evaluation"))
    manifest_path = out / "evaluation/run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update({"models_retrained": args.mode == "train", "prediction_mode": args.mode,
                     "maximum_bundled_model_score_difference": max(r["maximum_raw_score_error"] for r in comparisons)})
    evaluation.write_json(manifest_path, manifest)
    print(f"Completed: {out / 'evaluation'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["replay", "train"], default="replay")
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing directories are rejected")
    parser.add_argument("--n-jobs", type=int, default=4)
    run(parser.parse_args())
