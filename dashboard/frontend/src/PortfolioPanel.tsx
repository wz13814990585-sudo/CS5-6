import { useEffect, useState } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  ChevronDown,
  ShieldCheck,
  Info,
} from "lucide-react";
import { useLanguage } from "./i18n";
import { readJSON } from "./api";

type AllocationRow = {
  ticker: string;
  stock_name: string;
  model_rank: number;
  target_weight: number;
  actual_weight: number;
  shares: number;
};
type Portfolio = {
  status: "success" | "partial" | "no_data";
  module_id: string;
  module_version: string;
  run_id: string;
  signal_date: string;
  backtest: {
    dates: string[];
    start: string;
    end: string;
    weeks: number;
    window: string;
  };
  universe: {
    training_count: number | null;
    external_count: number;
    signal_count: number;
    external_tickers: string[];
  };
  model: { component_count: number; snapshot_count: number };
  strategy: { id: string };
  units: { currency: string | null };
  benchmark: {
    status: string;
    name: string | null;
    annualized_return: number | null;
  };
  assumptions: {
    annualization_periods_per_year: number;
    cost_bps_per_side: number;
  };
  allocation: {
    status: string;
    reason: string | null;
    rows: AllocationRow[];
    cash_weight: number | null;
    liquidated_at_period_end: boolean | null;
  };
  provenance: {
    allocation_artifact_sha256: string | null;
    research_engine_sha256: string | null;
    allocation_verification: {
      independent_accounting_checks: number;
      maximum_weekly_error: number;
    } | null;
  };
};
const api = (path: string) =>
  new URL(`api/cs5_6_equity/v1/${path}`, new URL("./", location.href)).href;
const pct = (value: number | null) =>
  value === null ? "—" : `${(value * 100).toFixed(2)}%`;
