# 本地 Dashboard：输入、输出与接口

当前版本读取项目现有文件，展示已验证的真实历史结果。所有接口只读，不接收上传或触发重新计算。使用 Python 原生服务即可，不需要 Docker。

## 启动与查看

在项目根目录运行：

```bash
.venv-dashboard/bin/python dashboard/start.py
```

保持终端运行，打开 <http://127.0.0.1:8000/>。首次安装见 [Dashboard README](../README.md)。

1. 点击“输入数据”：切换“模型因子输入”和“回测价格输入”，选择日期或搜索股票代码。
2. 默认查看“与本次输出对齐”的记录；改为“完整源文件”可查看更早历史。表格可横向滚动。
3. 点击某条输入的“查看输出”，排名表自动切换到相同日期和股票。早于预测区间的输入明确标注“不在预测区间”。
4. “策略概览”显示完整回测指标和资金曲线；“股票排名”显示过滤前排名，不是实际持仓。
5. 在输入区复制当前查询地址或打开 JSON；下载按钮保存完整原始输入 CSV。“输入输出接口”区可打开接口文档及输入/输出 JSON。

数据更换后重启 Python 服务，再刷新网页。浏览器刷新本身不会重新加载磁盘文件。

## 中英文切换

点击页面顶部的“中文 / English”即可切换。当前结果版本、输入范围、日期、股票搜索和图表选择会保留；浏览器记住语言。直接访问 `/?lang=en` 打开英文，`/?lang=zh` 打开中文；嵌入使用 `/?embed=1&lang=en`。URL 中的语言优先于本机记忆，无设置时默认为中文。

界面会翻译字段说明，API 字段名、原始响应及 CSV 文件保持原始合同。完整 API 文档和下载的研究文件不做语言改写。

## 输入是什么

| 输入 | 项目内文件 | 用途 |
|---|---|---|
| 模型因子 | external_validation/ensemble_ranker/inputs/test40.csv | date、ticker、五个原始财务因子；模型内部做同周百分位转换 |
| 历史价格 | external_validation/shared_inputs/inputs/test40_with_prices.csv | buy_price / sell_price 为下一周开盘/收盘代理价，用于历史回测 |

五个因子：revenue_growth_yoy、operating_profitability、cashflow_to_assets、debt_to_assets、asset_growth_yoy。stock_name 仅用于展示。

两份文件各 17,353 行、574 个信号周，范围 2015-09-04 至 2026-08-28。当前预测对应 13,517 条因子记录、366 周；当前回测日期/股票键对应 8,354 条价格记录、210 周。更早价格仍可能用于 13 周过滤回看，所以“输出对齐”并不表示计算只使用这些行。

原始 CSV 还含 target1/target2 等研究字段，下载保留完整原文件；查询只返回所列输入字段。未来收益标签不参与预测或选股。

输入文件通过 `external_validation/ensemble_ranker/model_configuration.json`、`saved_models_manifest.json` 和本次预测/回测验证记录关联。缺失或身份不符时，输入区显示不可用，已验证的输出仍可查看。文件 SHA-256 是一致性校验，不是数字签名。

## 输出是什么

- 股票排名：13,517 条预测，按信号日期和 ticker 与因子输入关联；包含集成排名/得分及三组件百分位。
- 每周资金：210 周账户序列，含期末资金、净收益、现金、费用和回撤。
- 汇总指标：本次历史回测初始资金 100,000，期末资金约 149,330.61，累计收益约 49.33%；数值以当前回放 CSV 为准。
- 原始下载：预测、每周资金、汇总以及校验清单。

Dashboard 不会重新生成这些输出。本机默认选择最近一次验证通过的回放；新克隆仓库使用随仓库交付的 verified_replay。由 `/api/v1/runs` 返回实际运行 ID，客户不要写死本机 ID。

## 客户怎样拿到接口

本地文档：<http://127.0.0.1:8000/api/docs>；机器可读定义：<http://127.0.0.1:8000/api/openapi.json>。可直接把 [openapi.json](openapi.json)、[API_V1.md](API_V1.md) 和 [client.mjs](../examples/client.mjs) 交给客户开发者。

以下路径均以 `http://127.0.0.1:8000/api/v1/` 为基础地址：

| 步骤 | GET 路径 |
|---|---|
| 获取当前 ID | runs |
| 输入目录与字段 | runs/{id}/inputs |
| 因子查询 | runs/{id}/inputs/factors/rows?date=2026-08-28&q=ANF&scope=output |
| 价格查询 | runs/{id}/inputs/prices/rows?date=2026-08-28&q=ANF&scope=output |
| 完整输入下载 | runs/{id}/inputs/{factors或prices}/download |
| 对应排名 | runs/{id}/rankings?date=2026-08-28&q=ANF |
| 回测汇总 | runs/{id}/overview |
| 资金序列 | runs/{id}/equity |

输入 rows 支持 `scope=output` 或 `source`；省略 date 查询该范围的全部日期。`page` 从 1 开始，`page_size` 最大 100。`q` 是股票代码子串查询，关联时仍用准确的 date + ticker。

可运行示例（Node.js 22 或更高版本）：

```bash
node dashboard/examples/client.mjs http://127.0.0.1:8000/
```

该示例自动查找默认运行和最近日期，打印同一只股票的因子、价格、输出排名、汇总及下载地址。页面与接口由同一个本地服务提供。`127.0.0.1` 指调用者自己的电脑；交付接口定义后，客户可在自己的环境运行服务，再替换基础地址。若其网页跨域请求服务，按 API 文档配置精确的 api_origins。
