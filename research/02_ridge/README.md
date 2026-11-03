# Ridge: common-protocol experiment

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

Version date: 2026-10-13.

### Protocol

- Model: Ridge regression with an intercept; the intercept is not penalised and the objective is `sum((y - prediction)^2) + alpha * sum(coef^2)`.
- Label: `target`, the forward-aligned next-week log return; it is not converted to the 0–4 relevance levels used by the Ranker.
- Universe: 66 stocks; some weeks have missing stocks, so the number of valid stocks per week is not always 66.
- Factor sets: 5 factors, 7 factors, 7 internal factors plus 4 macro factors (11 factors), and 45 factors. "Four sets" means four input combinations, not an enumeration of three-factor subsets.
- Training history: a trailing window of 6 **calendar years**, not a fixed 312 observed weeks.
- Refit frequency: every 26 calendar weeks (182 days) forms a refit block, refitted on the first actual signal date of the block. It is not 26 months, and the count does not restart at each stage.
- Stages: Development, Validation and Final Test are split by signal date; a refit block that crosses a stage boundary keeps each prediction's own stage.
- Selection: Development only. Candidates must pass Mean Rank IC > 0, Rank ICIR >= 0.05 and positive Rank IC weeks >= 50%; the candidate with the highest Development Top-5 excess annualised return is then selected.
- Validation and Final Test: use the frozen alpha without retuning; the model is still refitted chronologically every 26 weeks, using only realised labels with `label_end_date < fit_date`.
- This version runs rolling mode only; no fixed window, three-factor enumeration or other extra experiments.

#### Alignment with the teammate's version and explicit differences

The input CSV is byte-identical to the teammate's four-file XGBoost package, SHA-256:

`26e234363e83f2eaefe0ba787b6909be0999f6d4405fbf6ef2e2c7cb8b918d97`

The four factor sets, valid samples, 6-calendar-year window, 26-week refit dates, signal-date stage split and the eight summary metric formulas have all been checked. The model-specific alpha grid and standardisation do not need to imitate the tree models.

**One deliberate safety difference remains at the selection boundary:** the teammate's script scores all Development signal weeks; this Ridge keeps the original check and additionally requires `label_end_date < first Validation signal date` during selection. The 62 labels of 2024-08-30 are only realised on 2024-09-06, so they do not take part in alpha selection. Selection actually uses 104 weeks and 6,410 records; stage reporting still shows the full Development period by signal date, 105 weeks and 6,472 records. The Development metrics in the summary table are therefore not a direct copy of the selection scores. If the team needs exactly the same selection sample, the teammate's code should add the same label-boundary check; this point cannot be claimed to be identical at present.

### Files

- `train_ridge.py`: main training script (original name `train_ridge_5_7_11_45_6y26w.py`); depends only on NumPy and pandas.
- `results/ridge_5_7_11_45_6y26w_results.csv`: the delivered rolling results.
- Input data: `data/test_45_factors_weekly.csv` in the project root (identical for all four models).

The results CSV has 10 rows: three stages each for the 5, 7 and 11 factor sets that passed the gate (9 rows), plus one `no_candidate_passed` row for 45 factors. Empty metrics mean "not admitted / no result for that stage", **not a zero score or a program omission**.

### Running (from the project root)

```bash
python research/02_ridge/train_ridge.py --check-only     # only check data and dates
python research/02_ridge/train_ridge.py                  # full training
```

- Results are written to `research/02_ridge/outputs/ridge_5_7_11_45_6y26w_results.csv`; to protect existing results the script refuses to overwrite an existing output file, so delete it or pass a new `--output` before rerunning.
- Per-stock predictions of the selected configurations are written to `research/predictions/RIDGE-R6-F{5,7,11}.csv` for `06_evaluation_backtest`.
- Add `--audit-dir NEW_FOLDER` for audit files such as selection records and the refit schedule.
- Each factor set evaluates six alphas: `0.01, 0.1, 1, 10, 100, 1000`, 24 candidates in total. Ties are broken by Top5 Excess, Rank IC and Rank ICIR in descending order, then by alpha in ascending order.
- The console ends with three tables: the selected hyperparameter (alpha), the stage prediction metrics, and the stage Top-5 portfolio metrics.

### Factors and preprocessing

- 5 factors: `revenue_growth_yoy`, `operating_profitability`, `cashflow_to_assets`, `debt_to_assets`, `asset_growth_yoy`.
- 7 factors: `revenue_growth_yoy`, `ret_120d`, `cashflow_to_assets`, `ret_1d`, `ret_5d`, `close_location_value`, `body_range_ratio`.
- 11 factors: the 7 factors above plus `macro_vix_level`, `macro_vix_change_5obs`, `macro_yield_spread_10y_2y`, `macro_dgs10_change_5obs`.
- 45 factors: all 45 columns of the input table after excluding `date, ticker, open, high, low, close, adj_close, volume, target, target2`, in their original order.

