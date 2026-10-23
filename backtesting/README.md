# 新40股完整回测模块

`external40/` 来自2026年10月23日收到的 `Ensemble完整复现工程_20261023.zip`，1,396个文件原样保留。包含引擎、输入、模型、冻结预测、历史结果、核验、图表和页面源码。没有运行包内脚本，没有重算指标和回测。

## 文件入口

| 位置（相对 external40/） | 用途 |
|---|---|
| `integer_backtest.py` | 15种主策略＋2种对照，整数股、现金、持仓、双边费用和周账户记录 |
| `prepare_comparison.py`、`source/` | 正式150树独立Ranker的预测回放及已有模型 |
| `replay_old50.py`、`old_source/` | 历史50树对照；脚本会重新训练，不是正式主版本 |
| `ensemble_extension/complete_ensemble.py` | 三个子模型及集成的预测回放、Common210/Native366回测 |
| `evaluate_comparison.py`、`ensemble_extension/evaluate_extension.py` | 从回测产物计算和汇总指标 |
| `verify_integer.py`、`ensemble_extension/verify_extension.py` | 合成用例及历史运行产物的核验；具有计算行为 |
| `run_all.py` | 上述模块及图表、报告的执行顺序；会重训旧50树对照，不是只读命令 |
| `inputs/`、`prepared/`、`results/`、`ensemble_extension/runs/` | 冻结输入、回放预测及历史结果；其中部分结果是后续评估脚本的实际输入，不能全部删除 |
| `plot_results.R`、`ensemble_extension/plot_extension.R`、报告生成脚本、`report_app/` | 图表、报告、页面及构建源码，属于展示层 |

源包的 `source/` 15个文件与 `../../external_validation/standalone_ranker/` 对应文件完全一致；`ensemble_extension/source/` 80个文件与 `../../external_validation/ensemble_ranker/` 对应文件完全一致。保留本地副本是为了原路径和清单完整，不表示引入新的模型版本。

新包“六模型”指独立150、历史独立50、三个集成子模型及其组合。正式独立版仍然是用户确认的 model_only 150树；50树只作为历史对照。Common210与Native366是不同的评价日期范围，不能混为一张同样本排名。

## 已读代码确认的规则

- **Top5_NoLoss13w**：根据过去13周首尾累计价格收益不低于0，先过滤整个候选池，再按模型排名取前5只。不是要求每周都盈利；也不是先选5只再剔除且不补位。可选股票不足5只时每只仍按五分之一预算，余款留现金。
- 历史价格通过 `sell_price` 错后一行构造信号时已知的收盘代理。其正确性依赖输入约定“本行卖价对应下一周”；本次没有原始日行情核验这一来源。
- 每次按开盘账户价值分配预算，先卖后买，预留买入费用并将股数向下取整。未花完的钱留现金，买卖双方均计费。2/4周调仓策略在非调仓周保持股数。
- 期末清仓计卖费；只有 `Top5_WeeklyRoundTrip` 对照每周全清仓。`LowVol26w` 在有26周波动率记录的候选股中按模型排名取前5只，再按波动率倒数加权，单股权重上限35%；不是全池选最低波动5只。
- 收益为周净值的复利年化，波动按周收益的样本标准差年化，Sharpe使用零无风险收益。最大回撤包括初始资金，基于周收盘账户价值，CSV以负数表示；不等同于日内或每日最大回撤。

以上是源码阅读结论，不是本轮实际回测验收。

## 以后运行前需要处理

1. **缓存输入不完整**：`ensemble_extension/complete_ensemble.py` 第69—72行只用引擎及当期预测文件指纹判断复用，但主引擎还依赖完整前序价格历史。改变此前的价格后必须使缓存失效；建议补完整价格文件指纹。
2. **核验结果可能沿用**：`ensemble_extension/verify_extension.py` 第91—92行可因旧 verification 存在且旧状态为 verified 而跳过。换输入、代码、核验器或结果后，应重新验证，不把旧 passed 当成新的验证。
3. **环境需对齐**：根依赖固定 pandas 3.0.6，嵌套 `ensemble_extension/source/requirements.txt` 固定2.2.3，且后者才列出scikit-learn/scipy。需要确定覆盖所有入口的实际环境；当前没有安装或运行验证，不能宣称依赖已统一。R绘图使用macOS Quartz，跨平台需适配。
4. **检查脚本也可能计算**：原 `check_package.py` 会导入计算库并调用合成回测。静态检查请使用整合工程根目录 `check_project.py`，本次没有执行原包检查脚本。

本次只整理文件，上述运行逻辑保持原样。源包中的“验证通过”均为交付时保存的历史记录；本次确认的是文件完整、版本一致及静态语法可读，不是重新确认历史收益。
