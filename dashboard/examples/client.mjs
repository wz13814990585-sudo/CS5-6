// Node.js 22 or a browser module. Configure api_origins for a cross-origin browser.
// Node: node dashboard/examples/client.mjs http://127.0.0.1:8000/
export async function loadSafeCapital(baseURL) {
  const base = new URL('api/v1/', baseURL.endsWith('/') ? baseURL : baseURL + '/');
  async function get(path) {
    const response = await fetch(new URL(path, base));
    const body = await response.json();
    if (!response.ok) throw new Error(`${body.error.code}: ${body.error.message} (${body.error.request_id})`);
    return body;
  }
  const runs = await get('runs');
  if (!runs.default_run_id) throw new Error('No verified result available');
  const id = encodeURIComponent(runs.default_run_id);
  const overview = await get(`runs/${id}/overview`);
  const date = overview.dates.at(-1);
  const rankings = await get(`runs/${id}/rankings?date=${date}&page_size=10`);
  return {overview, rankings};
}
if (typeof process !== 'undefined' && process.argv[1]?.endsWith('client.mjs')) {
  console.log(JSON.stringify(await loadSafeCapital(process.argv[2] || 'http://127.0.0.1:8000/'), null, 2));
}
