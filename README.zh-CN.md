# SafeCapital

[English](README.md) | **中文**

<a id="readme-index"></a>

## README 总目录

所有 22 组说明均有独立英文页和中文页，共 44 个文件。点击页面顶部的语言链接即可切换，当前页只显示一种语言。

| 类别 | 文档 | English | 中文 |
|---|---|---|---|
| 总览 | [项目总览](README.zh-CN.md) | [English](README.md) | [中文](README.zh-CN.md) |
| Dashboard | [安装与接入](dashboard/README.zh-CN.md) | [English](dashboard/README.md) | [中文](dashboard/README.zh-CN.md) |
| 数据 | [数据版本与复现边界](data/README.zh-CN.md) | [English](data/README.md) | [中文](data/README.zh-CN.md) |
| 数据 | [原始数据范围](data/raw_inputs/README.zh-CN.md) | [English](data/raw_inputs/README.md) | [中文](data/raw_inputs/README.zh-CN.md) |
| 数据 | [采集与清洗参考](data_processing/README.zh-CN.md) | [English](data_processing/README.md) | [中文](data_processing/README.zh-CN.md) |
| 研究 | [因子筛选](research/01_factor_analysis/README.zh-CN.md) | [English](research/01_factor_analysis/README.md) | [中文](research/01_factor_analysis/README.zh-CN.md) |
| 研究 | [02 · Ridge](research/02_ridge/README.zh-CN.md) | [English](research/02_ridge/README.md) | [中文](research/02_ridge/README.zh-CN.md) |
| 研究 | [随机森林](research/03_random_forest/README.zh-CN.md) | [English](research/03_random_forest/README.md) | [中文](research/03_random_forest/README.zh-CN.md) |
| 研究 | [回归](research/04_xgboost/README.zh-CN.md) | [English](research/04_xgboost/README.md) | [中文](research/04_xgboost/README.zh-CN.md) |
| 研究 | [05 · XGBoostRanker](research/05_xgboost_ranker/README.zh-CN.md) | [English](research/05_xgboost_ranker/README.md) | [中文](research/05_xgboost_ranker/README.zh-CN.md) |
| 研究 | [评估与回测](research/06_evaluation_backtest/README.zh-CN.md) | [English](research/06_evaluation_backtest/README.md) | [中文](research/06_evaluation_backtest/README.zh-CN.md) |
| 外部评估 | [冻结模型](external_validation/ensemble_ranker/README.zh-CN.md) | [English](external_validation/ensemble_ranker/README.md) | [中文](external_validation/ensemble_ranker/README.zh-CN.md) |
| 外部评估 | [历史预测参考](external_validation/ensemble_ranker/predictions/README.zh-CN.md) | [English](external_validation/ensemble_ranker/predictions/README.md) | [中文](external_validation/ensemble_ranker/predictions/README.zh-CN.md) |
| 外部评估 | [原始训练参考](external_validation/ensemble_ranker/training_reference/README.zh-CN.md) | [English](external_validation/ensemble_ranker/training_reference/README.md) | [中文](external_validation/ensemble_ranker/training_reference/README.zh-CN.md) |
| 外部评估 | [共用价格输入](external_validation/shared_inputs/README.zh-CN.md) | [English](external_validation/shared_inputs/README.md) | [中文](external_validation/shared_inputs/README.zh-CN.md) |
| 回测 | [所选外部策略账户引擎](backtesting/README.zh-CN.md) | [English](backtesting/README.md) | [中文](backtesting/README.zh-CN.md) |
| 报告 | [报告总览](reports/README.zh-CN.md) | [English](reports/README.md) | [中文](reports/README.zh-CN.md) |
| 报告 | [模型、因子与证据](reports/ensemble/00_README_models_factors_files.zh-CN.md) | [English](reports/ensemble/00_README_models_factors_files.md) | [中文](reports/ensemble/00_README_models_factors_files.zh-CN.md) |
| 最终输出 | [最终输出目录](FINAL_OUTPUTS/README.zh-CN.md) | [English](FINAL_OUTPUTS/README.md) | [中文](FINAL_OUTPUTS/README.zh-CN.md) |
| 最终输出 | [保存模型回放](FINAL_OUTPUTS/01_saved_model_replay/README.zh-CN.md) | [English](FINAL_OUTPUTS/01_saved_model_replay/README.md) | [中文](FINAL_OUTPUTS/01_saved_model_replay/README.zh-CN.md) |
| 最终输出 | [已验证回测结果](FINAL_OUTPUTS/01_saved_model_replay/verified_replay/backtest/README.zh-CN.md) | [English](FINAL_OUTPUTS/01_saved_model_replay/verified_replay/backtest/README.md) | [中文](FINAL_OUTPUTS/01_saved_model_replay/verified_replay/backtest/README.zh-CN.md) |
| 验证 | [验证证据](docs/validation_runs/2026-11-01/README.zh-CN.md) | [English](docs/validation_runs/2026-11-01/README.md) | [中文](docs/validation_runs/2026-11-01/README.zh-CN.md) |

