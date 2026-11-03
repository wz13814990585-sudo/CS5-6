# 回归

[English](README.md) | **中文**

<a id="readme-zh"></a>

### 实验协议

- 模型为 `XGBRegressor`，使用平方误差回归目标。
- 标签 `target` 是向前对齐的下一周对数收益，不转换为 Ranker 使用的 0–4 相关性等级。
- 股票池为 66 只股票。
- 因子集合为 5、7、7 个内部因子加 4 个宏观因子（共 11 个），以及 45 因子。
- 训练历史采用过去 6 年滚动窗口，每 26 周重新拟合。
- Development、Validation 与 Final Test 按信号日期划分；实际信号开始日期从数据中确定，避免按标签结束日期错误划分阶段。
- 仅在 Development 选参。候选必须通过平均 Rank IC > 0、Rank ICIR >= 0.05，以及 Rank IC 为正的周占比 >= 50% 门槛，再选择 Development Top-5 超额年化收益最高者。
- Validation 和 Final Test 使用冻结的超参数，不再调参；仍可按时间顺序每 26 周重新拟合，但只使用预测日期前已经实现的标签。

### 文件

- `train_xgboost.py`：主训练脚本，原名 `train_xgboost_5_7_11_45_6y26w.py`。
- `results/xgboost_5_7_11_45_6y26w_results.csv`：交付的 6 年窗口、26 周滚动拟合结果。
- 输入为项目根目录下的 `data/test_45_factors_weekly.csv`。

### 运行方式（在项目根目录）

```bash
python research/04_xgboost/train_xgboost.py --check-only
python research/04_xgboost/train_xgboost.py                      # 默认 --mode rolling --feature-set all
python research/04_xgboost/train_xgboost.py --mode fixed         # 可选：固定窗口对比
```

脚本默认使用 12 组候选超参数：`max_depth ∈ {2,3}`、`min_child_weight ∈ {5,20}`、`n_estimators ∈ {50,150,300}`。结果写入 `research/04_xgboost/outputs/`，选定滚动配置的逐股预测写入 `research/predictions/XGB-R6-F{n}.csv`。

> **复现说明：**模型使用 `subsample=0.8` 和 `colsample_bytree=0.8`。报告第 3 页记录了重新运行交付脚本与原交付 CSV 的明显差异，例如 5 因子 Final Test 毛年化收益为 −20.80%，原表为 −13.58%。原包没有保留冻结超参数或逐股预测，因此不能确定原因。`06_evaluation_backtest` 中的 “XGB” 始终指用本脚本重跑得到的预测。

### 结果解读

Standard XGBoost 输出连续收益预测，因此可以报告 RMSE；与 XGBRanker 比较时，应使用共同的排名和策略指标，如 Rank IC、Rank ICIR、Top-5 年化收益及 Top-5 超额收益。XGBRanker 输出排名分数，不能将其视为收益预测来计算同一含义的 RMSE。
