import assert from "node:assert/strict";
import { test } from "node:test";
import { readJSON } from "../src/api.ts";

function pending(signal: AbortSignal) {
  return new Promise<never>((_, reject) => {
    const cancel = () => reject(new DOMException("Aborted", "AbortError"));
    if (signal.aborted) cancel();
    else signal.addEventListener("abort", cancel, { once: true });
  });
}
test("timeout bounds both the initial fetch and a stalled JSON body", async (t) => {
  for (const phase of ["fetch", "body"]) {
    t.mock.method(
      globalThis,
      "fetch",
      async (_url: unknown, options: RequestInit) => {
        const signal = options.signal!;
        if (phase === "fetch") return pending(signal);
        return { ok: true, json: () => pending(signal) };
      },
    );
    await assert.rejects(
      readJSON("http://localhost/test", undefined, 15),
      /请求超时/,
    );
    t.mock.restoreAll();
  }
});
test("changing selections cancels a request without displaying a timeout", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    async (_url: unknown, options: RequestInit) => pending(options.signal!),
  );
  const controller = new AbortController();
  const request = readJSON("http://localhost/test", controller.signal, 200);
  controller.abort();
  await assert.rejects(request, { name: "AbortError" });
});
test("successful data and structured API errors are preserved", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response(JSON.stringify({ rows: [], status: "no_data" })),
  );
  assert.deepEqual(await readJSON("http://localhost/test"), {
    rows: [],
    status: "no_data",
  });
  t.mock.restoreAll();
  t.mock.method(
    globalThis,
    "fetch",
    async () =>
      new Response(
        JSON.stringify({ error: { message: "Unsupported stocks: AAPL" } }),
        { status: 422 },
      ),
  );
  await assert.rejects(
    readJSON("http://localhost/test"),
    /Unsupported stocks: AAPL/,
  );
});
test("non-JSON responses and connection failures have readable messages", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response("<html>Gateway error</html>", { status: 502 }),
  );
  await assert.rejects(readJSON("http://localhost/test"), /无法读取的数据/);
  t.mock.restoreAll();
  t.mock.method(globalThis, "fetch", async () => {
    throw new TypeError("Failed to fetch");
  });
  await assert.rejects(readJSON("http://localhost/test"), /无法连接研究服务/);
});