At every refit, the missing-value medians, 1% / 99% winsorisation bounds, means and population standard deviations are computed from the current training sample only and the same transform is applied to that block's predictions. A zero standard deviation is replaced by 1; an entirely missing column is filled with 0. **Ridge standardises its inputs; the teammate's XGBoost does not, as the algorithm requires — this is not an inconsistency in the window rules.**

### Actual dates and samples

Raw input: 2016-09-02 to 2026-08-28, 522 signal dates, 27,651 records. Checking `target` against the same stock's adjusted price in the next market-wide observed week gives a maximum error of `5.21e-16`. The final week's 66 records have no next-week price and another 16 lack the same stock's next-week price, so 82 records are excluded; 27,569 verifiable labels remain, including training history.

| Stage | Actual signal range | Weeks | Records |
|---|---|---:|---:|
| Development (reporting) | 2022-09-02 to 2024-08-30 | 105 | 6,472 |
| Development (selection) | 2022-09-02 to 2024-08-23 | 104 | 6,410 |
| Validation | 2024-09-06 to 2025-08-29 | 52 | 3,230 |
| Final Test | 2025-09-05 to 2026-08-21 | 51 | 3,304 |

The last evaluable signal date is 2026-08-21, whose label is realised on 2026-08-28. The eight refit dates are 2022-09-02, 2023-03-03, 2023-09-01, 2024-03-01, 2024-08-30, 2025-02-28, 2025-08-29 and 2026-02-27.

### Delivered results

Final Test only; the CSV has all three stages.

| Factor set | Frozen alpha | Rank IC | Rank ICIR | Top-5 annualised return | Top-5 excess annualised return |
|---|---:|---:|---:|---:|---:|
| 5 factors | 1000 | 2.7338% | 0.2077 | -14.5591% | -20.0171% |
| 7 factors | 100 | 4.1675% | 0.2305 | -7.8620% | -13.4696% |
| 11 factors | 1000 | 3.7280% | 0.2085 | 0.9379% | -4.9331% |
| 45 factors | not admitted | — | — | — | — |

The Development Rank ICIR of the 45-factor candidates ranges from 0.0045 to 0.0185, all below the 0.05 gate. Its non-admission must not be read as a training failure.

### Metric formulas and interpretation

- IC: weekly Pearson correlation between predictions and realised log returns, averaged over valid weeks.
- Rank IC: weekly Spearman correlation (average ranks for ties), averaged.
- ICIR / Rank ICIR: mean of the weekly series divided by its sample standard deviation (`ddof=1`), **not multiplied by sqrt(52)**.
- Top-5: each week the 5 stocks with the highest predictions, equal-weighting their simple returns `expm1(target)`.
- Benchmark: equal-weight simple return of stocks with verifiable labels in the same week; not SPY or an external index.
- Annualized Return: `exp(mean(log(1 + weekly_top5_return)) * 52) - 1`.
- Top5 Excess: first compute weekly Top-5 return minus the same week's benchmark, then annualise that excess series with the same formula; **not the difference of two annualised returns**.
- Information Ratio: mean weekly excess return / sample standard deviation, multiplied by `sqrt(52)`.
- Positive Rank IC: share of valid Rank IC weeks that are above zero.

Correlations, returns and week shares are stored as raw decimals in the CSV; e.g. `0.041675` means a Rank IC of about 4.17%, not 0.041675%. The metric columns match the teammate's; RMSE is not added to this table. Ridge is a continuous return regression, so regression errors could be computed, but Ranker scores cannot use the same RMSE definition.

Results are historical comparisons before costs, not executable trading returns. The 11-factor set has a slightly positive Top-5 annualised return but a negative excess return; a positive Rank IC does not guarantee profit. The four factor sets are predefined inputs, and their screening was not re-shown to be independent of the historical test period; the data were used in earlier experiments, so the Final Test cannot be called never-observed new data.

### Second verification

The teammate's input data were checked byte for byte, as were the factors, valid samples and calendar refit rules. The 24 predictions from the eight refits of the three admitted models were recomputed with an independent augmented least-squares implementation; the maximum prediction error is `1.29e-16`. All nine stage-metric rows were recomputed independently with a maximum absolute error of `3.56e-15`. The selection gates, frozen alphas and non-admitted status were all verified.

---

<a id="readme-zh"></a>

