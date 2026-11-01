# CS5-6 / Portfolio Neo 接入交接（1.3.0）

本模块名称为 **Model-Based Stock Strategies**，命名空间为 `cs5_6_equity`。它读取既有研究结果，展示真实输入、模型排名、策略持仓和历史表现。此版本参考 [客户 Portfolio Neo 页面](https://www.safecapitai.com/portfolio-neo) 的深色绿色视觉风格，实现独立页面、iframe 和只读 API。

**当前交付是本地可演示模块，不是客户线上网站的已完成集成。** 客户站点源码、认证方式和测试环境尚未提供；实际入口、登录/权限和其他模块回归需由客户核心团队在 staging 中审核。Docker 和公网部署继续暂缓。

## 1. 本地演示（无需 Docker）

在工程根目录启动：

```sh
.venv-dashboard/bin/python dashboard/start.py
```

- 英文页面：`http://127.0.0.1:8000/?lang=en`；中文：`?lang=zh`，顶部也可切换。
- 嵌入入口预览：`http://127.0.0.1:8000/embed-example.html?lang=en`，点击 **Explore strategies** 展开独立 iframe；收起时宿主外壳仍在。
- 嵌入页面：`http://127.0.0.1:8000/?embed=1&lang=en`。
- 接口文档：`http://127.0.0.1:8000/api/docs`；离线合同：`openapi.json`。

演示顺序：

1. 展示入口卡片，说明建议放在客户 Strategy Lab 介绍下方、现有策略选项旁。
2. 打开模块，介绍 **Model-Based Stock Strategies**：查看模型选出的股票组合及其历史表现和风险。
3. 说明本次 FullHistory 回测为 **2022-08-26 至 2026-08-28，210 个信号周**。年化 **10.44%**、累计 **49.33%**、最大回撤 **−24.88%**，初始研究资金 100000，期末 149330.61。
4. 切换资金、每周收益、回撤与图表区间。顶部指标始终是完整区间，不因缩短图表而改变。
5. 点击 **Stocks & weights**，切换历史日期。目标权重与整数股模拟成交后的实际权重不同；现金单独列出。最新日期的股票为 SCL、CMG、UTZ、RH、URBN，不能把原始排名前五名当作持仓。
6. 展开 **Methodology & ontology**。介绍周度频率、13 周过滤、模型、费用、执行代理价、来源和限制。最后一个持有期结束时已经清仓，展示不代表当前持仓。
7. 点击 **Input data**，展示因子和回测价格，按日期/股票筛选、查看输出排名、下载原始文件。原始源数据范围与本次回测范围不同。
8. 点击 **Input & output APIs**，打开输入 JSON、输出汇总和持仓合同。使用下方脚本现场展示成功、无数据和无效输入三个响应。

中文/英文切换保留筛选；语言设置只写入 `cs5_6_equity.language`。股票组合不读取宿主页的单资产选择器。

## 2. 客户两页要求对应表

| 要求 | 此版本实现与证据 | 验收边界 |
|---|---|---|
| Portfolio Neo 内单独入口 | 本地入口卡片 + 独立 iframe；建议名称 Model-Based Stock Strategies | 客户真实页面入口待核心团队接入 |
| 模型、策略、持仓及权重 | 模型概览、周度选股表、目标/实际权重与现金 | 无实时选股或交易 |
| 图表、年化/总收益、回撤、基准 | 真实 210 周曲线及指标；基准明确显示不可用 | 未提供同范围、同口径的已验证基准序列 |
| 66 训练 + 独立 40 外部股票，不含 ETF | 离线读取实际股票集合并验证不相交；接口返回名单、计数、信号当周数量 | 66 是完整训练池，早期训练快照实际可用股票数随覆盖变化 |
| FullHistory 与较短 final-test 区分 | 界面/合同明确 Common210 / FullHistory 日期和周数 | 不移用报告较短区间的数字 |
| 年化、币种、成本、执行透明 | 每年 52 周复合年化，单边 10 bps，整数股，下一周开/收盘代理价，期末清仓 | 源文件未声明币种，currency=null；不声称真实 next-open 成交或 S&P 500 历史成员覆盖 |
| 独立模块与本体 | `/api/cs5_6_equity/v1`、独立数据目录和实体关系 | 不修改/合并其他团队本体、全局资产、登录、路由 |
| 故障不影响其他功能 | 组合快照缺失/损坏只禁用该表，既有输入输出继续服务；iframe 隔离宿主 | 客户整站故障隔离和已有模块回归仍需 staging 实测 |
| 可追溯、缺失值不归零 | 原文件哈希、引擎哈希、分配快照哈希、离线核验记录；缺失为 null + reason | 信号日期不等于财务数据发布时间，独立发布时间戳不可用 |
| 成功 + 无数据/错误示例 | `../examples/verify-module.mjs`、`../examples/cs5_6_equity/` JSON | 可对本地服务复现 |
| 手机、双语、交接 | 响应式布局；截图与验收见 `PORTFOLIO_NEO_VALIDATION.md` | 客户真实设备/宿主容器由客户再验收 |
| 分支与 PR | 分支 `feature/cs5-6-portfolio-neo-integration` | 不直接合并 main，不发布客户生产站 |

## 3. 模块接口

新集成前缀为 **`/api/cs5_6_equity/v1`**。已有 `/api/v1` 和 `/api` 为兼容别名，客户应使用命名空间前缀，避免其他团队路由碰撞。所有业务接口只读 GET；Web 服务不训练模型、不上传任意数据、不启动预测。

| 相对路径 | 内容 |
|---|---|
| `/runs` | 先获取可用 run_id 与 default_run_id |
| `/runs/{run_id}/portfolio?date=2026-08-28` | 本模块完整合同；不指定日期取最新回测信号日期 |
| `/runs/{run_id}/overview` | 原始回测汇总、运行来源、排名日期 |
| `/runs/{run_id}/equity` | 210 周资金、净收益和回撤，用于绘图 |
| `/runs/{run_id}/rankings?date=2026-08-28` | 策略过滤前的模型排序，非持仓 |
| `/runs/{run_id}/inputs` | 与运行哈希绑定的输入目录和字段 |
| `/runs/{run_id}/inputs/{factors或prices}/rows?date=2026-08-28&scope=output&q=SCL` | 输入查询；按 date + 精确 ticker 关联，不按行号 |
| `/runs/{run_id}/inputs/{factors或prices}/download` | 完整原始输入 CSV |
| `/runs/{run_id}/downloads/{predictions或equity或summary或manifest}` | 已验证原结果下载 |

`portfolio` 的字段：

| 字段 | 解释 |
|---|---|
| `module_id`, `module_version`, `run_id`, `data_mode` | 模块身份、版本、运行标识、historical_simulation |
| `status` | success：选定日期持仓可用；partial：输出可用但分配不可用；no_data：该日期无组合回测 |
| `model`, `strategy` | 冻结三组件模型、快照数、Top5_NoLoss13w、weekly、最多 5 只、单只目标 0.2 |
| `universe` | 完整训练池、独立外部股票池、所选日期实际有排名的股票；禁止把客户全局资产选择器当作组合池 |
| `signal_date`, `data_cutoff` | 数据集信号日期与最新源数据日期；financial_publication_timestamp=null，不夸大 point-in-time 保证 |
| `backtest` | start/end/weeks/dates/scope/window；完整区间指标与所选配置日期分开 |
| `metrics`, `units` | 收益、回撤和权重为小数，例如 .10439≈10.44%；账户金额沿用原研究单位，currency=null |
| `benchmark` | unavailable；name/收益/series=null，并给出 reason；不是 0 收益 |
| `assumptions` | 年化公式、52 周、费用 bps、执行代理价、整数股、13 周过滤、期末清仓 |
| `allocation` | status/reason、phase、股票 rows、现金、现金权重、配置总价值、期末清仓标志 |
| `allocation.rows[]` | ticker/company、model_rank、target_weight、actual_weight、shares、execution_price_proxy、market_value_at_open |
| `provenance` | 源结果/运行清单/引擎/分配快照哈希与独立核验结果 |

**权重口径：** `actual_weight = shares × next_week_open_proxy / post_trade_open_value`；`post_trade_open_value = 股票开盘代理价值之和 + 调仓后现金`。现金权重 + 股票实际权重之和为 1。它是调仓后配置，不是持有期末估值权重；最终一周仍展示持有期内股票，并明确 `liquidated_at_period_end=true`。

**状态口径：** `success` 仅表示主要持仓结果可用，不能据此认为 benchmark/currency 等可选字段齐备；逐个检查其状态和 null。合法但没有回测的日期返回 HTTP 200/no_data，`rows=[]`、`cash_weight=null`；不表示全现金。已验证的全现金周才可返回 available、空 rows、cash_weight=1。日期格式错误返回 HTTP 422，未知运行返回 404；`status=error`、`module_id` 和 `error.code/message/request_id/fields` 用于诊断。

重现例子（Node.js 22+）：

```sh
node dashboard/examples/verify-module.mjs http://127.0.0.1:8000/
node dashboard/examples/client.mjs http://127.0.0.1:8000/
```

`verify-module.mjs` 检查真实成功结果、2019-08-30 无回测记录、无效日期、缺失 run。固定 JSON 样例在 `dashboard/examples/cs5_6_equity/`，是从实际适配器导出的响应，不是模拟收益。示例 run_id 使用随包 `delivered`；调用时请始终先查 `/runs`。

## 4. 数据、本体及引擎边界

本模块的实体关系为 **Module → Model → Run → WeeklySignal → EquityAllocation → BacktestMetrics**。实体标识使用 `(module_id, run_id, signal_date, ticker)` 组合，日期与 ticker 为跨文件连接键。这里是本模块 JSON 数据关系，不是客户共享 RDF/ontology 的替代物；现有研究引擎、原文件名和运行 ID 保留，避免破坏证据链。

新增导出物只写入 `dashboard/data/cs5_6_equity/`。原模型、数据集、原始报告和回测文件不修改。离线导出程序使用原 `backtesting/external40/integer_backtest.py` 和独立账户核验器复算既有保存预测的执行过程，不重新训练或产生新预测。两种已保存 CSV 字节格式对应两份快照，每份 210 周；资金序列与原结果最大误差 0，独立账户核验每份 9586 项，最大数值误差约 2.84e-14。

在完整研究工程中重新导出（仅维护人员；不是 Dashboard 启动步骤）：

```sh
.venv/bin/python dashboard/tools/export_portfolio_snapshot.py
```

运行时服务只读 JSON 快照；先校验快照 SHA-256/大小/范围和权重，再用三份结果文件哈希、四份输入/配置哈希绑定当前运行。新增运行若无法匹配已有快照，组合表显示 unavailable，原始有效输出仍能查询。更换数据需离线重新导出和验收后重启服务；不要手工编辑收益、持仓或校验清单来绕过验证。

## 5. 客户正式接入步骤

推荐第一版采用独立 HTTPS 根域名托管模块 + iframe；客户不必复用 React，也不需要接管训练环境。本地 127.0.0.1 不能供客户公网访问。

1. 客户确认实际仓库、staging URL、认证/权限、模块服务域名及负责人。
2. 模块服务使用原生 Python 环境运行；配置 `public_url` 和精确 `embed_origins`。浏览器跨域直接取 JSON 才需要 `api_origins`，二者不是同一项。
3. 客户在自己的功能分支内新增入口，不改现有单资产选择器、登录、其他团队模块；由核心团队决定该卡片在 Strategy Lab 的准确位置。
4. iframe 示例（替换为实际模块域名，不是客户根域名）：

```html
<iframe
  src="https://research.example.com/?embed=1&lang=en"
  title="Model-Based Stock Strategies — CS5-6"
  width="100%" height="1450"
  style="border:1px solid #263c31;border-radius:14px"
  loading="lazy">
</iframe>
```

5. 客户使用自己的布局承载入口。若改为原生 UI，消费上述 JSON，不将本模块 CSS 全局导入客户站点、不合并本体。保留缺失值和证据说明。
6. 登录权限由客户网关/宿主策略实现。本版只读本地服务没有独立用户认证；CORS/iframe 白名单不等于访问控制。
7. 在 staging 实测手机、语言、加载/无数据/失败，以及模块服务断开后宿主导航、登录和其他策略仍正常。核对全局选择器不会改变本模块的 40 股组合池。
8. 核心团队审核聚焦 PR、控制合并和生产发布。此交接不自动修改客户网站。

## 6. 文件与依赖

- 前端：React 19、TypeScript、Vite、Recharts；锁定于 `dashboard/frontend/package-lock.json`。
- 运行时：Python 3.12 + `dashboard/requirements.txt`，无需模型训练依赖或 Node.js（使用交付包预构建页面）。
- API：`dashboard/server/portfolio.py`、`schemas.py`；UI：`PortfolioPanel.tsx`、`client-theme.css`。
- 样例：`dashboard/examples/`；测试：`dashboard/tests/test_portfolio.py`；截图/验证：`PORTFOLIO_NEO_VALIDATION.md`。
- 客户包可用 `dashboard/tools/build_delivery.py` 生成，包含模块快照、匹配输入、原结果、离线 API 合同与文档；不包含完整训练工程。旧 Docker 配方尚未纳入本次新数据验收，不作为当前启动路径。
