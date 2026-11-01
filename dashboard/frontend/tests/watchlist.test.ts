import assert from "node:assert/strict";
import { test } from "node:test";
import { parseWatchlist, matchStocks } from "../src/watchlist-core.ts";

test("saved preferences survive normalisation and corrupted storage safely", () => {
  assert.deepEqual(
    parseWatchlist('[" scl ", "TJX", "SCL", null, 7, "<script>"]'),
    ["SCL", "TJX"],
  );
  for (const value of [null, "not JSON", '{"ticker":"SCL"}', '"SCL"'])
    assert.deepEqual(parseWatchlist(value), []);
});
test("ticker and company searches find the same stock, with exact ticker first", () => {
  const stocks = [
    { ticker: "CMG", stock_name: "Chipotle Mexican Grill Inc." },
    { ticker: "SCL", stock_name: "Stepan Company" },
    { ticker: "TJX", stock_name: "The TJX Companies, Inc." },
  ];
  assert.equal(matchStocks(stocks, " chipotle ")[0].ticker, "CMG");
  assert.equal(matchStocks(stocks, "scl")[0].ticker, "SCL");
  assert.deepEqual(matchStocks(stocks, "AAPL"), []);
  assert.deepEqual(
    matchStocks(
      [...stocks, { ticker: "AAA", stock_name: "SCL group" }],
      "SCL",
    ).map((s) => s.ticker),
    ["SCL", "AAA"],
  );
  assert.equal(
    matchStocks([{ ticker: "CMG", stock_name: null }], "CMG").length,
    1,
  );
});
