# XGBoostRanker (optimised version)

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

The completed optimised Ranker: label schemes and hyperparameters are searched within Development only, frozen, and then evaluated on Validation / Final Test.

### Files

- `train_xgboost_ranker.py` (original name `train_xgboostranker_optimized.py`): full training, Development selection, frozen configuration and later evaluation.
- `results/xgboostranker_optimized_results.csv`: delivered results, four factor sets × three stages × eight metrics, 12 rows.
- `results/baseline_results.csv`: results of the Ranker before optimisation, used by the `evaluate` phase to build the before/after comparison; keep it when running the full workflow.
- Input data: `data/test_45_factors_weekly.csv` in the project root.

### Running (from the project root)

```bash
python research/05_xgboost_ranker/train_xgboost_ranker.py --check-only
python research/05_xgboost_ranker/train_xgboost_ranker.py --phase all                 # output to outputs/run by default
# or in two steps: select and freeze in Development first, then evaluate
python research/05_xgboost_ranker/train_xgboost_ranker.py --phase tune     --run-dir research/05_xgboost_ranker/outputs/run2
python research/05_xgboost_ranker/train_xgboost_ranker.py --phase evaluate --run-dir research/05_xgboost_ranker/outputs/run2
```

`--run-dir` must be a folder that does not exist yet; `evaluate` checks the frozen records, input and script hashes of the same `tune` run. Per-stock predictions of the selected configurations are also written to `research/predictions/RANKER-R6-F{n}.csv`.

Environment of the delivered results: Python 3.12.10, NumPy 2.5.4, pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1, XGBoost 3.4.1. Different library versions may produce numerical differences.

### Fixed experiment rules

- Train on the latest 6 calendar years, refit every 26 weeks; predict every week and hold an equal-weight Top-5 portfolio.
- Factor sets are 5, 7, 11 (7 internal factors plus 4 macro factors) and 45 factors.
- Each fit uses only realised labels with `label_end_date < fit_date`. The imputation medians and 1% / 99% winsorisation thresholds are computed from the current training window only.
- Development is 2022-09-02 to 2024-08-30, 105 weeks; Validation is 2024-09-06 to 2025-08-29, 52 weeks; Final Test is 2025-09-05 to 2026-08-21, 51 weeks and 3,304 predictions.
- Each factor set has 36 predefined label/hyperparameter candidates (144 in total), selected using Development only; all four configurations are frozen before later evaluation.
- Gates are Rank IC > 0, Rank ICIR >= 0.05 and positive Rank IC weeks >= 50%; passing candidates are ranked by Development Top5 Excess, Rank IC and Rank ICIR in descending order, with the lower candidate number winning exact ties.
- What is frozen is the label scheme and the hyperparameters; the model is still refitted on a rolling 26-week schedule using the historical labels realised at that time.

### Eight evaluation metrics

IC, ICIR, Rank IC, Rank ICIR, Annualized Return, Information Ratio, Top5 Excess and Positive Rank IC, consistent with the original XGBoost.

Training labels are within-week grades of stock returns, and predictions are ranking scores. Evaluation and portfolio returns always use realised returns; grade labels or prediction scores are never treated as returns. ICIR and Rank ICIR are not annualised; the Information Ratio is annualised by the square root of 52; Top5 Excess is the geometric annualisation of the weekly excess returns, not the difference of two annualised returns. Transaction costs are not deducted.

### Delivered Final Test results

| Factor set | IC | ICIR | Rank IC | Rank ICIR | Annualised return | Information ratio | Top5 Excess | Positive Rank IC weeks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.0485 | 0.3314 | 0.0503 | 0.3610 | 23.80% | 1.1827 | 16.10% | 66.67% |
| 7 | 0.0322 | 0.2133 | 0.0302 | 0.1875 | 9.93% | 0.3142 | 4.13% | 56.86% |
| 11 | 0.0069 | 0.0467 | 0.0117 | 0.0796 | 8.14% | 0.1883 | 1.84% | 49.02% |
| 45 | 0.0039 | 0.0243 | 0.0244 | 0.1524 | -7.27% | -0.5735 | -12.39% | 49.02% |

The CSV keeps unrounded values; returns and shares are stored as decimals.

