# Ridge 统一配置实验

这个文件夹包含可上传的四个文件：Ridge 脚本、运行结果、66 只股票的周频数据，以及本说明文件。版本日期：2026-10-13。

## 实验口径

- 模型：带截距的 Ridge 回归；截距不受惩罚，目标为 `sum((y - prediction)^2) + alpha * sum(coef^2)`。
- 标签：`target`，已经前向对齐的下一周对数收益；不转换成 Ranker 使用的 0–4 relevance levels。
- 股票池：66 只股票；个别周有缺失，不能把每周有效股票数量都当成 66。
- 因子版本：5 因子、7 因子、7 个内部因子加 4 个宏观因子（11 因子）和 45 因子。这里的“四类”指四套输入组合，不是三因子遍历。
- 训练历史：6 个**日历年**的 trailing window，不是固定 312 个观测周。
- 更新频率：每 26 个日历周（182 天）形成一个重训区间，在区间首个实际信号日重新拟合。不是 26 个月，也不是每个阶段重新计数。
- 阶段：Development、Validation、Final Test 按 signal date 划分；跨阶段的重训区间仍保留每条预测自身的阶段。
- 选参：只用 Development。候选先通过 Mean Rank IC > 0、Rank ICIR >= 0.05、正 Rank IC 周比例 >= 50% 的门槛，再选择 Development Top-5 超额年化收益最高的候选。
- Validation 和 Final Test：使用冻结后的 alpha，不重新调参；模型仍按 26 周进行时间顺序重训，仅使用 `label_end_date < fit_date` 的已实现标签。
- 本版本只运行 rolling；不加入固定窗口、三因子遍历或其他额外实验。

### 与队友版本的对齐及明确差异

输入 CSV 与队友 XGBoost 四文件包逐字节相同，SHA-256：

`26e234363e83f2eaefe0ba787b6909be0999f6d4405fbf6ef2e2c7cb8b918d97`

四套因子列、有效样本、6 年日历窗口、26 周重训日期、信号日阶段划分及八项汇总指标公式均已核对。模型特有的 alpha 网格和标准化不需要模仿树模型。

**选参边界有一处保留的安全差异：**队友脚本将 Development 的全部信号周用于评分；本 Ridge 延续原版检查，选参时额外要求 `label_end_date < Validation 首个信号日`。2024-08-30 的 62 条标签在 2024-09-06 才实现，所以不参与 alpha 选择。实际选参使用 104 周、6,410 条记录；阶段汇报仍按 signal date 展示完整 Development 的 105 周、6,472 条记录。因此汇总表的 Development 指标不是选参评分的直接副本。若团队需要严格一致的选参样本，应在队友代码也加入同样的标签边界检查；不能声称目前这点完全一致。

## 文件说明

- `train_ridge_5_7_11_45_6y26w.py`：独立主训练脚本，只依赖 NumPy、pandas。
- `test_45_factors_weekly.csv`：与队友相同的输入数据，脚本从中读取四套因子。
- `ridge_5_7_11_45_6y26w_results.csv`：已完成的 rolling 结果，保留队友的指标列，另加 Alpha、Status、周数、样本数、信号起止日期和选参样本数。
- `README.md`：本说明文件。

结果 CSV 共 10 行：通过门槛的 5、7、11 因子各有三个阶段，共 9 行；45 因子有一行 `no_candidate_passed` 状态。空指标表示没有入选、没有该阶段结果，**不是零分或程序遗漏**。45 因子的六组候选已经完成 Development 评估，但按门槛规则不运行 Validation／Final Test，也不强行选“最好的一组”。

## 运行方式

在本文件夹打开 PowerShell：

```powershell
python -m pip install numpy pandas
python train_ridge_5_7_11_45_6y26w.py --mode rolling --feature-set all --rolling-years 6 --output .\ridge_5_7_11_45_6y26w_results_new.csv
```

如果希望明确指定数据和输出文件：

```powershell
python train_ridge_5_7_11_45_6y26w.py `
  --mode rolling `
  --feature-set all `
  --rolling-years 6 `
  --input .\test_45_factors_weekly.csv `
  --output .\ridge_5_7_11_45_6y26w_results_new.csv