其他指南：[安装与交付](START_HERE.zh-CN.md) · [安装速查](dashboard/docs/CUSTOMER_HANDOFF.zh-CN.md) · [API 约定（英文）](dashboard/docs/API_V1.md) · [英文演示讲稿](dashboard/docs/PRESENTATION_SCRIPT_EN.md)。

<a id="readme-zh"></a>

SafeCapital 展示周度股票排名研究方法，以及一个选定的外部投资组合策略：冻结的三组件 Ensemble 在 Common210 FullHistory 区间上的 `Top5_NoLoss13w`。

**本项目的复现从提供的已处理周度数据开始。原始数据采集和重建不属于本次交付范围。** 这些数据是研究、模型训练演示和策略回放的明确起点，运行这些流程不需要额外采集原始数据。

### Web Dashboard

**客户交付入口：**[安装与交付指南](START_HERE.zh-CN.md) · [安装速查](dashboard/docs/CUSTOMER_HANDOFF.zh-CN.md) · [英文提交消息模板](dashboard/docs/CLIENT_SUBMISSION_EN.md)。执行安装命令前，先区分完整 Source 源码 ZIP 与预构建 Web 运行包。所交付 Dashboard 和随附数据回放均不需要 API Key。

1.4 版本提供默认英文、支持中文切换的 Dashboard，包含关注股票、共享历史日期、因子与排名详情、实际策略入选状态及权重、图表、CSV/JSON 导出和只读 API。关注列表不会改变原始策略或其收益。详见[本地输入输出指南](dashboard/docs/LOCAL_IO.md)。Docker 和公网部署暂缓。

交付资料还包含[完整实施计划](dashboard/docs/DEVELOPMENT_PLAN.md)、[安装与接入指南](dashboard/docs/CUSTOMER_HANDOFF.zh-CN.md)、[API v1 约定](dashboard/docs/API_V1.md)，以及包含预构建前端和真实已验证结果快照的可移植 ZIP 打包方式。已完成的检查与目标环境限制见[交付验收记录](dashboard/docs/DELIVERY_VALIDATION.md)。

