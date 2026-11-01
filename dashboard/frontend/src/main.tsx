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
  Layers3,
  LayoutDashboard,
  ListOrdered,
  Menu,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import "./styles.css";

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
const api = (path: string) => new URL(`api/v1/${path}`, base).href;
const download = (id: string, kind: string) =>
  api(`runs/${encodeURIComponent(id)}/downloads/${kind}`);
const pct = (n: number, digits = 2) => `${(n * 100).toFixed(digits)}%`;
const money = (n: number) =>
  n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
const time = (s: string) =>
  new Date(s).toLocaleString("zh-CN", { hour12: false });
const embedded =
  new URLSearchParams(window.location.search).get("embed") === "1";
const localEmbeddedURL = new URL("?embed=1", base).href;
async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(api(path), { signal });
  if (!res.ok)
    throw new Error(
      res.status === 404
        ? "未找到对应的结果，请重新选择。"
        : "无法读取结果，请确认 Dashboard 服务正在运行。",
    );
  return res.json();
}
function ErrorBox({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="error" role="alert">
      <CircleHelp size={20} />
      <span>{message}</span>
      {retry && <button onClick={retry}>重试</button>}
    </div>
  );
}
function App() {
  const [publicURL, setPublicURL] = useState("");
  const embeddedURL = publicURL
    ? new URL("?embed=1", publicURL).href
    : localEmbeddedURL;
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
  const [menu, setMenu] = useState(false);
  const [tab, setTab] = useState<"end_capital" | "net_return" | "drawdown">(
    "end_capital",
  );
  const [period, setPeriod] = useState("all");
  const [date, setDate] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [ranking, setRanking] = useState<Ranking | null>(null);
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
        setBundle({ id: runId, overview, equity: equity.rows });
        setDate(overview.dates.at(-1)!);
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
        .then(setRanking)
        .catch((e) => {
          if (e.name !== "AbortError") setRankingError(e.message);
        });
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [runId, date, search, page, bundle, rankingRetry]);

  const overview = bundle?.id === runId ? bundle.overview : null;
  const summary = overview?.summary;
  const allEquity = bundle?.equity ?? [];
  const chartRows =
    period === "all" ? allEquity : allEquity.slice(-Number(period));
  const dateIndex = overview?.dates.indexOf(date) ?? -1;
  const embedCode = `<iframe\n  src="${embeddedURL}"\n  title="SafeCapital 历史策略研究"\n  width="100%" height="1400"\n  style="border:0; border-radius:16px"\n  loading="lazy">\n</iframe>`;
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
    <div className={embedded ? "app embedded" : "app"}>
      {!embedded && (
        <>
          {menu && (
            <button
              aria-label="关闭导航遮罩"
              className="scrim"
              onClick={() => setMenu(false)}
            />
          )}
          <aside className={`sidebar ${menu ? "open" : ""}`}>
            <a className="brand" href="#overview">
              <span className="brand-mark">
                <Activity size={23} />
              </span>
              <span>
                SafeCapital
                <span className="brand-caption">RESEARCH WORKSPACE</span>
              </span>
            </a>
            <div className="workspace-label">
              工作空间 <span>V1</span>
            </div>
            <nav aria-label="主导航">
              <a
                className="nav-link primary"
                href="#overview"
                onClick={() => setMenu(false)}
              >
                <LayoutDashboard size={18} />
                策略总览
                <ArrowUpRight size={14} />
              </a>
              <a
                className="nav-link"
                href="#rankings"
                onClick={() => setMenu(false)}
              >
                <ListOrdered size={18} />
                股票排名
              </a>
              <a
                className="nav-link"
                href="#results"
                onClick={() => setMenu(false)}
              >
                <FileCheck2 size={18} />
                验证与下载
              </a>
              <a
                className="nav-link"
                href="#integration"
                onClick={() => setMenu(false)}
              >
                <Code2 size={18} />
                网站接入
              </a>
            </nav>
            <div className="sidebar-bottom">
              <div className="sidebar-note">
                <ShieldCheck size={22} />
                <strong>每个结果，都有依据</strong>
                <p>读取真实回放记录，展示已通过校验的历史策略结果。</p>
                <span className="dot-label">
                  <i />
                  只读研究模式
                </span>
              </div>
              <div className="sidebar-footer">
                SafeCapital Ensemble <span>1.1</span>
              </div>
            </div>
          </aside>
        </>
      )}
      <div className="main-shell">
        {!embedded && (
          <header className="topbar">
            <div>
              <button
                className="mobile-menu icon-button"
                aria-label="打开导航"
                onClick={() => setMenu(!menu)}
              >
                {menu ? <X size={20} /> : <Menu size={20} />}
              </button>
              <span>研究工作台</span>
              <ChevronRight size={14} />
              <strong>历史策略</strong>
            </div>
            <span className="topbar-status">
              <i />
              历史结果
            </span>
          </header>
        )}
        <main>
          <section className="page-heading" id="overview">
            <div>
              <div className="eyebrow">SAFECAPITAL / ENSEMBLE RESEARCH</div>
              <h1>
                让策略表现，一目了然<span>.</span>
              </h1>
              <p>从每周股票排名，到投资组合的完整历史表现。</p>
            </div>
            <span className="history-badge">
              <Activity size={15} />
              历史回测 · 非实时行情
            </span>
          </section>
          <div className="run-toolbar">
            <div className="run-control">
              <span className="small-icon">
                <Layers3 size={17} />
              </span>
              <label htmlFor="run">结果版本</label>
              <select
                id="run"
                value={runId}
                onChange={(e) => setRunId(e.target.value)}
                disabled={!runs.length}
              >
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    {time(r.finished_utc)} · {r.label}
                  </option>
                ))}
              </select>
            </div>
            {overview && (
              <span className="verified">
                <ShieldCheck size={15} />
                文件哈希校验通过
              </span>
            )}
          </div>
          {error && (
            <ErrorBox message={error} retry={() => setRetry((n) => n + 1)} />
          )}
          {!error && !summary && (
            <div className="loading" role="status">
              <span className="spinner" />
              正在读取已验证的运行结果…
            </div>
          )}
          {summary && overview && (
            <>
              <div className="metric-grid">
                <Metric
                  label="期末账户资金"
                  value={money(summary.final_capital)}
                  note={`初始资金 ${money(summary.initial_capital)}`}
                  icon={<BarChart3 size={18} />}
                  accent
                />
                <Metric
                  label="累计收益"
                  value={`${summary.total_return >= 0 ? "+" : ""}${pct(summary.total_return)}`}
                  note={`年化收益 ${pct(summary.annualized_return)}`}
                  icon={<ArrowUpRight size={18} />}
                  positive={summary.total_return >= 0}
                />
                <Metric
                  label="最大回撤"
                  value={pct(summary.max_drawdown)}
                  note="完整回测区间 · 峰值至谷值"
                  icon={<Activity size={18} />}
                />
                <Metric
                  label="夏普比率"
                  value={summary.sharpe.toFixed(3)}
                  note={`覆盖 ${summary.weeks} 个信号周`}
                  icon={<Layers3 size={18} />}
                />
              </div>
              <div className="chart-layout">
                <section className="panel chart-panel" aria-label="回测图表">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">PORTFOLIO PERFORMANCE</span>
                      <h2>看见资金的每一步</h2>
                    </div>
                    <div className="period-control" aria-label="图表区间">
                      {[
                        ["52", "末 52 周"],
                        ["156", "末 156 周"],
                        ["all", "全部"],
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
                  <div className="chart-tabs" aria-label="图表指标">
                    {(
                      [
                        ["end_capital", "账户资金"],
                        ["net_return", "每周收益"],
                        ["drawdown", "历史回撤"],
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
                    aria-label={`${tab === "end_capital" ? "账户资金" : tab === "net_return" ? "每周净收益率" : "相对历史峰值的回撤"}曲线；完整数值可下载每周资金 CSV`}
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
                              stopColor="#29816b"
                              stopOpacity={0.19}
                            />
                            <stop
                              offset="100%"
                              stopColor="#29816b"
                              stopOpacity={0.015}
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 5"
                          vertical={false}
                          stroke="#e6ebe8"
                        />
                        <XAxis
                          dataKey="date"
                          tickFormatter={(d: string) => d.slice(0, 7)}
                          axisLine={false}
                          tickLine={false}
                          minTickGap={48}
                          tick={{ fontSize: 11, fill: "#7a8981" }}
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
                          tick={{ fontSize: 11, fill: "#7a8981" }}
                          width={52}
                        />
                        <Tooltip
                          formatter={(v: number) => [
                            tab === "end_capital" ? money(v) : pct(v),
                            tab === "end_capital"
                              ? "期末资金"
                              : tab === "net_return"
                                ? "当周净收益"
                                : "历史回撤",
                          ]}
                          labelFormatter={(v) => `信号日期 ${v}`}
                          contentStyle={{
                            borderRadius: 12,
                            border: "1px solid #dbe5df",
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
                          stroke="#21765f"
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
                    横轴为信号日期；资金为对应持有期末值。顶部指标始终对应完整回测区间。
                  </p>
                </section>
                <aside className="panel strategy-panel">
                  <div className="strategy-icon">
                    <Layers3 size={22} />
                  </div>
                  <span className="eyebrow">THE STRATEGY</span>
                  <h2>
                    三个模型组件
                    <br />
                    一个组合策略。
                  </h2>
                  <p className="strategy-description">
                    按周综合模型排名，以过去 13 周非负收益筛选，最多选择 5
                    只股票。
                  </p>
                  <dl>
                    <div>
                      <dt>组合方式</dt>
                      <dd>三组件等权</dd>
                    </div>
                    <div>
                      <dt>模型快照</dt>
                      <dd>{overview.run.models_loaded} 个</dd>
                    </div>
                    <div>
                      <dt>单只目标权重</dt>
                      <dd>20%</dd>
                    </div>
                    <div>
                      <dt>交易成本</dt>
                      <dd>单边 {summary.cost_bps} bps</dd>
                    </div>
                    <div>
                      <dt>调仓频率</dt>
                      <dd>每周</dd>
                    </div>
                  </dl>
                  <a href="#results" className="text-link">
                    查看结果依据
                    <ArrowRight size={16} />
                  </a>
                </aside>
              </div>
              <section className="panel rankings-panel" id="rankings">
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">WEEKLY STOCK RANKINGS</span>
                    <h2>
                      每周股票排名{" "}
                      <span className="count-badge">
                        {overview.ticker_count} 只股票池
                      </span>
                    </h2>
                    <p>{overview.ranking_notice}</p>
                  </div>
                  <a
                    className="button secondary"
                    href={download(runId, "predictions")}
                  >
                    <ArrowDownToLine size={16} />
                    下载全部排名
                  </a>
                </div>
                <div className="table-toolbar">
                  <div className="date-control">
                    <label htmlFor="date">信号日期</label>
                    <button
                      className="icon-button"
                      aria-label="上一个信号周"
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
                      aria-label="下一个信号周"
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
                      aria-label="搜索股票代码"
                      placeholder="搜索股票代码，例如 ANF"
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
                        aria-label="清空搜索"
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
                          <th>排名</th>
                          <th>股票代码</th>
                          <th>
                            集成得分{" "}
                            <span title="三个组件的周内百分位得分的等权平均；不是收益预测">
                              ⓘ
                            </span>
                          </th>
                          <th>组件 1 百分位</th>
                          <th>组件 2 百分位</th>
                          <th>组件 3 百分位</th>
                        </tr>
                      </thead>
                      <tbody>
                        {!ranking ? (
                          <tr>
                            <td colSpan={6} className="table-empty">
                              正在读取排名…
                            </td>
                          </tr>
                        ) : ranking.rows.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="table-empty">
                              没有匹配的股票，试试其他代码。
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
                      ? `共 ${ranking.total} 条匹配结果 · 每页 10 条`
                      : "正在加载"}
                    <span className="desktop-only">
                      {" "}
                      · 分数越高，模型排序越靠前
                    </span>
                  </span>
                  <div>
                    <button
                      className="icon-button"
                      aria-label="上一页"
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
                      aria-label="下一页"
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
                      <h2>真实运行，可追溯</h2>
                    </div>
                    <span className="verified">
                      <ShieldCheck size={16} />
                      校验通过
                    </span>
                  </div>
                  <div className="provenance-stats">
                    <div>
                      <strong>
                        {overview.run.prediction_rows.toLocaleString()}
                      </strong>
                      <span>股票 × 周预测记录</span>
                    </div>
                    <div>
                      <strong>{overview.run.prediction_weeks}</strong>
                      <span>预测信号周</span>
                    </div>
                    <div>
                      <strong>{summary.weeks}</strong>
                      <span>组合回测周</span>
                    </div>
                  </div>
                  <dl>
                    <div>
                      <dt>运行完成时间</dt>
                      <dd>{time(overview.run.finished_utc)}（本地时间）</dd>
                    </div>
                    <div>
                      <dt>预测覆盖</dt>
                      <dd>
                        {overview.prediction_first_date} —{" "}
                        {overview.prediction_last_date}
                      </dd>
                    </div>
                    <div>
                      <dt>回测覆盖</dt>
                      <dd>
                        {summary.first_signal} — {summary.last_signal}
                      </dd>
                    </div>
                    <div>
                      <dt>结果编号</dt>
                      <dd className="mono">{runId}</dd>
                    </div>
                  </dl>
                  {rejected > 0 && (
                    <p className="muted">
                      另有 {rejected} 份不完整或未通过校验的记录，未用于展示。
                    </p>
                  )}
                </div>
                <div className="panel downloads">
                  <span className="eyebrow">TAKE A CLOSER LOOK</span>
                  <h2>把研究结果带走</h2>
                  <p>下载当前版本的原始文件，继续分析或核对。</p>
                  {[
                    ["summary", "回测汇总", "收益、风险与交易成本", "CSV"],
                    ["equity", "每周资金", "210 周账户变化与净收益", "CSV"],
                    [
                      "manifest",
                      "运行校验清单",
                      "运行状态与原始文件哈希",
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
                            ? `${summary.weeks} 周账户变化与净收益`
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
                    <h2>一个模块，接入你的网站</h2>
                    <p>嵌入模式保留全部研究内容，收起独立导航。</p>
                    <div className="integration-actions">
                      <a
                        className="button secondary"
                        href={embeddedURL}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ArrowUpRight size={16} />
                        预览嵌入模式
                      </a>
                      <a
                        className="text-link"
                        href={new URL("embed-example.html", base).href}
                        target="_blank"
                        rel="noreferrer"
                      >
                        查看网站嵌入示例
                        <ArrowRight size={15} />
                      </a>
                    </div>
                    <p className="integration-note">
                      正式接入时，将地址换成部署域名，并在服务端允许客户域名。未配置公开域名时，代码中的本机地址仅供当前设备预览。
                    </p>
                  </div>
                  <div className="code-box">
                    <button onClick={copyEmbed}>
                      {copied ? (
                        <>
                          <Check size={14} />
                          已复制
                        </>
                      ) : (
                        <>
                          <Code2 size={14} />
                          复制代码
                        </>
                      )}
                    </button>
                    <pre tabIndex={0}>{embedCode}</pre>
                    {copyError && <p role="status">{copyError}</p>}
                  </div>
                </section>
              )}
              <footer className="page-footer">
                <span>
                  <ShieldCheck size={16} />
                  历史研究结果不代表未来收益。价格为回测代理值，排名不等同于投资建议。
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
    <App />
  </React.StrictMode>,
);
