import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  Info,
  Play,
  Plus,
  RotateCcw,
  Search,
  Star,
  X,
} from "lucide-react";
import { useLanguage } from "./i18n";
import { apiURL, readJSON } from "./api";
import {
  EXAMPLE_DATE,
  EXAMPLE_TICKERS,
  WATCHLIST_KEY,
  matchStocks,
  parseWatchlist,
} from "./watchlist-core";
import "./watchlist.css";

type Stock = { ticker: string; stock_name: string | null };
type Catalog = { run_id: string; stocks: Stock[] };
type Selection = "selected" | "not_selected" | "unavailable" | "no_data";
type Inspection = Stock & {
  factors_status: string;
  factors: Record<string, number> | null;
  prices_status: string;
  prices: { buy_price: number; sell_price: number } | null;
  ranking: {
    ensemble_predicted_rank: number;
    ensemble_ranking_score: number;
    model_1_percentile: number;
    model_2_percentile: number;
    model_3_percentile: number;
  } | null;
  selection_status: Selection;
  allocation: {
    target_weight: number;
    actual_weight: number;
    shares: number;
  } | null;
};
type Result = {
  run_id: string;
  signal_date: string;
  requested_tickers: string[];
  rows: Inspection[];
  status: string;
  strategy_context: {
    strategy: { id: string };
    liquidated_at_period_end: boolean | null;
    units: { currency: string | null };
  };
};
type Props = {
  runId: string;
  date: string;
  dates: string[];
  onDateChange: (date: string) => void;
  onReset: () => void;
  onExample: (date: string) => void;
};
const number = (value: number | null | undefined, digits = 4) =>
  value == null
    ? "—"
    : value.toLocaleString("en-US", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
const percent = (value: number | null | undefined) =>
  value == null ? "—" : `${(value * 100).toFixed(2)}%`;
const featureLabels = [
  ["revenue_growth_yoy", "营收同比增长"],
  ["operating_profitability", "经营盈利能力"],
  ["cashflow_to_assets", "现金流 / 资产"],
  ["debt_to_assets", "负债 / 资产"],
  ["asset_growth_yoy", "资产同比增长"],
];
function savedWatchlist() {
  try {
    return parseWatchlist(localStorage.getItem(WATCHLIST_KEY));
  } catch {
    return [];
  }
}
export default function WatchlistPanel({
  runId,
  date,
  dates,
  onDateChange,
  onReset,
  onExample,
}: Props) {
  const { t } = useLanguage();
  const [selected, setSelected] = useState<string[]>(savedWatchlist);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [option, setOption] = useState(0);
  const [active, setActive] = useState<string | null>(null);
  const [result, setResult] = useState<{ key: string; value: Result } | null>(
    null,
  );
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [announcement, setAnnouncement] = useState<{
    message: string;
    values?: Record<string, string>;
  }>({ message: "" });
  const input = useRef<HTMLInputElement>(null);
  const currentCatalog = catalog?.run_id === runId ? catalog : null;
  const stocks = currentCatalog?.stocks ?? [];
  const watch = selected.filter((ticker) =>
    stocks.some((s) => s.ticker === ticker),
  );
  const tickerKey = watch.join(",");
  const key = `${runId}|${date}|${tickerKey}`;
  const data = result?.key === key ? result.value : null;
  const rows = data?.rows ?? [];
  const focused = rows.find((r) => r.ticker === active) ?? rows[0];
  const matches = matchStocks(stocks, query);
  const suggestions = matches.slice(0, 10);
  const dateIndex = dates.indexOf(date);
  const queryParams = new URLSearchParams({ date, tickers: tickerKey });
  const resultURL = apiURL(
    `runs/${encodeURIComponent(runId)}/watchlist?${queryParams}`,
  );
  const downloadURL = (format: string) =>
    apiURL(
      `runs/${encodeURIComponent(runId)}/watchlist/download?${queryParams}&format=${format}`,
    );
  useEffect(() => {
    try {
      localStorage.setItem(WATCHLIST_KEY, JSON.stringify(selected));
    } catch {}
  }, [selected]);
  useEffect(() => {
    const controller = new AbortController();
    setCatalogError("");
    readJSON<Catalog>(
      apiURL(`runs/${encodeURIComponent(runId)}/stocks`),
      controller.signal,
    )
      .then((value) => {
        if (!controller.signal.aborted) setCatalog(value);
      })
      .catch((e) => {
        if (e.name !== "AbortError") setCatalogError(e.message);
      });
    return () => controller.abort();
  }, [runId, retry]);
  useEffect(() => {
    if (!currentCatalog) return;
    setSelected((values) =>
      values.filter((ticker) =>
        currentCatalog.stocks.some((s) => s.ticker === ticker),
      ),
    );
  }, [currentCatalog]);
  useEffect(() => {
    setResult(null);
    setError("");
    if (!tickerKey || !date) return;
    const controller = new AbortController();
    readJSON<Result>(resultURL, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setResult({ key, value });
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [key, resultURL, retry, tickerKey, date]);
  const statusLabel = (status: Selection) =>
    t(
      {
        selected: "已入选策略",
        not_selected: "未入选策略",
        unavailable: "暂无法判断",
        no_data: "该日期无配置",
      }[status],
    );
  function add(ticker: string) {
    if (!stocks.some((s) => s.ticker === ticker)) return;
    setSelected((values) =>
      values.includes(ticker) ? values : [...values, ticker],
    );
    setActive(ticker);
    setQuery("");
    setOpen(false);
    setOption(0);
    setAnnouncement({ message: "已关注 {ticker}", values: { ticker } });
    input.current?.focus();
  }
  function remove(ticker: string) {
    setSelected((values) => values.filter((x) => x !== ticker));
    setAnnouncement({ message: "已移除 {ticker}", values: { ticker } });
  }
  function example() {
    setSelected(
      EXAMPLE_TICKERS.filter((x) => stocks.some((s) => s.ticker === x)),
    );
    setQuery("");
    setOpen(false);
    setActive("SCL");
    onExample(dates.includes(EXAMPLE_DATE) ? EXAMPLE_DATE : dates.at(-1)!);
    setAnnouncement({ message: "示例已载入：对照排名与策略入选情况。" });
  }
  function reset() {
    setSelected([]);
    setQuery("");
    setOpen(false);
    setActive(null);
    setError("");
    onReset();
    setAnnouncement({ message: "已重置关注列表、日期和图表筛选。" });
  }
  return (
    <section
      id="watchlist"
      className="watchlist panel"
      aria-labelledby="watchlist-title"
    >
      <div className="watchlist-heading">
        <div>
          <span className="eyebrow">YOUR RESEARCH · WATCHLIST</span>
          <h2 id="watchlist-title">{t("从你关注的股票开始")}</h2>
          <p>{t("选择股票，查看同一历史日期的输入、模型排名与策略配置。")}</p>
        </div>
        <div className="watchlist-actions">
          <button className="button secondary" onClick={reset}>
            <RotateCcw size={15} />
            {t("重置演示")}
          </button>
          <button
            className="watchlist-primary"
            onClick={example}
            disabled={!currentCatalog}
          >
            <Play size={15} />
            {t("载入演示示例")}
          </button>
        </div>
      </div>
      <div className="watchlist-steps" aria-label={t("研究查看流程")}>
        <span>
          <b>01</b>
          {t("选择关注股票")}
        </span>
        <ArrowRight size={14} />
        <span>
          <b>02</b>
          {t("查看输入与排名")}
        </span>
        <ArrowRight size={14} />
        <a href="#performance">
          <b>03</b>
          {t("查看原策略表现")}
        </a>
      </div>
      <div className="watchlist-controls">
        <div
          className="watchlist-picker"
          onBlur={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget))
              setOpen(false);
          }}
        >
          <label htmlFor="watchlist-search">{t("添加关注股票")}</label>
          <div className="watchlist-search">
            <Search size={18} />
            <input
              id="watchlist-search"
              ref={input}
              role="combobox"
              aria-expanded={open}
              aria-controls="watchlist-options"
              aria-autocomplete="list"
              aria-activedescendant={
                open && suggestions[option]
                  ? `watchlist-option-${suggestions[option].ticker}`
                  : undefined
              }
              autoComplete="off"
              maxLength={80}
              disabled={!currentCatalog}
              placeholder={t("搜索代码或公司名称，例如 SCL、Chipotle")}
              value={query}
              onFocus={() => setOpen(true)}
              onChange={(e) => {
                setQuery(e.target.value);
                setOpen(true);
                setOption(0);
              }}
              onKeyDown={(e) => {
                if (e.key === "Escape") {
                  setOpen(false);
                  return;
                }
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  setOpen(true);
                  setOption((n) =>
                    open
                      ? Math.min(n + 1, Math.max(0, suggestions.length - 1))
                      : 0,
                  );
                }
                if (e.key === "ArrowUp") {
                  e.preventDefault();
                  setOption((n) => Math.max(0, n - 1));
                }
                if (e.key === "Enter") {
                  e.preventDefault();
                  const candidate = open
                    ? suggestions[option]
                    : stocks.find(
                        (s) => s.ticker === query.trim().toUpperCase(),
                      );
                  if (candidate) add(candidate.ticker);
                  else setOpen(true);
                }
              }}
            />
          </div>
          {open && currentCatalog && (
            <div className="watchlist-dropdown">
              <div
                id="watchlist-options"
                role="listbox"
                aria-label={t("可关注的研究股票")}
              >
                {suggestions.map((s, i) => (
                  <button
                    type="button"
                    role="option"
                    id={`watchlist-option-${s.ticker}`}
                    aria-selected={selected.includes(s.ticker)}
                    className={i === option ? "highlight" : ""}
                    key={s.ticker}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => add(s.ticker)}
                  >
                    <span>
                      <strong>{s.ticker}</strong>
                      <small>{s.stock_name || s.ticker}</small>
                    </span>
                    {selected.includes(s.ticker) ? (
                      <Check size={16} />
                    ) : (
                      <Plus size={16} />
                    )}
                  </button>
                ))}
              </div>
              {!matches.length ? (
                <p className="watchlist-no-match" role="status">
                  {t(
                    "不在当前支持的股票列表中。请从研究股票池中选择，不会为未支持的股票生成结果。",
                  )}
                </p>
              ) : (
                <p className="watchlist-search-hint">
                  {t("找到 {count} 只股票；继续输入可缩小范围。", {
                    count: matches.length,
                  })}
                </p>
              )}
            </div>
          )}
          <small className="watchlist-hint">
            {t(
              "仅查看本模块的 {count} 只外部评估股票；与客户网站的全局资产选择器独立。",
              { count: stocks.length || 40 },
            )}
          </small>
        </div>
        <div className="watchlist-date">
          <label htmlFor="research-date">{t("统一历史信号日期")}</label>
          <div>
            <button
              className="icon-button"
              aria-label={t("前一个研究周")}
              onClick={() => onDateChange(dates[dateIndex - 1])}
              disabled={dateIndex <= 0}
            >
              <ChevronLeft size={17} />
            </button>
            <select
              id="research-date"
              value={date}
              onChange={(e) => onDateChange(e.target.value)}
            >
              {!dates.includes(date) && date && (
                <option value={date}>
                  {date} · {t("回测区间外")}
                </option>
              )}
              {dates
                .slice()
                .reverse()
                .map((d) => (
                  <option key={d}>{d}</option>
                ))}
            </select>
            <button
              className="icon-button"
              aria-label={t("后一个研究周")}
              onClick={() => onDateChange(dates[dateIndex + 1])}
              disabled={dateIndex < 0 || dateIndex >= dates.length - 1}
            >
              <ChevronRight size={17} />
            </button>
          </div>
          <small className="watchlist-hint">
            {t("同步关注结果、持仓、排名和对齐输入。")}
          </small>
        </div>
      </div>
      {catalogError && (
        <div className="error" role="alert">
          {t(catalogError)}
          <button onClick={() => setRetry((n) => n + 1)}>{t("重试")}</button>
        </div>
      )}
      {!currentCatalog && !catalogError && (
        <div className="input-loading" role="status">
          {t("正在读取可关注的股票…")}
        </div>
      )}
      <div className="watchlist-selection">
        <span>
          <Star size={15} />
          {t("已关注 {count} 只", { count: watch.length })}
        </span>
        <div>
          {watch.map((ticker) => (
            <span className="watchlist-chip" key={ticker}>
              {ticker}
              <button
                aria-label={t("移除 {ticker}", { ticker })}
                onClick={() => remove(ticker)}
              >
                <X size={13} />
              </button>
            </span>
          ))}
        </div>
        {watch.length > 0 && (
          <button
            className="text-link"
            onClick={() => {
              setSelected([]);
              setActive(null);
            }}
          >
            {t("清空关注")}
          </button>
        )}
      </div>
      <span className="sr-only" role="status" aria-live="polite">
        {t(announcement.message, announcement.values)}
      </span>
      <div className="watchlist-boundary">
        <Info size={16} />
        <p>
          {t(
            "关注列表只改变查看范围，不重新计算组合。下方收益始终属于原策略完整组合。",
          )}
        </p>
      </div>
      {!watch.length && currentCatalog && (
        <div className="watchlist-empty">
          <span>
            <Star size={26} />
          </span>
          <h3>{t("先选一只你想了解的股票")}</h3>
          <p>{t("或载入 SCL、TJX、CMG 示例，看看排名和实际入选有何不同。")}</p>
          <button className="text-link" onClick={example}>
            {t("用真实示例开始")}
            <ArrowRight size={16} />
          </button>
        </div>
      )}
      {watch.length > 0 && (
        <>
          <div className="watchlist-results-heading">
            <div>
              <h3>{t("我的关注结果")}</h3>
              <small>
                {date} · {t("历史研究结果")}
              </small>
            </div>
            <div className="watchlist-exports">
              {data && (
                <>
                  <a className="button secondary" href={downloadURL("csv")}>
                    <Download size={14} />
                    {t("导出当前 CSV")}
                  </a>
                  <a href={downloadURL("json")} className="text-link">
                    {t("导出 JSON")}
                  </a>
                </>
              )}
            </div>
          </div>
          {error ? (
            <div className="error" role="alert">
              {t(error)}
              <button onClick={() => setRetry((n) => n + 1)}>
                {t("重试")}
              </button>
            </div>
          ) : !data ? (
            <div className="input-loading" role="status">
              {t("正在按同一日期关联输入、排名和配置…")}
            </div>
          ) : (
            <>
              <div className="table-scroll">
                <table
                  className="watchlist-table"
                  aria-label={t("关注股票研究结果")}
                >
                  <thead>
                    <tr>
                      <th>{t("股票代码")}</th>
                      <th>{t("模型排名")}</th>
                      <th>{t("集成得分")}</th>
                      <th>{t("策略入选状态")}</th>
                      <th>{t("目标权重")}</th>
                      <th>{t("实际权重")}</th>
                      <th>{t("操作")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr
                        key={row.ticker}
                        className={
                          focused?.ticker === row.ticker ? "focused" : ""
                        }
                      >
                        <td>
                          <button
                            className="watchlist-stock"
                            onClick={() => setActive(row.ticker)}
                          >
                            <strong>{row.ticker}</strong>
                            <small>{row.stock_name || "—"}</small>
                          </button>
                        </td>
                        <td>{row.ranking?.ensemble_predicted_rank ?? "—"}</td>
                        <td>{number(row.ranking?.ensemble_ranking_score)}</td>
                        <td>
                          <span
                            className={`selection-state ${row.selection_status}`}
                          >
                            {statusLabel(row.selection_status)}
                          </span>
                        </td>
                        <td>{percent(row.allocation?.target_weight)}</td>
                        <td>{percent(row.allocation?.actual_weight)}</td>
                        <td>
                          <button
                            className="text-link"
                            aria-pressed={focused?.ticker === row.ticker}
                            aria-label={t("查看 {ticker} 详情", {
                              ticker: row.ticker,
                            })}
                            onClick={() => setActive(row.ticker)}
                          >
                            {t("查看详情")}
                            <ArrowRight size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="watchlist-table-note">
                {t(
                  "得分是当周的相对排名参考，不是预计收益。未入选与没有配置记录是两种不同状态。",
                )}
              </p>
              {focused && (
                <article
                  className="watchlist-detail"
                  aria-label={t("关注股票详情")}
                >
                  <div className="watchlist-detail-title">
                    <div>
                      <span className="eyebrow">STOCK DETAIL · {date}</span>
                      <h3>
                        {focused.ticker}
                        <span>{focused.stock_name || "—"}</span>
                      </h3>
                    </div>
                    <span
                      className={`selection-state ${focused.selection_status}`}
                    >
                      {statusLabel(focused.selection_status)}
                    </span>
                  </div>
                  <div className="watchlist-detail-grid">
                    <div>
                      <h4>{t("输入：五个原始因子")}</h4>
                      {focused.factors ? (
                        <dl className="watchlist-factors">
                          {featureLabels.map(([key, label]) => (
                            <div key={key}>
                              <dt>{t(label)}</dt>
                              <dd>{number(focused.factors?.[key], 6)}</dd>
                            </div>
                          ))}
                        </dl>
                      ) : (
                        <p className="watchlist-missing">
                          {t(
                            focused.factors_status === "unavailable"
                              ? "匹配的输入文件暂不可用。"
                              : "该股票在此日期没有对齐的因子记录。",
                          )}
                        </p>
                      )}
                      <p>
                        {t(
                          "因子以原始数值展示；模型使用同周股票百分位转换后的输入。",
                        )}
                      </p>
                    </div>
                    <div>
                      <h4>{t("输出：模型评价")}</h4>
                      {focused.ranking ? (
                        <>
                          <div className="watchlist-rank">
                            <strong>
                              #{focused.ranking.ensemble_predicted_rank}
                            </strong>
                            <span>
                              {t("当周模型排名")}
                              <br />
                              {t("集成得分")}{" "}
                              {number(focused.ranking.ensemble_ranking_score)}
                            </span>
                          </div>
                          <dl className="watchlist-factors">
                            {[
                              focused.ranking.model_1_percentile,
                              focused.ranking.model_2_percentile,
                              focused.ranking.model_3_percentile,
                            ].map((value, i) => (
                              <div key={i}>
                                <dt>
                                  {t("模型组件 {n} 百分位", { n: i + 1 })}
                                </dt>
                                <dd>{percent(value)}</dd>
                              </div>
                            ))}
                          </dl>
                        </>
                      ) : (
                        <p className="watchlist-missing">
                          {t("该股票在此日期没有保存的模型排名。")}
                        </p>
                      )}
                    </div>
                    <div>
                      <h4>{t("结果：策略配置")}</h4>
                      <p className="watchlist-strategy">
                        {data.strategy_context.strategy.id}
                      </p>
                      {focused.allocation ? (
                        <dl className="watchlist-factors">
                          <div>
                            <dt>{t("目标权重")}</dt>
                            <dd>{percent(focused.allocation.target_weight)}</dd>
                          </div>
                          <div>
                            <dt>{t("实际权重")}</dt>
                            <dd>{percent(focused.allocation.actual_weight)}</dd>
                          </div>
                          <div>
                            <dt>{t("股数")}</dt>
                            <dd>{number(focused.allocation.shares, 0)}</dd>
                          </div>
                        </dl>
                      ) : (
                        <p className="watchlist-missing">
                          {t(
                            focused.selection_status === "not_selected"
                              ? "这只股票没有进入当周保存的策略配置。排名靠前不保证入选。"
                              : "缺少此日期的已验证配置，不能判断是否入选。",
                          )}
                        </p>
                      )}
                      {focused.selection_status === "not_selected" && (
                        <p>
                          {t(
                            "保存结果没有逐股过滤原因，因此不推断具体未入选理由。",
                          )}
                        </p>
                      )}
                      {focused.allocation && (
                        <p>
                          {t(
                            "权重为下一周开盘代理价调仓后的历史配置，包含整数股与现金约束。",
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                  {data.strategy_context.liquidated_at_period_end && (
                    <p className="watchlist-liquidation">
                      <Info size={14} />
                      {t(
                        "最后持有期结束时已清仓，展示的历史配置不代表当前持仓。",
                      )}
                    </p>
                  )}
                  <details className="watchlist-price-details">
                    <summary>{t("查看回测价格与数据来源")}</summary>
                    <p>
                      {t(
                        "价格是下一周开盘和收盘的历史回测代理价，不是当前行情或未来价格预测。",
                      )}
                    </p>
                    <dl className="watchlist-factors">
                      <div>
                        <dt>{t("下一周开盘代理价")}</dt>
                        <dd>{number(focused.prices?.buy_price, 6)}</dd>
                      </div>
                      <div>
                        <dt>{t("下一周收盘代理价")}</dt>
                        <dd>{number(focused.prices?.sell_price, 6)}</dd>
                      </div>
                    </dl>
                    {!focused.prices && (
                      <p>{t("该日期的对齐回测价格不可用。")}</p>
                    )}
                    <p>{t("金额沿用原研究账户单位，币种未声明。")}</p>
                    <code>
                      {runId} · {date}
                    </code>
                    <a
                      href={resultURL}
                      className="text-link"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {t("查看当前关注接口 JSON")}
                      <ArrowRight size={14} />
                    </a>
                  </details>
                </article>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