只读中英文 Dashboard 以图表、按日期筛选的排名和下载功能展示已核验历史结果，支持独立访问和客户网站 iframe 嵌入。已有本地安装可用 `.venv-dashboard/bin/python dashboard/start.py` 启动；首次安装、部署和 API 文档见 [Dashboard 设置与接入](dashboard/README.zh-CN.md#readme-zh)。它使用独立依赖，不运行或替代以下模型流程。

### 两条独立流程

| 流程 | 用途 | 命令 |
|---|---|---|
| 冻结 Ensemble 回放 | 加载 45 个已训练快照，复现预测并核验所选外部策略结果 | `python safecapital.py` |
| Ensemble 训练演示（V1） | 准备随附周度训练数据，仅拟合 3 个 Ensemble 组件，保存模型并核验保存/加载一致性 | `python safecapital.py --retrain-v1 --profile full` |

V1 是训练演示的旧标识，不是整个 SafeCapital 项目的版本号，也不是第二个经过外部评估的 Ensemble。训练演示不生成外部预测、不执行外部回测，也不比较两个 Ensemble。新模型保存在独立运行目录，绝不替换默认冻结模型。独立外部 Ranker 分支及其模型、预测、回测产物已删除。

原始四类研究模型（Ridge、Random Forest、XGBoost 和 XGBRanker）作为方法资料保留。研究用 XGBRanker 和 Ensemble 组件，与已删除的独立外部 Ranker 对比分支是不同概念。

<a id="why-the-trained-models-are-frozen"></a>

### 为什么冻结已训练模型

策略结果属于某一组具体训练完成的 Ensemble。固定超参数本身不能保证拟合出完全相同的树。模型使用随机子采样；即使随机种子固定，平台、库版本、线程与浮点计算仍可能影响树的拟合。项目历史比较观察到了跨环境树结构与预测差异，但这不意味着每次重新拟合必然不同。

学习到的树不同，可能改变分数、股票排名、入选组合和策略结果。仅文件哈希改变并不能证明预测不同，因为序列化或元数据也可能改变。因此交付包同时核验产物身份与数值输出。

项目冻结原始 45 个训练快照，记录 SHA-256，并为每个历史信号加载当时生效的快照。回放根据随附因子重新生成全部组件与 Ensemble 预测，与参考精确比较，再计算组合模拟，并独立核验选股及账户。冻结消除了重新训练带来的差异，但仍需匹配数据、预处理和交易规则，且执行环境中的检查必须通过。

重新训练用于展示组件的拟合方法。新拟合文件是独立实验产物，不用于证明所交付策略结果。

### 安装研究环境

使用 64 位 Python 3.12 和独立环境，在解压后的项目根目录执行。

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate
```

若无法激活环境，可直接调用环境内 Python 可执行文件。安装需要网络，使用随附数据的流程可离线执行。`tools/check_environment.py` 检查固定依赖。macOS 上 XGBoost 可能额外需要 OpenMP 运行库。数值验收以该次运行的预测与账户检查为准。

### 运行所选策略

```bash
python safecapital.py
```

`python run.py` 和 `python safecapital.py --saved-ensemble` 等价，`--legacy-ensemble` 保留为兼容别名。一次回放只需运行一个入口。使用 `--run-id NAME` 指定新输出目录，已有运行目录不会被覆盖。

回放加载 45 个原始 XGBRanker 快照（3 个组件，每个 15 次拟合），在外部股票池内将因子转为排名，计算组件分数和周内百分位，再按各三分之一权重取三个百分位的平均值。Ensemble 同分时按股票代码顺序确定排名。每个历史日期使用当时有效的快照，而不是更晚的拟合版本。未来收益标签不进入预测或选股。

预测核验覆盖 366 个信号周、13,517 条股票—周记录。所选组合使用 Common210 区间：2022-08-26 至 2026-08-28，共 210 个信号周、8,354 条股票—周记录。

#### 策略规则

1. 在信号日计算每只股票可观测的过去 13 周价格收益。执行价格面板存储的是下一周收盘价，引擎先将该序列移回一行，再构造历史过滤条件。
2. 排除过去收益为负，或缺乏足够有效 13 周历史的股票；零收益仍合格。
3. 从合格股票中选择 Ensemble 分数最高的最多五只。
4. 每只股票目标配置为开盘账户权益的 20%。不足五只时，未用配置保留为现金；整数股取整和交易费也会产生剩余现金。
5. 每周以次期开盘代理价再平衡，保留现金，并按次期收盘代理价估值。初始资金 100,000，每次买入或卖出收取 10 个基点费用；股数计算包含费用并避免现金为负。模拟结束时清算剩余持仓。

外部结果仅有一个 FullHistory 策略案例，不单独展示最后一年年化收益表或图；训练演示也没有外部绩效对比。

| 模型 | 策略 | 周数 | 年化收益 | 夏普比率 | 最大回撤 | 最终资金 |
|---|---|---:|---:|---:|---:|---:|
| Frozen Ensemble | Top5_NoLoss13w | 210 | 10.4390% | 0.5434211 | -24.8781% | 149330.61 |

### 输出与验证

本交付用于展示研究方法与策略结果，保留预测、每周资金和验证记录。不要求单独交付每周入选股票清单、逐股过滤决策表、订单台账或逐股持仓台账。订单和持仓在内存中计算，独立验证器据此检查选股、整数股数量、费用、现金、持仓和汇总指标。

| 每次回放目录中的输出 | 内容 |
|---|---|
| `saved_model_predictions.csv` | 每周逐股组件模型 ID、原始分数、百分位和排名，以及 Ensemble 分数/排名；均在策略过滤之前 |
| `prediction_verification.json` | 快照身份、预测覆盖范围及与历史参考精确一致的核验 |
| `backtest/weekly_capital.csv` | 每周资金、净收益、现金、费用、持仓数量和股数 |
| `backtest/summary.csv` | 单个所选策略的汇总指标 |
| `backtest/verification.json` | 指标一致性与独立选股/账户核验 |
| `backtest/README.md` | 策略和结果摘要 |
| `manifest.json` | 完整运行状态与输出哈希 |

预测排名不是实际执行持仓清单。完整回放的 `manifest.json` 应在预测和组合验证均通过后显示 `status: passed`。失败或中断会记录为失败。运行是短时、独立执行，没有检查点恢复或续跑功能；中断后应创建新运行。

`FINAL_OUTPUTS/01_saved_model_replay/verified_replay/` 保留已验证的完整回放，包含预测、每周资金和验证记录。辅助配置、因子定义及快照/排名审计位于 `reports/ensemble/`。[验证结果](docs/VALIDATION.md)列明检查内容与结果。

### Ensemble 训练演示

```bash
# 每个组件只拟合最近一次：共 3 个模型文件
python safecapital.py --retrain-v1 --profile smoke

# 每个组件完成全部 15 次拟合：共 45 个模型文件
python safecapital.py --retrain-v1 --profile full
```

选择其中一个配置运行。V1 使用 `data/reproducible/train66_corrected_complete.csv`（66 股、521 个完整信号周）、`data/reproducible/train_universe.csv`（股票代码校验），以及 `data/clean_basic_data.csv`（对所有标签执行日度复权收盘价检查，包括最后一周和缺口相邻行）。三个文件都必需，并在运行清单中记录哈希。流程验证周度键、因子和标签，构造 156 / 52 / 52 周的时间顺序窗口，每 26 周拟合三个组件并保存 JSON 模型。每个模型会重新加载，其在训练矩阵上的预测必须精确一致。这是序列化检查，不是外部绩效评估。

输出包括 `prepare/train.csv`、`prepare/calendar.csv`、`prepare/data_audit.json`、`train/models/`、`train/model_manifest.json`、`manifest.json` 与 `run.log`，没有外部预测、回测或比较阶段。详见[训练指南](docs/V1_RETRAINING.md)。

未修改的原始训练实现及其历史 66 股输入，也保存在 `external_validation/ensemble_ranker/training_reference/` 与该 Ensemble 目录下的 `inputs/train66.csv`，用于保留方法来源。V1 修正后的 521 周训练输入与原始冻结模型的训练输入是明确区分的数据版本。

### 研究方法与项目结构

| 位置 | 作用 |
|---|---|
| [data/](data/README.zh-CN.md#readme-zh) | 随附已处理数据及版本定义 |
| [research/01_factor_analysis/](research/01_factor_analysis/README.zh-CN.md#readme-zh) | 45 个因子的构造定义和筛选 |
| [research/02_ridge/](research/02_ridge/README.zh-CN.md#readme-zh) | Ridge 研究 |
| [research/03_random_forest/](research/03_random_forest/README.zh-CN.md#readme-zh) | Random Forest 研究 |
| [research/04_xgboost/](research/04_xgboost/README.zh-CN.md#readme-zh) | XGBoost 回归研究 |
| [research/05_xgboost_ranker/](research/05_xgboost_ranker/README.zh-CN.md#readme-zh) | XGBRanker 研究 |
| [research/06_evaluation_backtest/](research/06_evaluation_backtest/README.zh-CN.md#readme-zh) | 原始研究评估方法及保留证据 |
| [external_validation/ensemble_ranker/](external_validation/ensemble_ranker/README.zh-CN.md#readme-zh) | 原始冻结 Ensemble、因子、参考预测和训练源码 |
| [external_validation/shared_inputs/](external_validation/shared_inputs/README.zh-CN.md#readme-zh) | 所选回放使用的已处理外部价格面板 |
| `pipeline/` | 训练演示和独立回放验证辅助模块 |
| [FINAL_OUTPUTS/](FINAL_OUTPUTS/README.zh-CN.md#readme-zh) | 所选策略证据和原始研究章节 |
| [data_processing/](data_processing/README.zh-CN.md#readme-zh) | 历史采集/准备源码，仅作为复现边界之外的方法参考 |
| `runs/` | 新的本地运行，不纳入交付压缩包 |

原始四模型研究使用其随附的 522 周数据。历史结果属于各自记载的研究协议，不是额外的外部 Ensemble 对比。只有计划开展新研究实验时才运行研究脚本；各指南明确输入和输出位置。

### 检查

```bash
# 仅核验文件清单和哈希
python -B tools/check_release.py

# 检查依赖及已处理输入是否就绪
python -B tools/check_environment.py

# 回归检查，包括冻结推断及合成账户案例
python -B -m unittest discover -s pipeline_tests -v
```

默认回放本身会执行完整的所选策略验证。文件完整性、依赖检查和数值核验各有用途，不能互相替代。不要使用 `python -O`，因为历史执行引擎依赖断言。

### 解释与来源

冻结产物建立可复现模型版本，不证明未来盈利。全样本因子筛选和曾被查看的研究区间限制了独立泛化结论。报价代理值不能证明真实成交、滑点、市场冲击、容量或全部公司行动。已处理输入的检查也不独立证明每项财务数据的发布时间或历史修订。

来源说明见 [NOTICE.md](NOTICE.md)，交付变化见 [CHANGELOG.md](CHANGELOG.md)。

### 原始研究结果的报告引用口径

项目报告引用模型指标时，以各模型 `research/02_ridge/results/`、`research/03_random_forest/results/`、`research/04_xgboost/results/` 和 `research/05_xgboost_ranker/results/` 中原始交付结果表为准。`research/06_evaluation_backtest/results/` 内的统一评估单独保存，代表对归档重跑预测的评估；它不替代原始交付表，也不证明复现了其中不同的指标。这一引用口径不改变独立的冻结外部 Ensemble 回放。
