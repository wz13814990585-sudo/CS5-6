// Node.js 22 or a browser module. Configure api_origins for a cross-origin browser.
// Node: node dashboard/examples/client.mjs http://127.0.0.1:8000/
export async function loadSafeCapital(baseURL) {
  const base = new URL(
    "api/cs5_6_equity/v1/",
    baseURL.endsWith("/") ? baseURL : baseURL + "/",
  );
  async function get(path) {
    const response = await fetch(new URL(path, base));
    const body = await response.json();
    if (!response.ok)
      throw new Error(
        `${body.error.code}: ${body.error.message} (${body.error.request_id})`,
      );
    return body;
  }
  const runs = await get("runs");
  if (!runs.default_run_id) throw new Error("No verified result available");
  const id = encodeURIComponent(runs.default_run_id);
  const overview = await get(`runs/${id}/overview`);
  const date = overview.dates.at(-1);
  const rankings = await get(`runs/${id}/rankings?date=${date}&page_size=10`);
  const portfolio = await get(`runs/${id}/portfolio`);
  const inputs = await get(`runs/${id}/inputs`);
  if (!inputs.available) throw new Error(inputs.reason);
  const ticker = rankings.rows[0].ticker;
  const query = new URLSearchParams({
    date,
    q: ticker,
    scope: "output",
    page_size: "100",
  });
  const factors = await get(`runs/${id}/inputs/factors/rows?${query}`);
  const prices = await get(`runs/${id}/inputs/prices/rows?${query}`);
  // q is a substring filter. Join by both date and exact ticker, never row position.
  const match = (row) => row.date === date && row.ticker === ticker;
  return {
    run_id: runs.default_run_id,
    date,
    ticker,
    input_factors: factors.rows.find(match),
    input_prices: prices.rows.find(match) ?? null,
    output_ranking: rankings.rows.find(match),
    output_summary: overview.summary,
    portfolio,
    downloads: {
      factors: new URL(`runs/${id}/inputs/factors/download`, base).href,
      prices: new URL(`runs/${id}/inputs/prices/download`, base).href,
      predictions: new URL(`runs/${id}/downloads/predictions`, base).href,
    },
  };
}
if (typeof process !== "undefined" && process.argv[1]?.endsWith("client.mjs")) {
  console.log(
    JSON.stringify(
      await loadSafeCapital(process.argv[2] || "http://127.0.0.1:8000/"),
      null,
      2,
    ),
  );
}