## 中文

版本日期：2026-10-13。

### 实验协议

- 模型为带截距的 Ridge 回归，截距不受惩罚；目标函数是 `sum((y - prediction)^2) + alpha * sum(coef^2)`。
- 标签 `target` 是向前对齐的下一周对数收益，不转换为 Ranker 使用的 0–4 相关性等级。
- 股票池包含 66 只股票，部分周有缺失，因此每周有效股票数不一定是 66。
- 因子集合为 5、7、7 个内部因子加 4 个宏观因子（共 11 个），以及 45 因子。“四组”指四种输入组合，不是枚举三因子子集。
- 训练历史采用过去 6 个**自然年**，不是固定 312 个观测周。
- 每 26 个自然周（182 天）形成一个重新拟合区间，在该区间第一个实际信号日重新拟合。不是每 26 个月，也不会在每个阶段重新计数。
- Development、Validation 与 Final Test 按信号日期划分；拟合区间跨越阶段边界时，各条预测仍保留自身所属阶段。
- 仅在 Development 选择参数。候选必须满足平均 Rank IC > 0、Rank ICIR >= 0.05、Rank IC 为正的周占比 >= 50%，再按 Development 的 Top-5 超额年化收益最高者选定。
- Validation 和 Final Test 使用冻结的 alpha，不再调参；模型仍按时间顺序每 26 周拟合，且只使用 `label_end_date < fit_date` 的已实现标签。
- 当前版本仅运行滚动模式，不运行固定窗口、三因子枚举或其他额外实验。

#### 与队友版本的对齐及明确差异

输入 CSV 与队友提供的四文件 XGBoost 包逐字节一致，SHA-256 为：

`26e234363e83f2eaefe0ba787b6909be0999f6d4405fbf6ef2e2c7cb8b918d97`

已核查四组因子、有效样本、6 自然年窗口、26 周拟合日期、按信号日期分阶段，以及八项汇总指标公式。模型专属的 alpha 网格与标准化不需要模仿树模型。

**参数选择边界仍有一项有意保留的差异：**队友脚本对全部 Development 信号周评分；本 Ridge 在原检查基础上额外要求选参时 `label_end_date < first Validation signal date`。2024-08-30 的 62 个标签要到 2024-09-06 才实现，因此不参与 alpha 选择。实际选参使用 104 周、6,410 条记录；阶段报告仍按信号日期展示完整 Development，即 105 周、6,472 条记录。所以汇总表的 Development 指标并非选参评分的直接复制。若团队要求完全相同的选参样本，队友代码需加入同样的标签边界检查；目前不能声称这一点一致。

### 文件

- `train_ridge.py`：主训练脚本，原名 `train_ridge_5_7_11_45_6y26w.py`，仅依赖 NumPy 与 pandas。
- `results/ridge_5_7_11_45_6y26w_results.csv`：交付的滚动结果。
- 输入为项目根目录下的 `data/test_45_factors_weekly.csv`，四模型相同。

结果 CSV 共 10 行：通过门槛的 5、7、11 因子各三个阶段，共 9 行；45 因子额外保留一行 `no_candidate_passed`。空指标表示“未获准进入 / 该阶段无结果”，**不是零分或程序遗漏**。

### 运行方式（在项目根目录）

```bash
python research/02_ridge/train_ridge.py --check-only     # 仅检查数据与日期
python research/02_ridge/train_ridge.py                  # 完整训练
```

- 结果写入 `research/02_ridge/outputs/ridge_5_7_11_45_6y26w_results.csv`。为保护已有结果，脚本拒绝覆盖现有输出文件；重跑前应使用新的 `--output`，或确认后删除旧输出。
- 入选配置的逐股预测写入 `research/predictions/RIDGE-R6-F{5,7,11}.csv`，供 `06_evaluation_backtest` 使用。
- 使用 `--audit-dir NEW_FOLDER` 可保存选参记录、拟合日程等审计文件。
- 每个因子集合评估六个 alpha：`0.01, 0.1, 1, 10, 100, 1000`，共 24 个候选。并列时依次按 Top5 Excess、Rank IC、Rank ICIR 降序，再按 alpha 升序决胜。
- 控制台最后展示三个表：选中的超参数 alpha、阶段预测指标、阶段 Top-5 组合指标。

### 因子与预处理

