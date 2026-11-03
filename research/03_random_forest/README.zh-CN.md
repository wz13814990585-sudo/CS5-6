# 随机森林

[English](README.md) | **中文**

<a id="readme-zh"></a>

本版本将 Random Forest 对齐到当前 Standard XGBoost 对比所采用的共同实验协议。

### 配置

- 模型为 `RandomForestRegressor`，预测向前对齐的连续周度 `target` 对数收益。
- 因子集合为 5、7、7 因子加 4 个宏观因子（共 11 个），以及全部 45 因子。
- 训练历史为过去六个自然年，每 26 个自然周重新拟合。
- Development：仅用 Development 预测评估所有 RF 候选。候选须满足平均 Rank IC > 0、Rank ICIR >= 0.05，以及 Rank IC 为正的周占比 >= 50%；通过门槛后选择 Development Top-5 超额年化收益最高的候选。
- Validation 与 Final Test：冻结已选参数。模型可按时间顺序每 26 周重新拟合，但不使用后续阶段调参。
- 每条预测按自身信号日期划分阶段，即使 26 周拟合区间跨越阶段边界也如此。
- 缺失值中位数填充与 1% / 99% 缩尾参数，仅在各自训练窗口中拟合。

### 文件

- `train_random_forest.py`：训练评估脚本，原名 `random_forest_standard_6y_26w.py`。
- `results/random_forest_5_7_11_45_6y26w_results.csv`：交付的阶段结果，包含各因子集合选定参数。
- `results/random_forest_5_7_11_45_6y26w_results_development_candidates.csv`：每个候选的 Development 得分与门槛状态。
- 输入为仓库根目录下的 `data/test_45_factors_weekly.csv`。

### 运行方式（在仓库根目录）

```bash
python research/03_random_forest/train_random_forest.py --feature-set all
python research/03_random_forest/train_random_forest.py --feature-set 5     # 只运行一组因子
```

因子集合名称为 `5`、`7`、`7_macro` 和 `45`。结果写入 `research/03_random_forest/outputs/`；选定参数的逐股预测写入 `research/predictions/RF-R6-F{n}.csv`，供 `06_evaluation_backtest` 使用。

候选网格保持 18 组：`n_estimators=100`、`max_depth ∈ {4,6,8}`、`min_samples_leaf ∈ {10,20,30}`、`max_features ∈ {"sqrt", 0.5}`、`random_state=5703`、`n_jobs=-1`。Development 选参排除直到 Validation 边界才实现的标签，因此使用 104 个选参周。
