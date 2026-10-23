# XGBoostRanker 优化版交付文件

本文件夹与其他算法的交付形式一致，包含代码、输入数据、已运行结果和说明。使用当前已完成的优化版 Ranker，不改变训练流程、参数搜索或评估结果。

## 文件

- `train_xgboostranker_optimized.py`：完整训练、Development 选参、冻结配置和后续评估代码。
- `test_45_factors_weekly.csv`：与另外三种算法相同的输入数据。
- `xgboostranker_optimized_results.csv`：已完成的结果，包含四套因子在 Development、Validation、Final Test 的全部八项指标，共12行。
- `baseline_results.csv`：优化前 Ranker 的结果，供代码生成优化前后对比使用；运行完整流程时需要保留。
- `README.md`：本说明。

## 运行

在解压后的文件夹中打开终端，安装依赖：

```bash
python -m pip install numpy pandas scipy scikit-learn "xgboost>=2.0"
```

检查数据、因子和时间划分（不训练）：

```bash
python train_xgboostranker_optimized.py --check-only
```

完整重跑：

```bash
python train_xgboostranker_optimized.py --phase all --run-dir run_new
```

也可分两步执行，先仅在 Development 选参并冻结，再进行后续评估：

```bash
python train_xgboostranker_optimized.py --phase tune --run-dir run_new
python train_xgboostranker_optimized.py --phase evaluate --run-dir run_new
```

首次运行使用一个不存在的输出目录；再次运行请改用新的目录名。新结果、候选评分、预测、冻结记录和训练窗口会写入该目录，已有交付结果不会被覆盖。`evaluate` 必须读取同一次 `tune` 产生的冻结记录，不能单独对空目录运行。

已交付结果的运行环境：Python 3.12.10、NumPy 2.5.4、pandas 3.0.6、SciPy 1.18.1、scikit-learn 1.9.1、XGBoost 3.4.1。不同依赖版本可能产生数值差异。

## 固定实验规则

- 最近6个日历年训练，每26周重新拟合；每周预测并选择Top-5等权组合。
- 因子组合为5、7、11（7个内部因子加4个宏观因子）、45因子。
- 每次训练仅使用 `label_end_date < fit_date` 的已实现标签。填补中位数和1%／99%缩尾阈值只由当前训练窗口计算。
- Development 为2022-09-02至2024-08-30，105周；Validation 为2024-09-06至2025-08-29，52周；Final Test 为2025-09-05至2026-08-21，51周、3,304条预测。
- 每套因子有36个预先确定的标签与参数候选，共144个，只使用Development选择；所有四套配置冻结后再评估。
- 入选门槛为 Rank IC > 0、Rank ICIR >= 0.05、正Rank IC周占比 >= 50%；通过后按Development Top5 Excess、Rank IC、Rank ICIR依次降序选择，完全并列时取候选编号较小者。
- 冻结的是标签方案与超参数，模型仍按26周滚动重训，可使用当时已经实现的历史标签。

## 八项评估指标

IC、ICIR、Rank IC、Rank ICIR、Annualized Return、Information Ratio、Top5 Excess、Positive Rank IC，与原XGBoost保持一致。

训练标签是同一周股票收益的等级，预测结果是排序分数。评估和组合收益始终使用真实收益，不把等级标签或预测分数当作收益率。ICIR及Rank ICIR未年化；Information Ratio按平方根52年化；Top5 Excess是逐周超额收益的几何年化，不是两个年化收益相减。未扣除交易费用。

## 已完成的 Final Test

| 因子组合 | IC | ICIR | Rank IC | Rank ICIR | 年化收益 | 信息比率 | Top5 Excess | 正Rank IC周占比 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.0485 | 0.3314 | 0.0503 | 0.3610 | 23.80% | 1.1827 | 16.10% | 66.67% |
| 7 | 0.0322 | 0.2133 | 0.0302 | 0.1875 | 9.93% | 0.3142 | 4.13% | 56.86% |
| 11 | 0.0069 | 0.0467 | 0.0117 | 0.0796 | 8.14% | 0.1883 | 1.84% | 49.02% |
| 45 | 0.0039 | 0.0243 | 0.0244 | 0.1524 | -7.27% | -0.5735 | -12.39% | 49.02% |

CSV保留未四舍五入的数值，收益及比例以小数存储。

## 与另外三种模型的可比范围

输入数据、因子、滚动窗口、更新周期和八项评估指标一致。按此前确定的口径，Ranker与XGBoost使用105个Development信号周选参，Ridge与Random Forest使用104周。Ranker的候选搜索预算也更大，不能把结果差异全部归因于算法。

此前已经查看过原版Final Test。优化版未使用Validation或Final Test指标选择候选，但本轮属于迭代实验，不能称为从未观察过的独立测试。
