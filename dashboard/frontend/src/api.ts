/** Bound the complete JSON request, including a stalled response body. */
export const apiURL = (path: string) =>
  new URL(`api/cs5_6_equity/v1/${path}`, new URL("./", window.location.href))
    .href;

export async function readJSON<T>(
  url: string,
  signal?: AbortSignal,
  timeoutMs = 12000,
): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const cancel = () => controller.abort();
  if (signal?.aborted) controller.abort();
  else signal?.addEventListener("abort", cancel, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  try {
    const response = await fetch(url, { signal: controller.signal });
    const body = await response.json();
    if (!response.ok)
      throw new Error(
        body.error?.message || "无法读取结果，请确认 Dashboard 服务正在运行。",
      );
    if (controller.signal.aborted)
      throw new DOMException("Aborted", "AbortError");
    return body;
  } catch (error) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    if (timedOut) throw new Error("请求超时，请检查本地服务后重试。");
    if (error instanceof TypeError)
      throw new Error("无法连接研究服务，请检查服务是否正在运行。");
    if (error instanceof SyntaxError)
      throw new Error("服务返回了无法读取的数据，请重试。");
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
  }
}
