// Read-only acceptance against the shipped historical example. Node.js 22+.
import assert from "node:assert/strict";
const base = new URL(
  "api/cs5_6_equity/v1/",
  (process.argv[2] || "http://127.0.0.1:8000/").replace(/\/?$/, "/"),
);
async function get(path) {
  const response = await fetch(new URL(path, base), {
    signal: AbortSignal.timeout(12000),
  });
  return { status: response.status, body: await response.json() };
}
const { body: runs } = await get("runs");
assert.ok(runs.default_run_id);
const run = `runs/${encodeURIComponent(runs.default_run_id)}`;
const { body: catalog } = await get(`${run}/stocks`);
assert.equal(catalog.stocks.length, 40);
const query = new URLSearchParams({
  date: "2026-08-28",
  tickers: "SCL,TJX,CMG",
});
const result = await get(`${run}/watchlist?${query}`);
assert.equal(result.status, 200);
assert.equal(result.body.status, "success");
assert.deepEqual(
  result.body.rows.map((r) => r.ranking.ensemble_predicted_rank),
  [1, 2, 3],
);
assert.deepEqual(
  result.body.rows.map((r) => r.selection_status),
  ["selected", "not_selected", "selected"],
);
assert.equal(result.body.rows[1].allocation, null);
assert.equal(result.body.rows[1].exclusion_reason, null);
assert.equal(result.body.watchlist_changes_strategy, false);
const { body: original } = await get(`${run}/portfolio`);
assert.deepEqual(result.body.strategy_context.metrics, original.metrics);
const exported = await get(`${run}/watchlist/download?${query}&format=json`);
assert.deepEqual(exported.body, result.body);
const empty = await get(`${run}/watchlist?date=2015-09-04&tickers=SCL`);
assert.equal(empty.body.status, "no_data");
assert.equal(empty.body.rows[0].ranking, null);
assert.equal(empty.body.rows[0].allocation, null);
const unsupported = await get(
  `${run}/watchlist?date=2026-08-28&tickers=SCL,AAPL`,
);
assert.equal(unsupported.status, 422);
assert.equal(unsupported.body.error.code, "unsupported_stocks");
console.log(
  JSON.stringify(
    {
      status: "passed",
      run_id: runs.default_run_id,
      stocks: 40,
      date: result.body.signal_date,
      example: result.body.rows.map((r) => ({
        ticker: r.ticker,
        rank: r.ranking.ensemble_predicted_rank,
        selection: r.selection_status,
      })),
      original_metrics_unchanged: true,
      json_export_matched: true,
      no_data: empty.status,
      unsupported: unsupported.status,
    },
    null,
    2,
  ),
);
