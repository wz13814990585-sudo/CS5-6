// Reproducible success, no-data and invalid-input acceptance against a running service.
import assert from "node:assert/strict";
const base = new URL(
  "api/cs5_6_equity/v1/",
  (process.argv[2] || "http://127.0.0.1:8000/").replace(/\/?$/, "/"),
);
async function request(path) {
  const response = await fetch(new URL(path, base));
  return { http: response.status, data: await response.json() };
}
const runs = await request("runs");
assert.equal(runs.http, 200);
assert.ok(runs.data.default_run_id);
const path = `runs/${encodeURIComponent(runs.data.default_run_id)}/portfolio`;
const success = await request(path);
assert.equal(success.http, 200);
assert.equal(success.data.status, "success");
assert.equal(success.data.module_id, "cs5_6_equity");
assert.ok(
  Math.abs(success.data.metrics.annualized_return - 0.1043902627962429) < 1e-10,
);
assert.ok(
  Math.abs(
    success.data.allocation.rows.reduce(
      (sum, row) => sum + row.actual_weight,
      0,
    ) +
      success.data.allocation.cash_weight -
      1,
  ) < 1e-10,
);
assert.equal(success.data.benchmark.series, null);
const noData = await request(path + "?date=2019-08-30");
assert.equal(noData.http, 200);
assert.equal(noData.data.status, "no_data");
assert.equal(noData.data.allocation.cash_weight, null);
assert.deepEqual(noData.data.allocation.rows, []);
const invalid = await request(path + "?date=not-a-date");
assert.equal(invalid.http, 422);
assert.equal(invalid.data.status, "error");
const missing = await request("runs/missing/portfolio");
assert.equal(missing.http, 404);
assert.equal(missing.data.status, "error");
console.log(
  JSON.stringify(
    {
      status: "passed",
      module: success.data.module_id,
      run_id: runs.data.default_run_id,
      cases: {
        success: success.http,
        no_data: noData.http,
        invalid_date: invalid.http,
        missing_run: missing.http,
      },
    },
    null,
    2,
  ),
);