```

输出路径相对于当前工作目录；脚本默认输入、输出位于脚本所在文件夹。为保护已交付结果，已有输出文件不会被覆盖，重跑请指定一个尚不存在的 `--output`。每种因子集合各评估六个 alpha：`0.01, 0.1, 1, 10, 100, 1000`，共 24 个候选。并列时依次按 Top5 Excess、Rank IC、Rank ICIR 降序，再按 alpha 升序确定结果。

仅检查数据和日期、不训练、不写结果：

```powershell
python train_ridge_5_7_11_45_6y26w.py --check-only
```

需要逐股 prediction／actual 和选参记录时，可以额外指定一个尚不存在的 `--audit-dir .\audit_new`。审计文件不在默认四文件交付包中，以免与唯一汇总结果表混淆。

## 因子与预处理

- 5 因子：`revenue_growth_yoy`, `operating_profitability`, `cashflow_to_assets`, `debt_to_assets`, `asset_growth_yoy`。
- 7 因子：`revenue_growth_yoy`, `ret_120d`, `cashflow_to_assets`, `ret_1d`, `ret_5d`, `close_location_value`, `body_range_ratio`。
- 11 因子：上述 7 因子，加 `macro_vix_level`, `macro_vix_change_5obs`, `macro_yield_spread_10y_2y`, `macro_dgs10_change_5obs`。
- 45 因子：输入表中排除 `date, ticker, open, high, low, close, adj_close, volume, target, target2` 后的全部 45 列，保留原始列顺序。

每次重训仅用当前训练样本计算缺失值中位数、1%／99% winsorisation 边界、均值及总体标准差，然后将同一变换用于该区间的预测。零标准差取 1；整列缺失时填 0。**Ridge 做标准化；队友的 XGBoost 不做标准化，这是算法需要，不是窗口规则不一致。**

## 实际日期与样本

原始输入：2016-09-02 至 2026-08-28，522 个信号日、27,651 条记录。将 target 与下一全市场观测周的同股复权价格核对，最大误差为 `5.21e-16`。最后一周 66 条没有下一周价格，另有 16 条缺少下一周同股价格，共排除 82 条；保留 27,569 条可核验标签，包含训练历史。

| 阶段 | 实际信号范围 | 周数 | 记录数 |
|---|---|---:|---:|
| Development 汇报 | 2022-09-02 至 2024-08-30 | 105 | 6,472 |
| Development 选参 | 2022-09-02 至 2024-08-23 | 104 | 6,410 |
| Validation | 2024-09-06 至 2025-08-29 | 52 | 3,230 |
| Final Test | 2025-09-05 至 2026-08-21 | 51 | 3,304 |

最后可评估信号日为 2026-08-21，其收益标签在 2026-08-28 实现。八次重训日期为：2022-09-02、2023-03-03、2023-09-01、2024-03-01、2024-08-30、2025-02-28、2025-08-29、2026-02-27。

## 已完成结果

下面只展示 Final Test；完整三个阶段以 CSV 为准。

| 因子集合 | 冻结 alpha | Rank IC | Rank ICIR | Top-5 年化收益 | Top-5 超额年化收益 |
|---|---:|---:|---:|---:|---:|
| 5 因子 | 1000 | 2.7338% | 0.2077 | -14.5591% | -20.0171% |
| 7 因子 | 100 | 4.1675% | 0.2305 | -7.8620% | -13.4696% |
| 11 因子 | 1000 | 3.7280% | 0.2085 | 0.9379% | -4.9331% |
| 45 因子 | 未入选 | — | — | — | — |

45 因子各候选的 Development Rank ICIR 为 0.0045–0.0185，全部低于 0.05 门槛。不能把其未入选解释为模型训练失败。

## 指标公式与解释结果时的注意事项

- IC：每周预测与实际对数收益的 Pearson 相关系数，再对有效周取均值。
- Rank IC：每周 Spearman 相关系数（平均秩处理并列），再取均值。
- ICIR／Rank ICIR：对应周序列的均值除以样本标准差 `ddof=1`，**不乘 sqrt(52)**。
- Top-5：每周取预测最高的 5 股，其简单收益 `expm1(target)` 等权平均。
- 基准：同周有可核验标签的股票简单收益等权平均；不是 SPY 或外部指数。
- Annualized Return：`exp(mean(log(1 + weekly_top5_return)) * 52) - 1`。
- Top5 Excess：先计算每周 Top-5 收益减同周基准收益，再对这个超额序列按同一公式年化；**不是两个年化收益相减**。
- Information Ratio：每周超额收益均值／样本标准差，乘 `sqrt(52)`。
- Positive Rank IC：有效 Rank IC 周中，大于零的周占比。

CSV 的相关系数、收益、周比例均保存为原始小数；例如 `0.041675` 表示 Rank IC 约 4.17%，不是 0.041675%。指标列与队友一致；本表不额外加入 RMSE。Ridge 是连续收益回归，可以另算回归误差，但 Ranker 分数不能直接用同一 RMSE 口径。

结果为费用前的历史比较，不是可执行交易收益。11 因子虽有轻微正的 Top-5 年化收益，但超额收益仍为负；正 Rank IC 也不保证获利。四套因子是既定输入组合，本次没有重新证明它们的筛选独立于历史测试期；该数据在此前实验中已经使用，不能声称 Final Test 是从未观察过的独立新数据。

## 二次核验

已逐字节核对队友输入数据，并核对因子、有效样本和日历重训规则。对入选三套模型的八次重训共 24 次预测，使用独立的增广最小二乘实现重算；最大预测误差 `1.29e-16`。对全部九行阶段指标独立复算，最大绝对误差 `3.56e-15`。选参门槛、冻结 alpha 和未入选状态均已核验。
