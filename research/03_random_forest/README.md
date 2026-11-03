# Random Forest Standard Experiment

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

This version aligns Random Forest with the common experiment protocol used for the current Standard XGBoost comparison.

### Configuration

- Model: `RandomForestRegressor` predicting the continuous forward-aligned weekly `target` log return.
- Factor sets: 5 factors, 7 factors, 7 factors plus 4 macro factors (11 total), and all 45 factors.
- Training history: trailing six calendar years.
- Refit schedule: every 26 calendar weeks.
- Development: all RF candidates are evaluated using Development predictions only. Candidates must satisfy Mean Rank IC > 0, Rank ICIR >= 0.05 and positive Rank IC weeks >= 50%; the passing candidate with the highest Development Top-5 excess annualised return is selected.
- Validation and Final Test: the selected parameters are frozen. Models may refit chronologically every 26 weeks, but no later stage is used to retune parameters.
- Stage labels: each prediction row is assigned from its own signal date, including when a 26-week refit block crosses a stage boundary.
- Preprocessing: median imputation and 1%/99% winsorisation are fitted on each training window only.

### Files

- `train_random_forest.py`: training and evaluation script (original name `random_forest_standard_6y_26w.py`).
- `results/random_forest_5_7_11_45_6y26w_results.csv`: delivered stage results (selected parameters per factor set).
- `results/random_forest_5_7_11_45_6y26w_results_development_candidates.csv`: every candidate's Development score and gate status.
- Input: `data/test_45_factors_weekly.csv` at the repository root.

### Run (from the repository root)

```bash
python research/03_random_forest/train_random_forest.py --feature-set all
python research/03_random_forest/train_random_forest.py --feature-set 5     # one factor set
```

Factor set names are `5`, `7`, `7_macro` and `45`. Results go to `research/03_random_forest/outputs/`;
per-stock predictions of the selected parameters go to `research/predictions/RF-R6-F{n}.csv` for `06_evaluation_backtest`.

Candidate grid (18 entries, unchanged): `n_estimators=100`, `max_depth ∈ {4,6,8}`, `min_samples_leaf ∈ {10,20,30}`,
`max_features ∈ {"sqrt", 0.5}`, `random_state=5703`, `n_jobs=-1`. Development selection excludes labels that are only
realised at the Validation boundary (104 selection weeks).

---

<a id="readme-zh"></a>

## 中文

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
