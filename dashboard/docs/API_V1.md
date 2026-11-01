# SafeCapital API v1 合同

本地基础地址：`http://127.0.0.1:8000/api/cs5_6_equity/v1/`。仅提供 GET 查询和下载。API 主要版本固定为 v1；新增可选字段不改变主要版本，客户端应忽略未知字段。删除字段或改变字段含义需要新的主要版本。旧 `/api/...` 地址继续兼容，不作为新集成入口。

可导入接口定义：`openapi.json`；运行服务也提供 `/api/openapi.json`。在线 Swagger 地址 `/api/docs` 依赖外部 CDN；离线集成请使用本文件及 OpenAPI JSON。

模块级 `portfolio` 合同、完整字段和成功/无数据/错误口径见 [Portfolio Neo 接入交接](PORTFOLIO_NEO_INTEGRATION.md)。旧 `/api/v1` 也保留为兼容别名。

1.4 新增股票目录、关注查询与当前选择导出，完整字段/状态定义见 [关注股票 API](PRESENTATION_WATCHLIST.md#给客户的新增只读-api)。

## 接口顺序

1. GET `runs`，读取 `default_run_id`，不要把本机运行目录名写死。
2. GET `runs/{id}/inputs` 获取输入目录及可用状态；查询 `inputs/factors/rows` 或 `inputs/prices/rows`。
3. GET `runs/{id}/overview` 获取总览和全部有效信号日期。
4. GET `runs/{id}/equity` 获取完整每周资金序列。
5. GET `runs/{id}/rankings?date=2026-08-28&q=ANF&page=1&page_size=10` 获取排名。
6. GET `runs/{id}/downloads/summary` 下载原始结果。

可执行 JavaScript 示例在 `dashboard/examples/client.mjs`（交付包内同路径）：

```bash
node dashboard/examples/client.mjs http://127.0.0.1:8000/
```

| 接口 | 主要响应字段 |
|---|---|
| `health` | status、verified_runs、rejected_runs；无结果返回 503 |
| `config` | app_version、api_version、public_url、data_mode |
| `runs` | runs 数组、default_run_id（无结果为 null）、rejected_runs |
| `runs/{id}/stocks` | stocks、backtest_dates、ranking_dates、default_date |
| `runs/{id}/watchlist?date=2026-08-28&tickers=SCL,TJX,CMG` | rows、selection_status、strategy_context、provenance；仅查看既有结果 |
| `runs/{id}/watchlist/download?...&format=csv` | 当前日期/股票选择 CSV；format=json 为 JSON |
| `runs/{id}/inputs` | available、reason、run_id、datasets、model |
| `runs/{id}/inputs/{dataset}/rows` | dataset、scope、date、total、page、page_size、rows |
| `runs/{id}/inputs/{dataset}/download` | 完整原始输入 CSV 字节 |
| `runs/{id}/overview` | run、summary、dates、prediction_first_date、prediction_last_date、ticker_count、ranking_notice |
| `runs/{id}/equity` | rows：date、start_capital、end_capital、net_return、cash、fees、drawdown 及原始账户字段 |
| `runs/{id}/rankings` | date、total、page、page_size、rows |
| `runs/{id}/downloads/{kind}` | 原始字节，Content-Disposition 提供下载文件名 |

排名行：ticker、date、ensemble_predicted_rank、ensemble_ranking_score、model_1/2/3_percentile，以及原始模型得分/ID。页码从 1 开始，page_size 为 1–100；q 为大小写不敏感股票代码子串（最长 30 字符）。超过最后一页返回空 rows，total 仍为全部匹配数。不存在的信号日期返回 404，不能用任意自然日代替。

下载种类：predictions、equity、summary、manifest、prediction-verification、backtest-verification。CSV 为 UTF-8 原始结果，不重新格式化数值。

## 输入查询约定

`dataset` 为 `factors` 或 `prices`。`date` 可省略，省略时查询所选范围的全部日期。`scope=output`（默认）只返回与该次输出的日期/股票键对齐的记录；`scope=source` 返回完整源文件范围。输入按日期降序、股票代码升序排列；`q`、`page`、`page_size` 与排名查询相同。有效日期没有匹配记录时，输入查询返回 200、空 rows、total=0（排名接口对不存在日期返回 404）。

- factors：date、ticker、stock_name，以及 revenue_growth_yoy、operating_profitability、cashflow_to_assets、debt_to_assets、asset_growth_yoy 五个原始因子。模型内部还进行周内百分位转换。
- prices：date、ticker、stock_name、buy_price、sell_price。价格为下一周开盘/收盘代理价，用于历史回测。
- 以 date + ticker 关联输入与排名。排名是策略过滤前的结果，不保证每行都有实际交易。回测价格的更早行也可能用于 13 周历史回看。
- datasets 提供 source_rows/source_dates（完整源文件）、output_aligned_rows/output_dates（与输出对齐）、columns（查询字段）、source_columns（原始 CSV 字段）、omitted_columns、sha256 和 bytes。
- 下载总是完整原文件，不受筛选和分页影响；包含 target1/target2 等研究列。查询只返回指定输入字段，未来收益标签不参与预测。
- 启动时核对输入、模型清单及该次结果的文件身份。缺失或不匹配时 catalog 返回 available=false，查询和下载返回 503 inputs_unavailable；已验证的输出仍可用。输入与输出均为启动时快照，更换文件后需要重启。

例如：`runs/{id}/inputs/factors/rows?scope=output&date=2026-08-28&q=ANF&page=1&page_size=10`。

## 字段语义

- total_return、annualized_return、net_return、drawdown、max_drawdown 为小数比例：0.10 表示 10%。
- ensemble_ranking_score 为三组件周内百分位的均值，不是预计收益；rank=1 表示当周最高排名。
- 排名在策略过滤前生成，不代表实际持仓、交易指令或实时市场状态。
- date 是信号日期；end_capital 是对应持有期末资金。数据覆盖与运行时间是不同字段。
- finished_utc 为带时区时间；客户端可转换为用户时区。
- 资金使用原回测计价单位；接口未额外声明币种。
- summary 始终对应完整回测；drawdown 的峰值从完整历史计算，前端筛选展示区间不会重新设置峰值。
- 服务在启动时读取并验证结果；更新磁盘文件后应重启服务。同一进程内图表、API 和下载使用同一内存快照。

## 错误格式

```json
{
  "error": {
    "code": "invalid_request",
    "message": "请求参数不符合接口约定",
    "request_id": "server-generated-id",
    "fields": ["query.date"]
  },
  "detail": "请求参数不符合接口约定"
}
```

| HTTP | code | 客户端处理 |
|---|---|---|
| 404 | not_found | 重新选择已有结果/日期，或修正下载种类 |
| 405 | method_not_allowed | 仅使用 GET |
| 422 | unsupported_stocks | 关注查询含不支持的股票或空选择；从 stocks 目录选择 |
| 422 | invalid_request | 根据 fields 修正参数 |
| 503 | no_verified_results | 展示暂无可用结果，联系维护人员 |
| 503 | inputs_unavailable | 输入缺失或与当前回放不一致；检查 catalog.reason，输出可继续使用 |
| 500 | internal_error | 保留 request_id，联系维护人员 |

每个响应含 `X-Request-ID`。错误不回传服务器路径或堆栈。API 的 Cache-Control 为 no-store。

## 浏览器跨域

嵌入 iframe 不需要 API CORS。客户使用自己的浏览器页面直接请求 API 时，将其精确 origin 添加到 `api_origins`。只授权 GET，未启用 cookie/凭证跨域。允许来源可读取 Content-Disposition 和 X-Request-ID。CORS 和 iframe 域名配置都不是账号认证；若需要客户登录，请在网关同时保护网页、API、下载，并另行确定 SSO 协议。

参考：[FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)、[FastAPI 响应模型](https://fastapi.tiangolo.com/tutorial/response-model/)。
