# Dashboard 1.4：关注股票演示与接口

本版用于本地 presentation：选择关注股票，查看已有输入、模型排名和实际策略配置。所有数据来自已验证历史回放，选择关注股票不会触发新预测、重新筛选策略或计算新组合收益。客户现有网站仍需在其测试环境接入和验收。

## 开始演示

在项目根目录运行（若 8000 已有 Dashboard 服务，不要重复启动）：

```bash
.venv-dashboard/bin/python dashboard/start.py
```

打开 [中文演示](http://127.0.0.1:8000/?lang=zh#watchlist) 或 [English](http://127.0.0.1:8000/?lang=en#watchlist)。本机地址只供当前电脑访问；远程会议使用屏幕共享。

建议按以下顺序演示 6–8 分钟：

| 步骤 | 操作 | 讲解要点 |
|---|---|---|
| 1. 准备 | 点击「重置演示」，再点击「载入演示示例」 | 重置关注、日期、输入/排名搜索与分页、图表指标及区间。示例为 SCL、TJX、CMG，日期 2026-08-28。 |
| 2. 用户选择 | 搜索 `Chipotle` 或 `CMG`，点击建议；再尝试 `URBN` | 支持代码/公司名称搜索、多选、移除、清空；仅限本模块已有的 40 只外部评估股票，重复选择不会增加重复行。 |
| 3. 集中结果 | 回到示例，查看三只股票的排名和状态 | SCL 排名 1、已入选；TJX 排名 2、未入选；CMG 排名 3、已入选。排名与实际策略配置是两种输出。 |
| 4. 输入输出 | 点击 TJX 的「查看详情」 | 左侧五个原始因子，中间模型排名/得分/三组件百分位，右侧策略状态。得分不代表预计收益。原结果没有逐股排除原因，因此不会生成解释。 |
| 5. 历史日期 | 在「统一历史信号日期」选择 2022-08-26，或使用左右箭头 | 关注结果、股票与权重、排名、对齐输入共享一个日期；日期改变后会清空旧显示并读取新结果。 |
| 6. 原策略收益 | 点击「查看原策略表现」 | 资金、收益、回撤对应原策略完整组合；选几只关注股票不会改变这些指标。年化约 10.44%、累计约 49.33%，范围 2022-08-26 至 2026-08-28。 |
| 7. 带走结果 | 回到关注结果，点击「导出当前 CSV」或「导出 JSON」 | 导出仅包含当前结果版本、当前日期和关注股票；原始数据下载仍是完整源文件。 |
| 8. 接入演示 | 打开「输入输出接口」及网站嵌入示例 | 客户可嵌入完整模块，也可按下面的接口做自己的界面。 |

可使用的开场说明：

> 用户先选择想关注的股票。我们把同一个历史信号日期的因子输入、模型排名和实际策略配置关联起来，让用户看懂已有研究结果。关注列表是查看偏好；下方收益始终对应原始策略完整组合。

## 演示边界和异常情况

- 输入 `AAPL`：提示不在当前研究股票池，不会为未支持的股票编造结果。
- 在「股票排名」选择 `2019-08-30`：日期同步到其他区域，关注表显示「该日期无配置」。SCL/TJX 可有排名而没有回测配置；CMG 当周没有保存的排名。这与「未入选策略」不同。
- 五个因子显示原始数值；模型使用同周股票百分位转换后的输入。研究标签 `target1/target2` 不作为输入查询字段。
- 展示的权重属于下一周开盘代理价调仓后配置。最终持有期结束时已经清仓，这些不是当前真实持仓。
- 回测价格是历史下一周开盘/收盘代理价；资金沿用研究账户单位，币种未声明。
- 「完整源文件」允许独立浏览 2015 年起的数据，不改变统一研究日期；「与本次输出对齐」才共享日期。
- 关注列表保存在当前浏览器本地；不上传用户偏好、不建立客户账号。刷新后保留关注股票，日期恢复到该运行最新回测日期。跨域 iframe 的存储行为取决于浏览器策略，不承诺跨设备/跨站同步。
- 请求超过 12 秒时显示超时和重试；切换筛选会取消旧请求，防止旧结果覆盖新日期。CSV/JSON 导出仅在当前查询有响应后显示。
- 本地嵌入示例使用模块就绪消息；12 秒未收到时展示重试及独立打开入口，父页面仍可操作。模块内 API 错误由模块展示，不会让其他页面区域停止工作。
- 本版未增加自定义组合回测、上传数据、实时行情、交易、排名历史图或打印报告。

## 给客户的新增只读 API

基础路径：`/api/cs5_6_equity/v1/`。先 GET `runs`，从 `default_run_id` 读取有效运行；不要写死本机目录名。旧接口与兼容别名继续保留。

| 请求 | 用途 |
|---|---|
| `GET runs/{id}/stocks` | 可关注股票及公司名、回测日期、排名日期、默认日期 |
| `GET runs/{id}/watchlist?date=2026-08-28&tickers=SCL,TJX,CMG` | 一次取得当前选择的输入、排名、策略配置及来源 |
| `GET runs/{id}/watchlist/download?date=2026-08-28&tickers=SCL,TJX,CMG&format=csv` | 当前选择 CSV；`format=json` 为完整 JSON 合同 |

`date` 和 `tickers` 必填。tickers 逗号分隔，去除空白、转大写、去重并保留选择顺序。最多为本运行股票池数量（现有 40）。混入一个不支持的股票就返回 HTTP 422 `unsupported_stocks`，不会悄悄丢弃。无效日期格式或 format 返回 422，未知运行返回 404；POST 不受支持。

股票目录 `stocks` 是整个运行出现过的股票，不保证每个历史日期都有全部股票。公司名优先取选定日期的输入；无对应记录时用源文件中最新的公司名作为目录标签。

关注响应：

- `module_id/module_version/run_id/signal_date/requested_tickers`：明确模块、版本、运行、日期、选择顺序。
- `status`：`success` 表示所有请求股票的排名、因子、回测价格和配置判断可用；`partial` 表示部分信息缺失；`no_data` 表示所选股票在该日期没有排名。仍应逐字段检查状态和 null。
- `watchlist_changes_strategy=false`：查询没有改变原研究股票池或策略。
- `rows[]`：`ticker/stock_name`、`factors_status/factors`、`prices_status/prices`、`ranking`、`selection_status`、`allocation`、`exclusion_reason`。
- `factors_status/prices_status`：`available`、`no_data`（无该日期的对齐记录）、`unavailable`（输入文件缺失或不匹配）。缺失数值为 null，不能转换为 0。
- `selection_status`：`selected` 已入选；`not_selected` 有已验证配置且有该股票排名，但不在实际配置中；`no_data` 无该日期回测/股票排名；`unavailable` 配置快照或输入身份无法验证。
- `allocation` 仅已入选时返回原真实目标/实际权重及股数等字段；其他情况为 null。`exclusion_reason` 固定 null：原文件未保存逐股原因。
- `strategy_context.metrics_scope=original_strategy_full_backtest`：随附指标为原完整策略；`metrics/backtest/units/assumptions` 不随关注列表改变。完整模型与股票池合同仍见 `portfolio` 接口。
- `provenance`：原输出、匹配输入和分配快照的哈希；缺失的来源项为 null。

CSV 使用 UTF-8 BOM，方便表格软件打开。百分位、权重为小数比例，`0.2` 表示 20%；空值为空单元格。CSV 包含日期、run、选中股票、五因子、价格、模型输出、状态、权重/股数、来源哈希，不创建关注组合收益。JSON 中 `strategy_context` 保留原完整组合指标。

运行可复现的接口验收：

```bash
node dashboard/examples/verify-watchlist.mjs http://127.0.0.1:8000/
```

真实示例文件：`dashboard/examples/cs5_6_equity/watchlist-success.json`、`watchlist-no-data.json`、`watchlist-invalid.json`。完整机器可读合同见 [openapi.json](openapi.json)。

## 客户接入

1. **iframe 方式**：在 Strategy Lab 入口打开 `https://研究域名/?embed=1&lang=en#watchlist`。部署方配置 `embed_origins`，客户配置 `frame-src`。示例位于 `dashboard/frontend/public/embed-example.html` 和 `.mjs`。
2. **原生界面方式**：客户先读 stocks 填充股票选择器，再按选定 date/tickers 请求 watchlist。直接跨域请求时配置 `api_origins`；客户后端代理可保持浏览器同源。
3. **失败隔离**：就绪消息 `{type:"cs5_6_equity:ready",version:"1.4.0"}` 仅表示前端已挂载，不能当作数据健康状态。客户父页须同时校验 `event.origin` 为研究域名且 `event.source` 为对应 iframe。当前示例按同源校验；跨域接入需替换为实际允许的精确 origin。
4. **正式上线**：客户仍需提供部署地址、认证/SSO 要求、测试环境，在独立分支审查入口改动并回归其他 Portfolio 功能。此版不表示已经接入客户生产网站。

实现与验收见 [PRESENTATION_VALIDATION.md](PRESENTATION_VALIDATION.md)。
