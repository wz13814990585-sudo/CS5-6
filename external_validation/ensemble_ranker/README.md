# XGBoost Ranker 模型、股票排名与机器学习评估交接

这是当前版本的独立交接包：原 66 只股票训练，新 40 只股票测试。保留三个子模型、等权集成、当前预测排名和全部机器学习评估。模型参数、因子、标签、滚动窗口、更新周期及排名算法均未修改。

本包不包含旧实验目录、交易回测结果、买卖策略、演示文件或本机 Python 虚拟环境。代码中只保留当前实验需要的训练、预测和评估逻辑，并整理了独立入口和相对路径；原项目文件未改动。

## 先看这些文件

| 路径 | 用途 |
|---|---|
| `outputs/current/predictions/stock_rankings.csv` | 13,517 个股票周，各子模型与集成的分数、排名和真实评价标签 |
| `outputs/current/predictions/model_rankings_long.csv` | 四个模型的 54,068 行长表，适合按模型分析 |
| `outputs/current/predictions/latest_historical_ranking.csv` | 2026-08-28 的历史排名，不是实时预测 |
| `outputs/current/metrics/overall_metrics.csv` | 全时期机器学习指标 |
| `outputs/current/metrics/stage_metrics.csv` | 全时期及 Development / Validation / Final Test 分段指标 |
| `outputs/current/metrics/` | 周度、年度、时间分段、重训区间和逐股评估 |
| `outputs/current/audit/` | 训练窗口、数据检查、模型复现与因子质量检查 |
| `models/` | 当前一次滚动实验的 45 个模型：3 个子模型 × 15 个更新时点 |
| `model_configuration.json` | 完整超参数、特征顺序、标签与集成配置 |
| `inputs/` | 66 股训练数据、40 股测试数据、五因子定义 |
| `docs/指标说明.md` | 全部指标口径、时间范围和数据解释 |
| `docs/source_provenance.json` | 原始来源哈希与交接整理说明 |
| `package_manifest.json` | 包内文件清单、SHA-256 与交接验证记录 |

45 个模型属于同一当前配置在不同时间的滚动训练实例，并非旧版本。历史排名必须使用该行 `model_1_id` / `model_2_id` / `model_3_id` 对应的模型，不能用最后一期模型重算所有历史日期。最后一次更新为 `refit_0520`，对应三个最新模型；集成是三个模型输出百分位的等权平均，因此没有第四个独立训练模型文件。

## 环境安装

建议 Python 3.12；交接核验使用 Python 3.12.14。依赖版本固定在 `requirements.txt`，不要将原机器 `.venv` 复制到同事机器。

在解压目录运行：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows 可用 `py -3.12 -m venv .venv`，再运行 `.venv\Scripts\activate`。如果 macOS 在导入 XGBoost 时提示缺少 `libomp`，需先安装 OpenMP 运行库，例如 `brew install libomp`。包内不包含操作系统运行库或依赖安装包。

## 三种运行方式

所有新输出目录必须尚不存在；重复运行时换一个目录名。

1. **读取保存模型，复现历史预测并重算全部评估**，不重新训练：

```bash
python -B code/run_pipeline.py --mode replay --output outputs/replay_new
```

结果位于 `outputs/replay_new/evaluation/`，中间预测和本次核对记录位于 `prediction_source/`。入口核对保存模型的原始分数和完整排名是否与当前交付结果一致。

2. **使用冻结参数从 66 股原数据重新训练，再预测 40 股并评估**：

```bash
python -B code/run_pipeline.py --mode train --output outputs/train_new --n-jobs 4
```

新模型位于 `outputs/train_new/models/`，结果位于 `outputs/train_new/evaluation/`。不搜索超参数，不使用新 40 股标签训练，不自动选取“最好”模型。跨平台或依赖版本差异可能导致数值差异，本次与交付分数的差异写入核对记录。

3. **仅从已保存预测重算机器学习指标**：

```bash
python -B code/build_evaluation.py --output outputs/evaluation_new
```

默认读取 `outputs/current/`，也可通过 `--source outputs/replay_new/evaluation` 指定另一份本包生成的评估结果。

这些入口复现本次固定日历的历史实验；它们不是自动获取行情或实时预测服务。新增日期或股票池需要明确新的数据和日历，并按同一预处理与特征顺序接入。

## 验证

```bash
python -B code/check_package.py
python -B -m unittest discover -s code -p 'test_*.py' -v
python -B code/verify_evaluation.py --output outputs/current
```

`check_package.py` 校验交付时文件的 SHA-256。`verify_evaluation.py` 独立重算 1,464 行周指标并核对 128 行汇总，会刷新所核验目录的 `verification.json`；若要检查原始包哈希，请先执行 `check_package.py`。核验新运行可把最后一个命令的路径换为 `outputs/replay_new/evaluation` 等。

## 给后续策略同事的接口说明

- 用 `date + ticker` 关联逐周股票排名；`date` 是信号周日期。排名 1 代表模型预测相对表现最好，不保证下一周收益为正。
- `model_*_raw_score` 是各子模型排序分数；`model_*_percentile` 是当周新股票池内的百分位；`ensemble_ranking_score` 是三者均值，越高越靠前。展示整数排名的并列按 ticker 升序打破。
- `actual_next_week_log_return` 是下一周复权收盘价对数收益，`actual_rank_*`、`actual_relevance_0_to_4` 是事后评价列，不能作为当时选股信号。分数不是预测收益率、股价或上涨概率。
- 模型 1 使用五因子和 156 周窗口；模型 2 使用盈利能力、债务资产比和 52 周窗口；模型 3 使用五因子和 52 周窗口。每 26 周重新训练，每周预测。训练因子在原 66 股内部逐周做百分位转换；预测因子在当周可用的新股票内部转换，不混合两股票池。
- 当前历史预测覆盖 2019-08-30 至 2026-08-28，共 366 周。Final Test 为 2025-09-05 至 2026-08-21，共 51 周，仅为报告区间；未在新 40 股上选参。
- 训练规则为 `label_end_week <= refit_week`，按周末信息可得的信号假设生成。后续成交时点、执行价格和信息可得性需在回测实现中明确，不能把同一周末才形成的信号当成更早已知。
- 新 40 股数据没有完整价格序列，标签含义由用户确认，无法从价格独立重建。后续需要实际成交价、复权行情、费用等时，应另行补充。本包不把标签当作可成交价格。
- `inputs/train66.csv` 仅从原训练 CSV 按列提取日期、股票代码、复权收盘价、target 和五因子；保留原文本数值，删除未使用的其他因子。`inputs/test40.csv` 保留原转换 CSV，`target1` 用于评价，`target2` 不使用。
- 因子发布时间尚未独立核验。长期不变值的检查保留在 `audit/factor_quality.csv`，本次交接没有清洗或修改输入数值。

全部指标定义见 `docs/指标说明.md`；当前 CSV 与交接前最新版的对应 CSV 内容保持一致。
