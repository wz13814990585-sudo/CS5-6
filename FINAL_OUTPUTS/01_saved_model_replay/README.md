# Saved Ensemble replay

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

This folder is the review copy of the focused external simulation. It retains only the three-component Ensemble `Top5_NoLoss13w` result on Common210 FullHistory.

Run `python safecapital.py` from the project root. The command reloads the 45 frozen model snapshots, verifies every historical prediction, and executes one backtest case. It does not fit a model.

The separate Ranker comparison, other strategy outputs and the final-year annualised-return display are excluded. See `selected_strategies.csv` for the retained value and `02_ensemble_evaluation_backtest_report.md` for scope and limitations.

`verified_replay/` contains a complete passed replay: regenerated per-stock predictions, weekly capital, strategy summary, prediction verification, independent account verification and the run manifest. The prediction table precedes the 13-week filter and is not a holdings list. No individual transaction or holding export is required for this methods-and-results presentation.

---

<a id="readme-zh"></a>

## 中文

本目录是专项外部模拟结果的审阅副本，仅保留三组件 Ensemble 在 Common210 FullHistory 区间上的 `Top5_NoLoss13w` 策略结果。

在项目根目录运行 `python safecapital.py`。程序会重新加载 45 个冻结模型快照，验证每一条历史预测，并执行一个回测案例；不会训练模型。

交付内容不包含独立 Ranker 对比、其他策略输出以及最后一年的年化收益展示。保留指标见 `selected_strategies.csv`，范围与局限见 `02_ensemble_evaluation_backtest_report.md`。

`verified_replay/` 保存一次完整且验证通过的回放，包括重新生成的逐股预测、每周资金、策略汇总、预测验证、独立账户核验和运行清单。预测表位于 13 周过滤之前，不是实际持仓清单。本次方法与结果展示不要求单独导出逐笔交易或持仓文件。
