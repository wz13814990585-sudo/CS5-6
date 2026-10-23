# Standard XGBoost 统一配置实验

这个文件夹包含可上传的四个文件：Standard XGBoost 脚本、运行结果、66 只股票的周频数据，以及本说明文件。

## 实验口径

- 模型：`XGBRegressor`，平方误差回归目标。
- 标签：`target`，已经前向对齐的下一周对数收益；不把标签转换成 Ranker 使用的 0–4 relevance levels。
- 股票池：66 只股票。
- 因子版本：5 因子、7 因子、7 个内部因子加 4 个宏观因子（11 因子）和 45 因子。
- 训练历史：6 年 trailing window。
- 更新频率：每 26 周重新拟合一次。
- 阶段：Development、Validation、Final Test 按 signal date 划分；本版本的实际信号起点由数据自动解析，避免使用 label end date 错分阶段。
- 选参：只用 Development。候选先通过 Mean Rank IC > 0、Rank ICIR >= 0.05、正 Rank IC 周比例 >= 50% 的门槛，再选择 Development Top-5 超额年化收益最高的候选。
- Validation 和 Final Test：使用冻结后的超参数，不重新调参；模型仍可按 26 周进行时间顺序重训，且只使用预测时点以前已经实现的标签。

## 文件说明

- `train_xgboost_5_7_11_45_6y26w.py`：主训练脚本。
- `test_45_factors_weekly.csv`：输入数据。脚本从同一份数据中读取四种因子集合。
- `xgboost_5_7_11_45_6y26w_results.csv`：已完成的 6 年、26 周 rolling 运行结果，包含四种因子集合的 Development、Validation 和 Final Test 指标。

## 运行方式

在本文件夹打开 PowerShell：

```powershell
python -m pip install numpy pandas scikit-learn xgboost
python train_xgboost_5_7_11_45_6y26w.py --mode rolling --feature-set all --rolling-years 6
```

如果希望明确指定数据和输出文件：

```powershell
python train_xgboost_5_7_11_45_6y26w.py `
  --mode rolling `
  --feature-set all `
  --rolling-years 6 `
  --input .\test_45_factors_weekly.csv `
  --output .\xgboost_5_7_11_45_6y26w_results_new.csv
```

脚本默认使用 12 组候选超参数。运行时会显示每种因子集合的选参过程、最终冻结参数和三个阶段的结果，并将汇总结果保存为 CSV。

## 解释结果时的注意事项

Standard XGBoost 的输出是连续收益预测，因此可以报告 RMSE；但与 XGBRanker 比较时，应使用共同的排序和策略指标，例如 Rank IC、Rank ICIR、Top-5 年化收益和 Top-5 超额收益。XGBRanker 的输出是排序分数，不能直接当作收益预测值计算 RMSE。

