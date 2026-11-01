"""HTTP acceptance of the real customer result, independent of repository paths."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import urlopen
from urllib.parse import urljoin


def check(url, expected=None):
    base = url.rstrip("/") + "/"

    def read(path):
        with urlopen(urljoin(base, path), timeout=15) as response:
            return response.read()

    def get(path):
        return json.loads(read("api/cs5_6_equity/v1/" + path))

    assert get("health")["status"] == "ok"
    runs = get("runs")
    run_id = runs["default_run_id"]
    assert run_id
    overview = get(f"runs/{run_id}/overview")
    equity = get(f"runs/{run_id}/equity")["rows"]
    assert len(equity) == overview["summary"]["weeks"]
    assert equity[-1]["end_capital"] == overview["summary"]["final_capital"]
    portfolio = get(f"runs/{run_id}/portfolio")
    assert portfolio["status"] == "success"
    assert portfolio["module_id"] == "cs5_6_equity"
    assert portfolio["metrics"]["final_capital"] == overview["summary"]["final_capital"]
    allocation = portfolio["allocation"]
    assert (
        abs(
            sum(row["actual_weight"] for row in allocation["rows"])
            + allocation["cash_weight"]
            - 1
        )
        < 1e-10
    )
    date = overview["dates"][-1]
    ranking = get(f"runs/{run_id}/rankings?date={date}&page_size=100")
    assert len(ranking["rows"]) == ranking["total"] > 0
    assert ranking["rows"][0]["ensemble_predicted_rank"] == 1
    inputs = get(f"runs/{run_id}/inputs")
    assert inputs["available"]
    for dataset in inputs["datasets"]:
        key = dataset["id"]
        downloaded = read(f"api/cs5_6_equity/v1/runs/{run_id}/inputs/{key}/download")
        assert hashlib.sha256(downloaded).hexdigest() == dataset["sha256"]
        original = list(csv.DictReader(io.StringIO(downloaded.decode("utf-8-sig"))))
        assert len(original) == dataset["source_rows"]
        sample_date = dataset["output_dates"][-1]
        rows = get(f"runs/{run_id}/inputs/{key}/rows?date={sample_date}&page_size=100")
        assert rows["total"] == len(rows["rows"]) > 0
        source = {(row["date"], row["ticker"]): row for row in original}
        for row in rows["rows"]:
            raw = source[(row["date"], row["ticker"])]
            for column in dataset["columns"]:
                name = column["key"]
                value = float(raw[name]) if column["type"] == "number" else raw[name]
                assert row[name] == value
    for kind, filename in [
        ("summary", "backtest/summary.csv"),
        ("equity", "backtest/weekly_capital.csv"),
        ("predictions", "saved_model_predictions.csv"),
        ("manifest", "manifest.json"),
    ]:
        downloaded = read(f"api/cs5_6_equity/v1/runs/{run_id}/downloads/{kind}")
        if expected:
            assert downloaded == (Path(expected) / filename).read_bytes(), filename
        if kind == "summary":
            row = next(csv.DictReader(io.StringIO(downloaded.decode("utf-8-sig"))))
            assert float(row["final_capital"]) == overview["summary"]["final_capital"]
        if kind == "manifest":
            assert (
                hashlib.sha256(downloaded).hexdigest()
                == overview["run"]["manifest_sha256"]
            )
    html = read("").decode()
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', html)
    assert scripts
    for script in scripts:
        assert read(script)
    assert b"iframe" in read("embed-example.html")
    try:
        read("api/cs5_6_equity/v1/runs/does-not-exist/overview")
        raise AssertionError("Missing run accepted")
    except HTTPError as exc:
        assert exc.code == 404
        assert json.load(exc)["error"]["code"] == "not_found"
    return {
        "status": "passed",
        "run_id": run_id,
        "prediction_rows": overview["run"]["prediction_rows"],
        "weeks": len(equity),
        "final_capital": overview["summary"]["final_capital"],
        "module_id": portfolio["module_id"],
        "allocation_status": allocation["status"],
        "input_datasets": [d["id"] for d in inputs["datasets"]],
        "input_rows_each": [d["source_rows"] for d in inputs["datasets"]],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/")
    parser.add_argument("--expected-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.url, args.expected_dir), indent=2))
