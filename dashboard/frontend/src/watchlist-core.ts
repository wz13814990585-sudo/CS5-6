export const WATCHLIST_KEY = "cs5_6_equity.watchlist.v1";
export const EXAMPLE_TICKERS = ["SCL", "TJX", "CMG"];
export const EXAMPLE_DATE = "2026-08-28";
export function parseWatchlist(raw: string | null): string[] {
  try {
    const value: unknown = JSON.parse(raw || "[]");
    if (!Array.isArray(value)) return [];
    return [
      ...new Set(
        value
          .filter((v): v is string => typeof v === "string")
          .map((v) => v.trim().toUpperCase())
          .filter((v) => /^[A-Z0-9.-]{1,12}$/.test(v)),
      ),
    ].slice(0, 40);
  } catch {
    return [];
  }
}
export function matchStocks<
  T extends { ticker: string; stock_name: string | null },
>(stocks: T[], search: string): T[] {
  const query = search.trim().toUpperCase();
  return stocks
    .filter(
      (s) =>
        s.ticker.includes(query) || s.stock_name?.toUpperCase().includes(query),
    )
    .sort(
      (a, b) =>
        Number(b.ticker === query) - Number(a.ticker === query) ||
        a.ticker.localeCompare(b.ticker),
    );
}
