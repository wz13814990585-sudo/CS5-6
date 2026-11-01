import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Code2,
  FileCheck2,
  FlaskConical,
  Layers3,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import "./styles.css";
import InputsPanel from "./InputsPanel";
import PortfolioPanel from "./PortfolioPanel";
import WatchlistPanel from "./WatchlistPanel";
import { readJSON } from "./api";
import "./client-theme.css";
import { LanguageProvider, LanguageSwitcher, useLanguage } from "./i18n";
import { languageURL } from "./i18n-core";

type Run = {
  id: string;
  label: string;
  finished_utc: string;
  models_loaded: number;
  prediction_rows: number;
  prediction_weeks: number;
  backtest_weeks: number;
  manifest_sha256: string;
  status: string;
};
type Summary = {
  initial_capital: number;
  final_capital: number;
  total_return: number;
  annualized_return: number;
  sharpe: number;
  max_drawdown: number;
  weeks: number;
  first_signal: string;
  last_signal: string;
  cost_bps: number;
  win_rate: number;
  total_fees: number;
  strategy: string;
};
type Overview = {
  run: Run;
  summary: Summary;
  dates: string[];
  prediction_first_date: string;
  prediction_last_date: string;
  ticker_count: number;
  ranking_notice: string;
};
type Equity = {
  date: string;
  end_capital: number;
  start_capital: number;
  net_return: number;
  cash: number;
  fees: number;
  drawdown: number;
};
type Rank = {
  ticker: string;
  ensemble_predicted_rank: number;
  ensemble_ranking_score: number;
  model_1_percentile: number;
  model_2_percentile: number;
  model_3_percentile: number;
};
type Ranking = { rows: Rank[]; total: number };
const base = new URL("./", window.location.href);
const api = (path: string) => new URL(`api/cs5_6_equity/v1/${path}`, base).href;
const download = (id: string, kind: string) =>
  api(`runs/${encodeURIComponent(id)}/downloads/${kind}`);
const pct = (n: number, digits = 2) => `${(n * 100).toFixed(digits)}%`;
const money = (n: number) =>
  n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
const embedded =
  new URLSearchParams(window.location.search).get("embed") === "1";