> **Reproducibility note**: the model uses `subsample=0.8`. When rerun on Linux on 2026-10-23, Development selected different candidates (candidate 13 for 5, 7 and 45 factors; candidate 18 for 11 factors) and the stage metrics differ clearly from the table above (e.g. 5-factor Final Test annualised −17.3%). Exact independent refitting of the original models has not been established across environments; see the [frozen-model reproducibility rationale](../../README.md#why-the-trained-models-are-frozen).

### Comparability with the other three models

Input data, factors, rolling window, refit schedule and the eight evaluation metrics are the same. Under the previously agreed protocol, Ranker and XGBoost select on 105 Development signal weeks, while Ridge and Random Forest use 104 weeks. The Ranker's candidate search budget is also larger, so result differences cannot be attributed entirely to the algorithm.

The original Final Test had been viewed before. The optimised version did not use Validation or Final Test metrics to select candidates, but this round is an iterative experiment and cannot be called a never-observed independent test.

---

<a id="readme-zh"></a>

## 中文

已完成的优化版 Ranker：仅在 Development 内搜索标签方案和超参数，随后冻结配置，再在 Validation / Final Test 上评估。

### 文件

- `train_xgboost_ranker.py`，原名 `train_xgboostranker_optimized.py`：完整训练、Development 选参、冻结配置及后续评估。
- `results/xgboostranker_optimized_results.csv`：交付结果，四组因子 × 三个阶段 × 八项指标，共 12 行。
- `results/baseline_results.csv`：优化前 Ranker 结果，`evaluate` 阶段用其建立优化前后对比；完整流程运行时应保留。
- 输入为项目根目录下的 `data/test_45_factors_weekly.csv`。

### 运行方式（在项目根目录）

```bash
python research/05_xgboost_ranker/train_xgboost_ranker.py --check-only
python research/05_xgboost_ranker/train_xgboost_ranker.py --phase all                 # 默认输出到 outputs/run
# 也可分两步：先在 Development 选参并冻结，再评估
python research/05_xgboost_ranker/train_xgboost_ranker.py --phase tune     --run-dir research/05_xgboost_ranker/outputs/run2
python research/05_xgboost_ranker/train_xgboost_ranker.py --phase evaluate --run-dir research/05_xgboost_ranker/outputs/run2
```

`--run-dir` 在创建调参运行时必须是尚不存在的目录；`evaluate` 会检查同一 `tune` 运行的冻结记录、输入及脚本哈希。入选配置的逐股预测还会写入 `research/predictions/RANKER-R6-F{n}.csv`。

交付结果的环境：Python 3.12.10、NumPy 2.5.4、pandas 3.0.6、SciPy 1.18.1、scikit-learn 1.9.1、XGBoost 3.4.1。不同库版本可能产生数值差异。

### 固定实验规则

- 使用最近 6 个自然年的数据训练，每 26 周重新拟合；逐周预测并持有等权 Top-5 组合。
- 因子集合为 5、7、11（7 个内部加 4 个宏观因子）和 45 因子。
- 每次拟合只使用 `label_end_date < fit_date` 的已实现标签。缺失值填充中位数和 1% / 99% 缩尾阈值只从当前训练窗口计算。
- Development 为 2022-09-02 至 2024-08-30，共 105 周；Validation 为 2024-09-06 至 2025-08-29，共 52 周；Final Test 为 2025-09-05 至 2026-08-21，共 51 周、3,304 条预测。
- 每组因子有 36 个预定义标签/超参数候选，共 144 个，仅在 Development 选择；四组配置都在后续评估前冻结。
- 门槛为 Rank IC > 0、Rank ICIR >= 0.05，以及 Rank IC 为正的周占比 >= 50%。通过者按 Development Top5 Excess、Rank IC、Rank ICIR 依次降序排列，完全并列时选候选编号较小者。
- 冻结的是标签方案和超参数；模型仍按每 26 周滚动日程，使用当时已实现的历史标签重新拟合。

### 八项评估指标

IC、ICIR、Rank IC、Rank ICIR、Annualized Return、Information Ratio、Top5 Excess 和 Positive Rank IC，与原始 XGBoost 的指标口径一致。

训练标签是股票收益的周内等级，预测输出是排名分数。评估和组合收益始终使用已实现收益，不能把等级标签或预测分数当作收益。ICIR 和 Rank ICIR 不年化；信息比率乘以 52 的平方根年化；Top5 Excess 是周度超额收益的几何年化，不是两个年化收益相减。未扣除交易成本。

### 交付的 Final Test 结果

| 因子集合 | IC | ICIR | Rank IC | Rank ICIR | 年化收益 | 信息比率 | Top5 Excess | Rank IC 为正的周占比 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.0485 | 0.3314 | 0.0503 | 0.3610 | 23.80% | 1.1827 | 16.10% | 66.67% |
| 7 | 0.0322 | 0.2133 | 0.0302 | 0.1875 | 9.93% | 0.3142 | 4.13% | 56.86% |
| 11 | 0.0069 | 0.0467 | 0.0117 | 0.0796 | 8.14% | 0.1883 | 1.84% | 49.02% |
| 45 | 0.0039 | 0.0243 | 0.0244 | 0.1524 | -7.27% | -0.5735 | -12.39% | 49.02% |

CSV 保留未四舍五入的值，收益与占比按小数存储。

> **复现说明：**模型使用 `subsample=0.8`。在 Linux 上于 2026-10-23 重跑时，Development 选择了不同候选：5、7、45 因子为候选 13，11 因子为候选 18；阶段指标与上表明显不同，例如 5 因子 Final Test 年化收益约为 −17.3%。尚未建立跨环境独立重新拟合原模型的精确复现，详见[冻结模型的复现理由](../../README.md#why-the-trained-models-are-frozen)。

### 与其他三个模型的可比性

输入数据、因子、滚动窗口、重新拟合日程和八项评估指标相同。按此前约定的协议，Ranker 和 XGBoost 使用 105 个 Development 信号周选参，Ridge 与 Random Forest 使用 104 周。Ranker 的候选搜索预算也更大，因此结果差异不能完全归因于算法。

原始 Final Test 已经被查看过。优化版没有使用 Validation 或 Final Test 指标选择候选，但本轮仍属于迭代实验，不能称为从未查看过的独立测试。
