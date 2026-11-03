# 评估与回测

[English](README.md) | **中文**

<a id="readme-zh"></a>

使用统一规则评估四类模型（Ridge、Random Forest、XGBoost、XGBRanker，各含 5/7/11/45 因子）的逐股预测：预测能力指标 IC / RankIC / ICIR / RMSE，以及 15 个组合策略 × 14 个区间 × 单边 0/10/25bps 的周度回测，之后执行独立验证。对应报告为 `reports/model_evaluation/model_evaluation_backtest_report_6y26w.pdf`。

### 执行顺序（在项目根目录）

```bash
# 1）训练四类模型，逐股预测写入 research/predictions/
python research/02_ridge/train_ridge.py
python research/03_random_forest/train_random_forest.py
python research/04_xgboost/train_xgboost.py
python research/05_xgboost_ranker/train_xgboost_ranker.py
# 2）评估与回测
python research/06_evaluation_backtest/evaluate.py          # 加 --no-charts 可跳过约 500 张 SVG 图
# 3）独立核验：周度持仓、权重漂移、成本、汇总指标、phase 0、共识分数与预测指标
python research/06_evaluation_backtest/verify.py
```

### 文件

| 文件 | 用途 |
|---|---|
| `strategies.py` | 15 个策略的规则、权重漂移、换手、成本，以及区间切片 |
| `metrics.py` | IC/RankIC/ICIR、MAE/RMSE，以及净值、年化收益、最大回撤、波动率、夏普比率、胜率 |
| `evaluate.py` | 主程序：加载预测 → 验证标签 → 构建同因子的四模型共识 → 回测 → 报告/Dashboard |
| `verify.py` | 不调用 `evaluate.py` 的独立重算程序 |
| `reference_code/` | 报告章节原始代码，仅供参考；依赖的原始 `run.py`、`native_replay.py` 等未保留，无法独立运行 |

`results/` 保留 2026-10-23 的 Linux 运行：`predictions/` 包含四模型的逐股预测，另有 `report.md`、汇总表和历史 `verification.json`。如果要评估这些冻结预测而不重新拟合四模型，在项目根目录执行：

```bash
python research/06_evaluation_backtest/evaluate.py --predictions-dir research/06_evaluation_backtest/results/predictions --output runs/research_evaluation_from_frozen --no-charts
python research/06_evaluation_backtest/verify.py --output runs/research_evaluation_from_frozen
```

每次使用新的输出目录，两条命令的 `--output` 必须一致。这会执行评估、回测与独立重算，不是无需计算的包完整性检查，也不会复现不同原始平台上的预测。所保留研究验证记录对应那次研究运行；所选外部策略另有完整回放和数值验证，见项目根目录的 `docs/VALIDATION.md`。

每次运行会生成完整 `outputs/`（约 126 MB）：`report.md`、交互式 `strategy_dashboard.html`、`strategy_comparison.csv`（全部回测指标）、`model_evaluation.csv`（预测指标）、`weekly_backtest.csv`、`positions.csv`、`phase_sensitivity.csv`、`coverage.csv`、`source_metric_reconciliation.csv`（与各训练脚本交付表对账）、`charts/*.svg` 和 `verification.json`。

### 方法

- 股票收益 = 下一全市场观测周的复权收盘价 / 当前周复权收盘价 − 1；组合毛收益为加权收益之和，现金收益为 0。
- 交易权重 = 目标权重与上周漂移后权重之差的绝对值之和；净收益 = (1 − 交易权重 × 单边成本) × (1 + 毛收益) − 1。
- 每个区间从现金、净值 1 开始；依赖路径的策略（缓冲、2/4 周再平衡）在各区间独立回放。结束时按市值计价，不强制清算。
- 14 个区间包括 FullHistory、最后 13/26/52/104/156 周、各自然年、Development6y、Validation 和 FinalTest。
- 共识为同因子集合四模型周内百分位的等权平均，分数保留 12 位小数，只使用四模型均有预测的股票。Ridge 的 45 因子未通过门槛，因此没有 45 因子共识。
- 年化收益 = 净值^(52 / 周数) − 1；夏普比率 = 周收益均值 × 52 / 年化波动率；ICIR 不年化。

### 与原始报告的关系

`evaluate.py` 是对报告章节代码的整理重写：策略、区间、成本、标签检查和共识规则逐项遵循 `reference_code/full_history_backtest.py`、`portfolio_strategies.py` 和 `evaluate_latest.py`；缺失的 `run.py` 引擎依据 `reference_code/verify_latest.py` 与 `verify_prediction_metrics.py` 的公式重建。使用 Ridge 预测重跑时，报告第 6–7 页的表格精确匹配，11,340 个主回测和 972 个阶段偏移测试也与报告数量一致。XGBoost 与 XGBRanker 使用随机子采样，因此不同平台可能产生不同预测，详见[冻结模型的复现理由](../../README.zh-CN.md#why-the-trained-models-are-frozen)。

> 研究局限：同收盘价生成信号并以同收盘价入场属于研究假设，未建模滑点、市场冲击和容量。完整历史包含调参区间，Final Test 曾在更早轮次被查看。各模型“最佳 Final Test 策略”是事后挑选，存在多重比较偏差。

### 原始研究结果的报告引用口径

项目报告引用模型指标时，以各模型 `research/02_ridge/results/`、`research/03_random_forest/results/`、`research/04_xgboost/results/` 和 `research/05_xgboost_ranker/results/` 中原始交付结果表为准。`research/06_evaluation_backtest/results/` 中的统一评估单独保留，表示对归档重跑预测的评估；它不替代原始交付表，也不证明复现了其中不同的指标。这一报告口径不改变独立的冻结外部 Ensemble 回放。