export default function PortfolioPanel({
  runId,
  date,
  onDateChange,
  onViewRanking,
}: {
  runId: string;
  date: string;
  onDateChange: (date: string) => void;
  onViewRanking: (date: string, ticker: string) => void;
}) {
  const { t } = useLanguage();
  const [data, setData] = useState<Portfolio | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setData(null);
  }, [runId]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    readJSON<Portfolio>(
      api(
        `runs/${encodeURIComponent(runId)}/portfolio${date ? `?date=${date}` : ""}`,
      ),
      controller.signal,
    )
      .then((value) => {
        if (controller.signal.aborted) return;
        setData(value);
        setLoading(false);
      })
      .catch((e) => {
        if (e.name !== "AbortError") {
          setError(e.message);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [runId, date, retry]);
  const current =
    data?.run_id === runId && data.signal_date === date ? data : null;
  const knownDates = data?.run_id === runId ? data.backtest.dates : [];
  return (
    <section id="allocation" className="portfolio-section">
      <div className="section-caption">
        <span>CS5-6 / PORTFOLIO</span>
        <span>{t("历史模拟 · 独立股票池")}</span>
      </div>
      <div className="allocation-grid">
        <div className="panel allocation-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">MODEL-BASED STOCK STRATEGIES</span>
              <h2>{t("策略选中的股票")}</h2>
              <p>
                {t(
                  "查看历史信号对应的配置，区分目标权重与模拟成交后的实际权重。",
                )}
              </p>
            </div>
            <ShieldCheck size={22} />
          </div>
          {error ? (
            <div role="alert" className="error">
              {t("暂时无法读取组合配置；其余研究结果仍可查看。")} {t(error)}
              <button onClick={() => setRetry((n) => n + 1)}>
                {t("重试")}
              </button>
            </div>
          ) : (
            <>
              <div className="allocation-toolbar">
                <label htmlFor="allocation-date">{t("信号日期")}</label>
                <select
                  id="allocation-date"
                  value={date}
                  onChange={(e) => onDateChange(e.target.value)}
                  disabled={!knownDates.length}
                >
                  {!knownDates.includes(date) && date && (
                    <option value={date}>
                      {date} · {t("回测区间外")}
                    </option>
                  )}
                  {knownDates
                    .slice()
                    .reverse()
                    .map((d) => (
                      <option key={d}>{d}</option>
                    ))}
                </select>
                <span>{current?.strategy.id || "Top5_NoLoss13w"}</span>
              </div>
              {loading ? (
                <div className="input-loading" role="status">
                  {t("正在读取已验证的组合配置…")}
                </div>
              ) : current?.allocation.status === "available" ? (
                <>
                  <div className="table-scroll">
                    <table aria-label={t("历史股票配置表")}>
                      <thead>
                        <tr>
                          <th>{t("股票代码")}</th>
                          <th>{t("模型排名")}</th>
                          <th>{t("目标权重")}</th>
                          <th>{t("实际权重")}</th>
                          <th>{t("股数")}</th>
                          <th>{t("对应输出")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {current.allocation.rows.length ? (
                          current.allocation.rows.map((row) => (
                            <tr key={row.ticker}>
                              <td>
                                <strong className="ticker">{row.ticker}</strong>
                                <span
                                  className="allocation-company"
                                  title={row.stock_name}
                                >
                                  {row.stock_name}
                                </span>
                              </td>
                              <td>{row.model_rank}</td>
                              <td>{pct(row.target_weight)}</td>
                              <td>
                                <span className="weight-value">
                                  {pct(row.actual_weight)}
                                </span>
                                <span className="weight-track">
                                  <i
                                    style={{
                                      width: `${row.actual_weight * 100}%`,
                                    }}
                                  />
                                </span>
                              </td>
                              <td>{row.shares.toLocaleString()}</td>
                              <td>
                                <a
                                  className="text-link"
                                  href="#rankings"
                                  onClick={() =>
                                    onViewRanking(
                                      current.signal_date,
                                      row.ticker,
                                    )
                                  }
                                >
                                  {t("查看排名")}
                                  <ArrowRight size={13} />
                                </a>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={6}>
                              {t("本周未选中股票，组合持有现金。")}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div className="allocation-footer">
                    <span>
                      {t("现金权重")}{" "}
                      <strong>{pct(current.allocation.cash_weight)}</strong>
                    </span>
                    <span>{t("配置时点：下一周开盘代理价成交后")}</span>
                  </div>
                  {current.allocation.liquidated_at_period_end && (
                    <p className="allocation-note">
                      <Info size={14} />
                      {t(
                        "此表为最后持有期内的配置；回测结束时已清仓，不代表当前持仓。",
                      )}
                    </p>
                  )}
                </>
              ) : (
                <div className="input-loading" role="status">
                  {t(
                    current?.allocation.status === "no_data"
                      ? "该日期没有组合回测记录。"
                      : "匹配的组合配置暂不可用，未用模型前五名替代。",
                  )}
                </div>
              )}
            </>
          )}
        </div>
        <aside className="panel scope-panel">
          <span className="eyebrow">RESEARCH SCOPE</span>
          <h3>{t("一个明确的研究范围")}</h3>
          <dl>
            <div>
              <dt>{t("训练股票池")}</dt>
              <dd>{current?.universe.training_count ?? "—"}</dd>
            </div>
            <div>
              <dt>{t("独立外部评估股票")}</dt>
              <dd>{current?.universe.external_count ?? "—"}</dd>
            </div>
            <div>
              <dt>{t("当前信号可用股票")}</dt>
              <dd>{current?.universe.signal_count ?? "—"}</dd>
            </div>
            <div>
              <dt>{t("信号频率")}</dt>
              <dd>{t("每周")}</dd>
            </div>
          </dl>
          <p>{t("仅股票，不包含 ETF；与客户页面的单一资产选择器独立。")}</p>
          <div className="benchmark-state">
            <span>{t("基准比较")}</span>
            <strong>{t("不可用")}</strong>
            <p>{t("未提供与本股票池、区间和交易假设一致的已验证基准序列。")}</p>
          </div>
          <div className="scope-period">
            <span>Common210 · FullHistory</span>
            <strong>
              {current
                ? `${current.backtest.start} → ${current.backtest.end}`
                : "—"}
            </strong>
            <small>{t("与报告中的较短最终测试区间分开呈现。")}</small>
          </div>
        </aside>
      </div>
      <details className="panel methodology">
        <summary>
          <span>
            <span className="eyebrow">METHODOLOGY & ONTOLOGY</span>
            <strong>{t("方法、假设与数据关系")}</strong>
          </span>
          <ChevronDown size={18} />
        </summary>
        <div className="methodology-content">
          <div>
            <h3>{t("模型与执行")}</h3>
            <p>
              {t(
                "三个冻结模型组件按周形成排名；使用可观察的过去 13 周非负收益过滤，再选择最多五只股票。",
              )}
            </p>
            <p>
              {t(
                "目标权重每只 20%；整数股、交易费用及现金约束会使实际权重略有差异。",
              )}
            </p>
            <p>
              {t(
                "使用下一周开盘与收盘代理价进行历史模拟，每次买入或卖出收取 10 bps；不表示真实成交。",
              )}
            </p>
            <p>
              {t(
                "年化约定：每年 52 周，(期末资金 / 初始资金)^(52 / 周数) − 1。",
              )}
            </p>
          </div>
          <div>
            <h3>{t("数据边界与来源")}</h3>
            <p>
              {t(
                "完整训练股票池有 66 只，早期快照实际可用股票数随历史数据覆盖而变化；外部 40 只股票与训练股票不重叠。",
              )}
            </p>
            <p>
              {t(
                "原结果未声明币种，金额沿用研究账户单位。财务数据的独立发布时间戳不可用，信号日期不等于发布时间。",
              )}
            </p>
            <p>
              {t(
                "独立命名空间内的关系：模型 → 运行 → 周度信号 → 股票配置 → 回测指标。不会合并客户其他模块的本体或结果。",
              )}
            </p>
            <p>
              {t(
                "配置从既有回测引擎离线导出，与原资金序列逐周核对；页面不会启动训练或实时预测。",
              )}
            </p>
          </div>
          {current?.provenance.allocation_verification && (
            <div className="methodology-evidence">
              <span>
                <ShieldCheck size={15} />
                {t("原资金序列最大误差")}{" "}
                <strong>
                  {
                    current.provenance.allocation_verification
                      .maximum_weekly_error
                  }
                </strong>
              </span>
              <span>
                {t("独立账户核验")}{" "}
                <strong>
                  {current.provenance.allocation_verification.independent_accounting_checks.toLocaleString()}
                </strong>
              </span>
              <a
                href={api(
                  `runs/${encodeURIComponent(runId)}/portfolio?date=${current.signal_date}`,
                )}
                target="_blank"
                rel="noreferrer"
              >
                <ArrowDownToLine size={14} />
                {t("查看模块数据合同 JSON")}
              </a>
            </div>
          )}
        </div>
      </details>
    </section>
  );
}