async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  return readJSON<T>(api(path), signal);
}
function ErrorBox({ message, retry }: { message: string; retry?: () => void }) {
  const { t } = useLanguage();
  return (
    <div className="error" role="alert">
      <CircleHelp size={20} />
      <span>{t(message)}</span>
      {retry && <button onClick={retry}>{t("重试")}</button>}
    </div>
  );
}
function App() {
  const { language, t } = useLanguage();
  const time = (value: string) =>
    new Date(value).toLocaleString(language === "zh" ? "zh-CN" : "en-AU", {
      hour12: false,
    });
  const [publicURL, setPublicURL] = useState("");
  const embeddedURL = languageURL(
    new URL("?embed=1", publicURL || base).href,
    language,
  );
  const [runs, setRuns] = useState<Run[]>([]);
  const [runId, setRunId] = useState("");
  const [rejected, setRejected] = useState(0);
  const [bundle, setBundle] = useState<{
    id: string;
    overview: Overview;
    equity: Equity[];
  } | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [section, setSection] = useState(window.location.hash || "#overview");
  useEffect(() => {
    const update = () => setSection(window.location.hash || "#overview");
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  const [tab, setTab] = useState<"end_capital" | "net_return" | "drawdown">(
    "end_capital",
  );
  const [period, setPeriod] = useState("all");
  const [date, setDate] = useState("");
  const [demoReset, setDemoReset] = useState(0);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [rankingResult, setRanking] = useState<{
    key: string;
    value: Ranking;
  } | null>(null);
  const rankingKey = `${runId}|${date}|${search}|${page}`;
  const ranking =
    rankingResult?.key === rankingKey ? rankingResult.value : null;
  const [rankingError, setRankingError] = useState("");
  const [rankingRetry, setRankingRetry] = useState(0);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setError("");
    get<{ public_url: string }>("config", controller.signal)
      .then((c) =>
        setPublicURL(c.public_url ? c.public_url.replace(/\/?$/, "/") : ""),
      )
      .catch(() => {});
    get<{ runs: Run[]; default_run_id: string | null; rejected_runs: number }>(
      "runs",
      controller.signal,
    )
      .then((data) => {
        if (!data.default_run_id)
          throw new Error(
            "没有可用的已验证结果。请先运行默认流程，再重启 Dashboard 服务。",
          );
        setRuns(data.runs);
        setRejected(data.rejected_runs);
        setRunId((current) =>
          data.runs.some((r) => r.id === current)
            ? current
            : data.default_run_id!,
        );
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [retry]);
  useEffect(() => {
    if (!runId) return;
    const controller = new AbortController();
    setError("");
    setBundle(null);
    setRanking(null);
    Promise.all([
      get<Overview>(`runs/${runId}/overview`, controller.signal),
      get<{ rows: Equity[] }>(`runs/${runId}/equity`, controller.signal),
    ])
      .then(([overview, equity]) => {
        if (controller.signal.aborted) return;
        setBundle({ id: runId, overview, equity: equity.rows });
        setDate(equity.rows.at(-1)!.date);
        setPage(1);
        setSearch("");
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [runId, retry]);
  useEffect(() => {
    if (!date || !bundle || bundle.id !== runId) return;
    const controller = new AbortController();
    setRanking(null);
    setRankingError("");
    const params = new URLSearchParams({
      date,
      q: search,
      page: String(page),
      page_size: "10",
    });
    const timer = window.setTimeout(() => {
      get<Ranking>(`runs/${runId}/rankings?${params}`, controller.signal)
        .then((value) => {
          if (!controller.signal.aborted)
            setRanking({ key: rankingKey, value });
        })
        .catch((e) => {
          if (e.name !== "AbortError") setRankingError(e.message);
        });
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [runId, date, search, page, bundle, rankingRetry]);

  useEffect(() => {
    if (embedded && window.parent !== window)
      window.parent.postMessage(
        { type: "cs5_6_equity:ready", version: "1.4.0" },
        "*",
      );
  }, []);
  function changeDate(value: string) {
    setDate(value);
    setPage(1);
  }
  function resetDemo(value?: string) {
    setDate(value || bundle?.equity.at(-1)?.date || "");
    setSearch("");
    setPage(1);
    setTab("end_capital");
    setPeriod("all");
    setDemoReset((n) => n + 1);
  }
  const overview = bundle?.id === runId ? bundle.overview : null;
  const summary = overview?.summary;
  const allEquity = bundle?.equity ?? [];
  const chartRows =
    period === "all" ? allEquity : allEquity.slice(-Number(period));
  const dateIndex = overview?.dates.indexOf(date) ?? -1;
  const embedCode = `<iframe\n  src="${embeddedURL}"\n  title="${t("SafeCapital 历史策略研究")}"\n  width="100%" height="1400"\n  style="border:0; border-radius:16px"\n  loading="lazy">\n</iframe>`;
  async function copyEmbed() {
    try {
      await navigator.clipboard.writeText(embedCode);
      setCopied(true);
      setCopyError("");
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopyError("浏览器不允许复制，请选中下面的代码手动复制。");
    }
  }
  return (
    <div className={embedded ? "app cs5-module embedded" : "app cs5-module"}>
      <div className="main-shell">
        <header className="module-header">
          <a href="#overview" className="module-brand">
            <span>
              <FlaskConical size={21} />
            </span>
            <div>
              SafeCapital<small>STRATEGY LAB</small>
            </div>
          </a>
          <span className="module-status">
            <i />
            CS5-6 · {t("历史模拟")}
          </span>
          <LanguageSwitcher />
        </header>
        <nav className="module-tabs" aria-label={t("主导航")}>
          {[
            ["watchlist", "关注股票"],
            ["performance", "组合表现"],
            ["allocation", "股票与权重"],
            ["inputs", "输入数据"],
            ["rankings", "股票排名"],
            ["results", "验证与下载"],
            ...(!embedded ? [["integration", "输入输出接口"]] : []),
          ].map(([id, label]) => (
            <a
              key={id}
              href={`#${id}`}
              className={section === `#${id}` ? "active" : ""}
              aria-current={section === `#${id}` ? "location" : undefined}
            >
              {t(label)}
            </a>
          ))}
        </nav>
        <main>
          <section className="page-heading" id="overview">
            <div>
              <div className="eyebrow">
                CS5-6 RESEARCH · INDEPENDENT EQUITY MODULE
              </div>
              <h1>
                {t("基于模型的")}
                <br />
                <span>{t("股票策略")}</span>
              </h1>
              <p>
                {t("从关注的股票出发，查看真实输入、模型排名与历史策略结果。")}
              </p>
            </div>
            <span className="history-badge">
              <Activity size={15} />
              {t("历史回测 · 非实时行情")}
            </span>
          </section>
          <div className="run-toolbar">
            <div className="run-control">
              <span className="small-icon">
                <Layers3 size={17} />
              </span>
              <label htmlFor="run">{t("结果版本")}</label>
              <select
                id="run"
                value={runId}
                onChange={(e) => setRunId(e.target.value)}
                disabled={!runs.length}
              >
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    {time(r.finished_utc)} · {t(r.label)}
                  </option>
                ))}
              </select>
            </div>
            {overview && (
              <span className="verified">
                <ShieldCheck size={15} />
                {t("文件哈希校验通过")}
              </span>
            )}
          </div>
          {error && (
            <ErrorBox message={error} retry={() => setRetry((n) => n + 1)} />
          )}
          {!error && !summary && (
            <div className="loading" role="status">
              <span className="spinner" />
              {t("正在读取已验证的运行结果…")}
            </div>
          )}
          {summary && overview && (
            <>
              <WatchlistPanel
                runId={runId}
                date={date}
                dates={allEquity.map((r) => r.date)}
                onDateChange={changeDate}
                onReset={() => resetDemo()}
                onExample={resetDemo}
              />
              <div className="performance-context" id="performance">
                <div>
                  <span className="eyebrow">
                    ORIGINAL STRATEGY · FULL BACKTEST
                  </span>
                  <h2>{t("原策略完整组合表现")}</h2>
                  <p>
                    {t(
                      "以下指标覆盖原策略完整回测，不是关注股票组成的新组合收益。",
                    )}
                  </p>
                </div>
                <span>
                  {summary.first_signal} → {summary.last_signal}
                </span>
              </div>
              <div className="metric-grid">
                <Metric
                  label={t("年化收益")}
                  value={pct(summary.annualized_return)}
                  note={t("完整区间 · 每年 52 周")}
                  icon={<ArrowUpRight size={18} />}
                  accent
                />

                <Metric
                  label={t("期末账户资金")}
                  value={money(summary.final_capital)}
                  note={t("初始研究资金 {value}", {
                    value: money(summary.initial_capital),
                  })}
                  icon={<BarChart3 size={18} />}
                />
                <Metric
                  label={t("累计收益")}
                  value={`${summary.total_return >= 0 ? "+" : ""}${pct(summary.total_return)}`}
                  note={t("年化收益 {value}", {
                    value: pct(summary.annualized_return),
                  })}
                  icon={<ArrowUpRight size={18} />}
                  positive={summary.total_return >= 0}
                />
                <Metric
                  label={t("最大回撤")}
                  value={pct(summary.max_drawdown)}
                  note={t("完整回测区间 · 峰值至谷值")}
                  icon={<Activity size={18} />}
                />
                <Metric
                  label={t("夏普比率")}
                  value={summary.sharpe.toFixed(3)}
                  note={t("覆盖 {count} 个信号周", { count: summary.weeks })}
                  icon={<Layers3 size={18} />}
                />
              </div>
              <div className="chart-layout">
                <section
                  className="panel chart-panel"
                  aria-label={t("回测图表")}
                >
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">PORTFOLIO PERFORMANCE</span>
                      <h2>{t("看见资金的每一步")}</h2>
                    </div>
                    <div className="period-control" aria-label={t("图表区间")}>
                      {[
                        ["52", t("末 52 周")],
                        ["156", t("末 156 周")],
                        ["all", t("全部")],
                      ].map(([key, label]) => (
                        <button
                          key={key}
                          aria-pressed={period === key}
                          className={period === key ? "selected" : ""}
                          onClick={() => setPeriod(key)}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="chart-tabs" aria-label={t("图表指标")}>
                    {(
                      [
                        ["end_capital", t("账户资金")],
                        ["net_return", t("每周收益")],
                        ["drawdown", t("历史回撤")],
                      ] as const
                    ).map(([key, label]) => (
                      <button
                        key={key}
                        aria-pressed={tab === key}
                        className={tab === key ? "active" : ""}
                        onClick={() => setTab(key)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <div
                    className="chart"
                    role="img"
                    aria-label={t("{metric}曲线；完整数值可下载每周资金 CSV", {
                      metric: t(
                        tab === "end_capital"
                          ? "账户资金"
                          : tab === "net_return"
                            ? "每周净收益率"
                            : "相对历史峰值的回撤",
                      ),
                    })}
                  >
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={chartRows}
                        margin={{ top: 20, right: 14, bottom: 0, left: 2 }}
                        accessibilityLayer
                      >
                        <defs>
                          <linearGradient
                            id="capitalFill"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="0%"
                              stopColor="#49c9a5"
                              stopOpacity={0.19}
                            />
                            <stop
                              offset="100%"
                              stopColor="#49c9a5"
                              stopOpacity={0.015}
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 5"
                          vertical={false}
                          stroke="#243632"
                        />
                        <XAxis
                          dataKey="date"
                          tickFormatter={(d: string) => d.slice(0, 7)}
                          axisLine={false}
                          tickLine={false}
                          minTickGap={48}
                          tick={{ fontSize: 11, fill: "#819992" }}
                          dy={10}
                        />
                        <YAxis
                          domain={["auto", "auto"]}
                          tickFormatter={(n) =>
                            tab === "end_capital"
                              ? `${(Number(n) / 1000).toFixed(0)}k`
                              : pct(Number(n), 0)
                          }
                          axisLine={false}
                          tickLine={false}
                          tick={{ fontSize: 11, fill: "#819992" }}
                          width={52}
                        />
                        <Tooltip
                          formatter={(v: number) => [
                            tab === "end_capital" ? money(v) : pct(v),
                            tab === "end_capital"
                              ? t("期末资金")
                              : tab === "net_return"
                                ? t("当周净收益")
                                : t("历史回撤"),
                          ]}
                          labelFormatter={(v) =>
                            t("信号日期 {date}", { date: String(v) })
                          }
                          contentStyle={{
                            borderRadius: 12,
                            border: "1px solid #29453d",
                            background: "#101e1b",
                            color: "#e7f3ee",
                            boxShadow: "0 8px 24px #20392b12",
                            fontSize: 12,
                          }}
                        />
                        {tab !== "end_capital" && (
                          <ReferenceLine y={0} stroke="#aabbb2" />
                        )}
                        <Area
                          type="linear"
                          dataKey={tab}
                          stroke="#53d0ad"
                          strokeWidth={2}
                          fill="url(#capitalFill)"
                          isAnimationActive={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="chart-caption">
                    <span>
                      <i />
                      Frozen Ensemble · Top5_NoLoss13w
                    </span>
                    <span>
                      {chartRows[0]?.date} — {chartRows.at(-1)?.date}
                    </span>
                  </div>
                  <p className="chart-footnote">
                    {t(
                      "横轴为信号日期；资金为对应持有期末值。顶部指标始终对应完整回测区间。",
                    )}
                  </p>
                </section>
                <aside className="panel strategy-panel">
                  <div className="strategy-icon">
                    <Layers3 size={22} />
                  </div>
                  <span className="eyebrow">THE STRATEGY</span>
                  <h2>
                    {t("三个模型组件")}
                    <br />
                    {t("一个组合策略。")}
                  </h2>
                  <p className="strategy-description">
                    {t(
                      "按周综合模型排名，以过去 13 周非负收益筛选，最多选择 5 只股票。",
                    )}
                  </p>
                  <dl>
                    <div>
                      <dt>{t("组合方式")}</dt>
                      <dd>{t("三组件等权")}</dd>
                    </div>
                    <div>
                      <dt>{t("模型快照")}</dt>
                      <dd>
                        {t("{count} 个", { count: overview.run.models_loaded })}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("单只目标权重")}</dt>
                      <dd>20%</dd>
                    </div>
                    <div>
                      <dt>{t("交易成本")}</dt>
                      <dd>
                        {t("单边 {cost} bps", { cost: summary.cost_bps })}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("调仓频率")}</dt>
                      <dd>{t("每周")}</dd>
                    </div>
                  </dl>
                  <a href="#results" className="text-link">
                    {t("查看结果依据")}
                    <ArrowRight size={16} />
                  </a>
                </aside>
              </div>
              <PortfolioPanel
                runId={runId}
                date={date}
                onDateChange={changeDate}
                onViewRanking={(signalDate, ticker) => {
                  setDate(signalDate);
                  setSearch(ticker);
                  setPage(1);
                }}
              />
              <InputsPanel
                key={`${runId}-${demoReset}`}
                runId={runId}
                sharedDate={date}
                onDateChange={changeDate}
                outputDates={overview.dates}
                onViewOutput={(inputDate, ticker) => {
                  setDate(inputDate);
                  setSearch(ticker);
                  setPage(1);
                }}
              />
              <section className="panel rankings-panel" id="rankings">
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">WEEKLY STOCK RANKINGS</span>
                    <h2>
                      {t("每周股票排名")}{" "}
                      <span className="count-badge">
                        {t("{count} 只股票池", {
                          count: overview.ticker_count,
                        })}
                      </span>
                    </h2>
                    <p>{t(overview.ranking_notice)}</p>
                  </div>
                  <a
                    className="button secondary"
                    href={download(runId, "predictions")}
                  >
                    <ArrowDownToLine size={16} />
                    {t("下载全部排名")}
                  </a>
                </div>
                <div className="table-toolbar">
                  <div className="date-control">
                    <label htmlFor="date">{t("信号日期")}</label>
                    <button
                      className="icon-button"
                      aria-label={t("上一个信号周")}
                      disabled={dateIndex <= 0}
                      onClick={() => {
                        setDate(overview.dates[dateIndex - 1]);
                        setPage(1);
                      }}
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <select
                      id="date"
                      value={date}
                      onChange={(e) => {
                        setDate(e.target.value);
                        setPage(1);
                      }}
                    >
                      {[...overview.dates].reverse().map((d) => (
                        <option key={d}>{d}</option>
                      ))}
                    </select>
                    <button
                      className="icon-button"
                      aria-label={t("下一个信号周")}
                      disabled={dateIndex >= overview.dates.length - 1}
                      onClick={() => {
                        setDate(overview.dates[dateIndex + 1]);
                        setPage(1);
                      }}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                  <label className="search">
                    <Search size={16} />
                    <input
                      aria-label={t("搜索股票代码")}
                      placeholder={t("搜索股票代码，例如 ANF")}
                      value={search}
                      maxLength={30}
                      onChange={(e) => {
                        setSearch(e.target.value);
                        setPage(1);
                      }}
                    />
                    {search && (
                      <button
                        className="icon-button"
                        aria-label={t("清空搜索")}
                        onClick={() => {
                          setSearch("");
                          setPage(1);
                        }}
                      >
                        <X size={14} />
                      </button>
                    )}
                  </label>
                </div>
                {rankingError ? (
                  <ErrorBox
                    message={rankingError}
                    retry={() => setRankingRetry((n) => n + 1)}
                  />
                ) : (
                  <div className="table-scroll" aria-busy={!ranking}>
                    <table>
                      <thead>
                        <tr>
                          <th>{t("排名")}</th>
                          <th>{t("股票代码")}</th>
                          <th>
                            {t("集成得分")}{" "}
                            <span
                              title={t(
                                "三个组件的周内百分位得分的等权平均；不是收益预测",
                              )}
                            >
                              ⓘ
                            </span>
                          </th>
                          <th>{t("组件 1 百分位")}</th>
                          <th>{t("组件 2 百分位")}</th>
                          <th>{t("组件 3 百分位")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {!ranking ? (
                          <tr>
                            <td colSpan={6} className="table-empty">
                              {t("正在读取排名…")}
                            </td>
                          </tr>
                        ) : ranking.rows.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="table-empty">
                              {t("没有匹配的股票，试试其他代码。")}
                            </td>
                          </tr>
                        ) : (
                          ranking.rows.map((r) => (
                            <tr key={r.ticker}>
                              <td>
                                <span
                                  className={`rank ${r.ensemble_predicted_rank <= 3 ? "top" : ""}`}
                                >
                                  {String(r.ensemble_predicted_rank).padStart(
                                    2,
                                    "0",
                                  )}
                                </span>
                              </td>
                              <td>
                                <strong className="ticker">{r.ticker}</strong>
                              </td>
                              <td>
                                <div className="score">
                                  <span>
                                    {r.ensemble_ranking_score.toFixed(4)}
                                  </span>
                                  <div className="score-track">
                                    <div
                                      style={{
                                        width: `${r.ensemble_ranking_score * 100}%`,
                                      }}
                                    />
                                  </div>
                                </div>
                              </td>
                              <td>{pct(r.model_1_percentile, 1)}</td>
                              <td>{pct(r.model_2_percentile, 1)}</td>
                              <td>{pct(r.model_3_percentile, 1)}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
                <div className="table-footer">
                  <span>
                    {ranking
                      ? t("共 {count} 条匹配结果 · 每页 10 条", {
                          count: ranking.total,
                        })
                      : t("正在加载")}
                    <span className="desktop-only">
                      {" "}
                      {t("· 分数越高，模型排序越靠前")}
                    </span>
                  </span>
                  <div>
                    <button
                      className="icon-button"
                      aria-label={t("上一页")}
                      disabled={page <= 1 || !ranking}
                      onClick={() => setPage((p) => p - 1)}
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <span>
                      {page} /{" "}
                      {Math.max(1, Math.ceil((ranking?.total ?? 0) / 10))}
                    </span>
                    <button
                      className="icon-button"
                      aria-label={t("下一页")}
                      disabled={!ranking || page * 10 >= ranking.total}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              </section>
              <section className="results-grid" id="results">
                <div className="panel provenance">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">VERIFIED & TRACEABLE</span>
                      <h2>{t("真实运行，可追溯")}</h2>
                    </div>
                    <span className="verified">
                      <ShieldCheck size={16} />
                      {t("校验通过")}
                    </span>
                  </div>
                  <div className="provenance-stats">
                    <div>
                      <strong>
                        {overview.run.prediction_rows.toLocaleString()}
                      </strong>
                      <span>{t("股票 × 周预测记录")}</span>
                    </div>
                    <div>
                      <strong>{overview.run.prediction_weeks}</strong>
                      <span>{t("预测信号周")}</span>
                    </div>
                    <div>
                      <strong>{summary.weeks}</strong>
                      <span>{t("组合回测周")}</span>
                    </div>
                  </div>
                  <dl>
                    <div>
                      <dt>{t("运行完成时间")}</dt>
                      <dd>
                        {t("{time}（本地时间）", {
                          time: time(overview.run.finished_utc),
                        })}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("预测覆盖")}</dt>
                      <dd>
                        {overview.prediction_first_date} —{" "}
                        {overview.prediction_last_date}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("回测覆盖")}</dt>
                      <dd>
                        {summary.first_signal} — {summary.last_signal}
                      </dd>
                    </div>
                    <div>
                      <dt>{t("结果编号")}</dt>
                      <dd className="mono">{runId}</dd>
                    </div>
                  </dl>
                  {rejected > 0 && (
                    <p className="muted">
                      {t(
                        "另有 {count} 份不完整或未通过校验的记录，未用于展示。",
                        { count: rejected },
                      )}
                    </p>
                  )}
                </div>
                <div className="panel downloads">
                  <span className="eyebrow">TAKE A CLOSER LOOK</span>
                  <h2>{t("把研究结果带走")}</h2>
                  <p>{t("下载当前版本的原始文件，继续分析或核对。")}</p>
                  {[
                    [
                      "summary",
                      t("回测汇总"),
                      t("收益、风险与交易成本"),
                      "CSV",
                    ],
                    [
                      "equity",
                      t("每周资金"),
                      t("210 周账户变化与净收益"),
                      "CSV",
                    ],
                    [
                      "manifest",
                      t("运行校验清单"),
                      t("运行状态与原始文件哈希"),
                      "JSON",
                    ],
                  ].map(([kind, title, desc, format]) => (
                    <a
                      className="download-row"
                      key={kind}
                      href={download(runId, kind)}
                    >
                      <span className="file-icon">
                        <FileCheck2 size={19} />
                      </span>
                      <span>
                        <strong>{title}</strong>
                        <small>
                          {kind === "equity"
                            ? t("{count} 周账户变化与净收益", {
                                count: summary.weeks,
                              })
                            : desc}
                        </small>
                      </span>
                      <span className="file-format">{format}</span>
                      <ArrowDownToLine size={17} />
                    </a>
                  ))}
                </div>
              </section>
              {!embedded && (
                <section className="panel integration" id="integration">
                  <div>
                    <span className="eyebrow">BUILT TO CONNECT</span>
                    <h2>{t("输入与输出，都有查询接口")}</h2>
                    <p>
                      {t(
                        "直接读取现有输入和已验证结果，也可以嵌入完整 Dashboard。",
                      )}
                    </p>
                    <div className="io-links">
                      <a
                        href={api(`runs/${runId}/portfolio?date=${date}`)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {t("查看模块数据合同 JSON")}
                        <ArrowUpRight size={13} />
                      </a>
                      <a
                        href={api(`runs/${runId}/stocks`)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {t("可关注股票清单 JSON")}
                        <ArrowUpRight size={13} />
                      </a>
                      <a
                        href={api(`runs/${runId}/inputs`)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {t("输入清单 JSON")}
                        <ArrowUpRight size={13} />
                      </a>
                      <a
                        href={api(
                          `runs/${runId}/rankings?date=${date}&page_size=10`,
                        )}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {t("当前日期输出排名")}
                        <ArrowUpRight size={13} />
                      </a>
                      <a
                        href={api(`runs/${runId}/overview`)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {t("输出汇总 JSON")}
                        <ArrowUpRight size={13} />
                      </a>
                      <a
                        href={new URL("api/docs", base).href}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {t("完整 API 文档")}
                        <ArrowUpRight size={13} />
                      </a>
                    </div>
                    <div className="integration-actions">
                      <a
                        className="button secondary"
                        href={embeddedURL}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ArrowUpRight size={16} />
                        {t("预览嵌入模式")}
                      </a>
                      <a
                        className="text-link"
                        href={languageURL(
                          new URL("embed-example.html", base).href,
                          language,
                        )}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {t("查看网站嵌入示例")}
                        <ArrowRight size={15} />
                      </a>
                    </div>
                    <p className="integration-note">
                      {t(
                        "正式接入时，将地址换成部署域名，并在服务端允许客户域名。未配置公开域名时，代码中的本机地址仅供当前设备预览。",
                      )}
                    </p>
                  </div>
                  <div className="code-box">
                    <button onClick={copyEmbed}>
                      {copied ? (
                        <>
                          <Check size={14} />
                          {t("已复制")}
                        </>
                      ) : (
                        <>
                          <Code2 size={14} />
                          {t("复制代码")}
                        </>
                      )}
                    </button>
                    <pre tabIndex={0}>{embedCode}</pre>
                    {copyError && <p role="status">{t(copyError)}</p>}
                  </div>
                </section>
              )}
              <footer className="page-footer">
                <span>
                  <ShieldCheck size={16} />
                  {t(
                    "历史研究结果不代表未来收益。价格为回测代理值，排名不等同于投资建议。",
                  )}
                </span>
                <span>SafeCapital · Research with evidence</span>
              </footer>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
function Metric({
  label,
  value,
  note,
  icon,
  accent,
  positive,
}: {
  label: string;
  value: string;
  note: string;
  icon: React.ReactNode;
  accent?: boolean;
  positive?: boolean;
}) {
  return (
    <article className={`metric ${accent ? "accent" : ""}`}>
      <div className="metric-label">
        {label}
        {icon}
      </div>
      <div className={`metric-value ${positive ? "positive" : ""}`}>
        {value}
      </div>
      <div className="metric-note">{note}</div>
    </article>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <LanguageProvider>
      <App />
    </LanguageProvider>
  </React.StrictMode>,
);