- 5 因子：`revenue_growth_yoy`、`operating_profitability`、`cashflow_to_assets`、`debt_to_assets`、`asset_growth_yoy`。
- 7 因子：`revenue_growth_yoy`、`ret_120d`、`cashflow_to_assets`、`ret_1d`、`ret_5d`、`close_location_value`、`body_range_ratio`。
- 11 因子：上述 7 因子，加 `macro_vix_level`、`macro_vix_change_5obs`、`macro_yield_spread_10y_2y`、`macro_dgs10_change_5obs`。
- 45 因子：从输入表排除 `date, ticker, open, high, low, close, adj_close, volume, target, target2` 后，按原顺序使用全部 45 列。

每次拟合的缺失值中位数、1% / 99% 缩尾边界、均值和总体标准差，仅从当前训练样本计算，并将相同变换用于该区间预测。零标准差替换为 1，全空列填为 0。**Ridge 需要标准化输入，队友的 XGBoost 不标准化，这是算法要求，并非窗口规则不一致。**

### 实际日期与样本

原始输入覆盖 2016-09-02 至 2026-08-28，522 个信号日期、27,651 条记录。将 `target` 与同股在下一全市场观测周的复权价格核对，最大误差为 `5.21e-16`。最后一周 66 条记录没有下一周价格，另有 16 条缺少同股下一周价格，因此排除 82 条；剩余 27,569 个可验证标签，包含训练历史。

| 阶段 | 实际信号区间 | 周数 | 记录数 |
|---|---|---:|---:|
| Development（报告） | 2022-09-02 至 2024-08-30 | 105 | 6,472 |
| Development（选参） | 2022-09-02 至 2024-08-23 | 104 | 6,410 |
| Validation | 2024-09-06 至 2025-08-29 | 52 | 3,230 |
| Final Test | 2025-09-05 至 2026-08-21 | 51 | 3,304 |

最后可评估信号日为 2026-08-21，其标签于 2026-08-28 实现。八个拟合日依次为 2022-09-02、2023-03-03、2023-09-01、2024-03-01、2024-08-30、2025-02-28、2025-08-29 和 2026-02-27。

### 交付结果

下表仅展示 Final Test，CSV 包含三个阶段。

| 因子集合 | 冻结 alpha | Rank IC | Rank ICIR | Top-5 年化收益 | Top-5 超额年化收益 |
|---|---:|---:|---:|---:|---:|
| 5 因子 | 1000 | 2.7338% | 0.2077 | -14.5591% | -20.0171% |
| 7 因子 | 100 | 4.1675% | 0.2305 | -7.8620% | -13.4696% |
| 11 因子 | 1000 | 3.7280% | 0.2085 | 0.9379% | -4.9331% |
| 45 因子 | 未通过门槛 | — | — | — | — |

45 因子候选在 Development 的 Rank ICIR 为 0.0045 至 0.0185，均低于 0.05 门槛。未获准进入不应解释为训练失败。

### 指标公式与解读

- IC：每周预测值与已实现对数收益的 Pearson 相关系数，在有效周上取平均。
- Rank IC：每周 Spearman 相关系数，并列值取平均排名，再跨周取平均。
- ICIR / Rank ICIR：周度序列均值除以样本标准差（`ddof=1`），**不乘 sqrt(52)**。
- Top-5：每周选预测最高的五只股票，对其简单收益 `expm1(target)` 等权平均。
- 基准：同周标签可验证股票的简单收益等权平均，不是 SPY 或外部指数。
- 年化收益：`exp(mean(log(1 + weekly_top5_return)) * 52) - 1`。
- Top5 Excess：先逐周计算 Top-5 收益减同周基准，再对该超额序列用相同公式年化，**不是两个年化收益相减**。
- 信息比率：周度超额收益均值 / 样本标准差，再乘 `sqrt(52)`。
- Positive Rank IC：有效 Rank IC 周中大于零的占比。

CSV 中相关系数、收益和周占比以原始小数存储。例如 `0.041675` 表示 Rank IC 约为 4.17%，不是 0.041675%。指标列与队友版本一致，不额外加入 RMSE。Ridge 是连续收益回归，可以计算回归误差，但 Ranker 分数不能使用相同的 RMSE 定义。

结果是未扣成本的历史比较，不是可执行交易收益。11 因子 Top-5 年化收益略正，但超额收益为负；正 Rank IC 不保证盈利。四个因子集合是预定义输入，未重新证明其筛选独立于历史测试区间；数据曾用于早期实验，因此 Final Test 不能称为从未查看的新数据。

### 第二轮核验

已逐字节核对队友输入，并检查因子、有效样本与自然日历拟合规则。对三个获准模型的八次拟合，共 24 组预测，使用独立的增广最小二乘实现重新计算，最大预测误差为 `1.29e-16`。九行阶段指标也独立重算，最大绝对误差为 `3.56e-15`。选参门槛、冻结 alpha 及未获准状态均已验证。
