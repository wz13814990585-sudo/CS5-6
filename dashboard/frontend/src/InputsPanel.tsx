import { useEffect, useState } from "react";
import { useLanguage } from "./i18n";
import {
  ArrowDownToLine,
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  Code2,
  Database,
  Search,
  ShieldCheck,
} from "lucide-react";

type Dataset = {
  id: "factors" | "prices";
  title: string;
  purpose: string;
  source_file: string;
  sha256: string;
  source_rows: number;
  source_dates: string[];
  output_aligned_rows: number;
  output_dates: string[];
  ticker_count: number;
  columns: { key: string; label: string; type: string }[];
  omitted_columns: string[];
};
type Catalog = {
  available: boolean;
  reason: string | null;
  run_id: string;
  datasets: Dataset[];
  model: {
    component_count: number;
    snapshot_count: number;
    feature_transform: string;
  } | null;
};
type InputRow = { date: string; ticker: string; stock_name: string } & Record<
  string,
  string | number
>;
type Result = { rows: InputRow[]; total: number };
type Props = {
  runId: string;
  outputDates: string[];
  onViewOutput: (date: string, ticker: string) => void;
};
const base = new URL("./", window.location.href);
const endpoint = (path: string) => new URL(`api/v1/${path}`, base).href;
async function read<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(endpoint(path), { signal });
  const body = await response.json();
  if (!response.ok)
    throw new Error(body.error?.message || "暂时无法读取输入数据");
  return body;
}
export default function InputsPanel({
  runId,
  outputDates,
  onViewOutput,
}: Props) {
  const { t } = useLanguage();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [dataset, setDataset] = useState<"factors" | "prices">("factors");
  const [scope, setScope] = useState<"output" | "source">("output");
  const [date, setDate] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [copied, setCopied] = useState("");
  const current = catalog?.run_id === runId ? catalog : null;
  const info = current?.datasets.find((d) => d.id === dataset);
  const dates = info
    ? scope === "output"
      ? info.output_dates
      : info.source_dates
    : [];
  const selectedDate = date || dates.at(-1) || "";
  const params = new URLSearchParams({
    scope,
    date: selectedDate,
    q: search,
    page: String(page),
    page_size: "10",
  });
  const query = `runs/${encodeURIComponent(runId)}/inputs/${dataset}/rows?${params}`;
  const downloadURL = endpoint(
    `runs/${encodeURIComponent(runId)}/inputs/${dataset}/download`,
  );
  useEffect(() => {
    const controller = new AbortController();
    setCatalog(null);
    setResult(null);
    setError("");
    setDate("");
    setSearch("");
    setPage(1);
    read<Catalog>(`runs/${encodeURIComponent(runId)}/inputs`, controller.signal)
      .then(setCatalog)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [runId, retry]);
  useEffect(() => {
    if (!current?.available || !selectedDate) return;
    const controller = new AbortController();
    setResult(null);
    setError("");
    const timer = setTimeout(
      () =>
        read<Result>(query, controller.signal)
          .then(setResult)
          .catch((e) => {
            if (e.name !== "AbortError") setError(e.message);
          }),
      150,
    );
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, current]);
  function reset() {
    setDate("");
    setSearch("");
    setPage(1);
    setResult(null);
  }
  async function copy(value: string, label: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(label);
      setTimeout(() => setCopied(""), 2000);
    } catch {
      setCopied("请选中地址手动复制");
    }
  }
  return (
    <section className="panel inputs-panel" id="inputs">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">INPUTS → MODEL → RESULTS</span>
          <h2>{t("从输入，看懂输出")}</h2>
          <p>
            {t(
              "查看当前运行所对应的现有输入；选择一只股票，即可对照它的输出排名。",
            )}
          </p>
        </div>
        <span className="input-mode">
          <Database size={15} />
          {t("现有数据 · 只读查询")}
        </span>
      </div>
      {error && (
        <div className="error" role="alert">
          {t(error)}
          <button onClick={() => setRetry((n) => n + 1)}>
            {t("重新读取")}
          </button>
        </div>
      )}
      {!current && !error && (
        <div className="input-loading" role="status">
          {t("正在验证输入与本次结果的对应关系…")}
        </div>
      )}
      {current && !current.available && (
        <div className="error">
          {t(current.reason || "暂时无法读取输入数据")}
        </div>
      )}
      {info && current?.available && (
        <>
          <div className="input-flow">
            <div>
              <Database size={18} />
              <span>
                <strong>{t("输入数据")}</strong>
                <small>{t("5 个因子 + 历史回测价格")}</small>
              </span>
            </div>
            <ArrowRight size={17} />
            <div>
              <ShieldCheck size={18} />
              <span>
                <strong>
                  {t("{count} 个模型组件", {
                    count: current.model?.component_count ?? 0,
                  })}
                </strong>
                <small>
                  {t("{count} 个已保存快照", {
                    count: current.model?.snapshot_count ?? 0,
                  })}
                </small>
              </span>
            </div>
            <ArrowRight size={17} />
            <div>
              <span>
                <strong>{t("排名与回测")}</strong>
                <small>{t("按日期和股票代码关联")}</small>
              </span>
            </div>
          </div>
          <div className="input-tabs">
            {current.datasets.map((d) => (
              <button
                key={d.id}
                className={dataset === d.id ? "selected" : ""}
                aria-pressed={dataset === d.id}
                onClick={() => {
                  setDataset(d.id);
                  reset();
                }}
              >
                {t(d.title)}
              </button>
            ))}
            <a className="button secondary" href={downloadURL}>
              <ArrowDownToLine size={15} />
              {t("下载完整输入 CSV")}
            </a>
          </div>
          <div className="input-summary">
            <div>
              <strong>{info.source_rows.toLocaleString()}</strong>
              <span>
                {t("源文件记录 · {count} 个信号周", {
                  count: info.source_dates.length,
                })}
              </span>
            </div>
            <div>
              <strong>{info.output_aligned_rows.toLocaleString()}</strong>
              <span>
                {t(
                  dataset === "factors"
                    ? "与本次预测输出对齐的记录"
                    : "与本次回测输出对齐的记录",
                )}
              </span>
            </div>
            <div>
              <strong>{t("{count} 只", { count: info.ticker_count })}</strong>
              <span>{t("源文件股票池")}</span>
            </div>
            <span className="verified">
              <ShieldCheck size={15} />
              {t("输入与运行记录哈希一致")}
            </span>
          </div>
          <div className="input-explanation">
            <p>{t(info.purpose)}</p>
            <p>
              {t(
                "源文件范围：{start} — {end}。表格显示 6 位小数；接口返回数值，下载保留原始文件。可左右滚动查看全部字段。",
                {
                  start: info.source_dates[0],
                  end: info.source_dates.at(-1) ?? "",
                },
              )}
            </p>
            <code>{info.source_file}</code>
          </div>
          <div className="table-toolbar">
            <div className="input-filters">
              <label htmlFor="input-scope">{t("查看范围")}</label>
              <select
                id="input-scope"
                value={scope}
                onChange={(e) => {
                  setScope(e.target.value as "output" | "source");
                  reset();
                }}
              >
                <option value="output">{t("与本次输出对齐")}</option>
                <option value="source">{t("完整源文件")}</option>
              </select>
              <label htmlFor="input-date">{t("输入日期")}</label>
              <select
                id="input-date"
                value={selectedDate}
                onChange={(e) => {
                  setDate(e.target.value);
                  setPage(1);
                }}
              >
                {[...dates].reverse().map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </div>
            <label className="search">
              <Search size={16} />
              <input
                aria-label={t("搜索输入股票代码")}
                placeholder={t("搜索输入股票代码")}
                value={search}
                maxLength={30}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
              />
            </label>
          </div>
          <div className="table-scroll" aria-busy={!result}>
            <table aria-label={t("输入数据表")}>
              <thead>
                <tr>
                  {info.columns.map((c) => (
                    <th key={c.key} title={c.key}>
                      {t(c.label)}
                    </th>
                  ))}
                  <th className="input-output-link">{t("对应输出")}</th>
                </tr>
              </thead>
              <tbody>
                {!result ? (
                  <tr>
                    <td
                      className="table-empty"
                      colSpan={info.columns.length + 1}
                    >
                      {t("正在读取输入…")}
                    </td>
                  </tr>
                ) : !result.rows.length ? (
                  <tr>
                    <td
                      className="table-empty"
                      colSpan={info.columns.length + 1}
                    >
                      {t("这个日期没有匹配的股票。")}
                    </td>
                  </tr>
                ) : (
                  result.rows.map((row) => (
                    <tr key={`${row.date}-${row.ticker}`}>
                      {info.columns.map((c) => (
                        <td key={c.key} title={String(row[c.key])}>
                          {c.key === "ticker" ? (
                            <strong className="ticker">{row[c.key]}</strong>
                          ) : typeof row[c.key] === "number" ? (
                            (row[c.key] as number).toFixed(6)
                          ) : (
                            <span
                              className={
                                c.key === "stock_name" ? "company-name" : ""
                              }
                            >
                              {row[c.key]}
                            </span>
                          )}
                        </td>
                      ))}
                      <td className="input-output-link">
                        {outputDates.includes(row.date) ? (
                          <a
                            className="text-link"
                            href="#rankings"
                            onClick={() => onViewOutput(row.date, row.ticker)}
                          >
                            {t("查看输出")}
                            <ArrowRight size={13} />
                          </a>
                        ) : (
                          <span className="muted">{t("不在预测区间")}</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="table-footer">
            <span>
              {result
                ? t("共 {count} 条匹配输入 · 每页 10 条", {
                    count: result.total,
                  })
                : t("读取中")}
            </span>
            <div>
              <button
                className="icon-button"
                aria-label={t("输入上一页")}
                disabled={page === 1 || !result}
                onClick={() => setPage((n) => n - 1)}
              >
                <ChevronLeft size={16} />
              </button>
              <span>
                {page} / {Math.max(1, Math.ceil((result?.total ?? 0) / 10))}
              </span>
              <button
                className="icon-button"
                aria-label={t("输入下一页")}
                disabled={!result || page * 10 >= result.total}
                onClick={() => setPage((n) => n + 1)}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
          <div className="input-api">
            <div>
              <Code2 size={17} />
              <strong>{t("当前输入查询接口")}</strong>
              <button
                className="button secondary"
                onClick={() => copy(endpoint(query), "input")}
              >
                {copied === "input" ? <Check size={14} /> : <Code2 size={14} />}
                {t("复制地址")}
              </button>
              <a
                className="text-link"
                href={endpoint(query)}
                target="_blank"
                rel="noreferrer"
              >
                {t("打开 JSON")}
                <ArrowRight size={13} />
              </a>
            </div>
            <code>{endpoint(query)}</code>
            <p>
              {t(
                "仅查询现有数据。完整 CSV 还包含研究标签等列；表格查询只返回上面列出的字段，target1 / target2 不参与预测或选股。",
              )}
            </p>
            {copied && (
              <span role="status">
                {t(copied === "input" ? "接口地址已复制" : copied)}
              </span>
            )}
            <details>
              <summary>{t("字段说明与文件校验")}</summary>
              <div className="input-field-list">
                {info.columns.map((c) => (
                  <div key={c.key}>
                    <code>{c.key}</code>
                    <span>
                      {t(c.label)} · {c.type}
                    </span>
                  </div>
                ))}
              </div>
              <p>
                {t("原文件 SHA-256：")}
                <code>{info.sha256}</code>
              </p>
            </details>
          </div>
        </>
      )}
    </section>
  );
}
