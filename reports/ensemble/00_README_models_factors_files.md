# Ensemble external-simulation files

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

This directory contains the focused saved-model evidence for the three-component Ensemble. The external simulation exposes only `Top5_NoLoss13w` on Common210 FullHistory.

Retained result files:

- `02_ensemble_evaluation_backtest_report.md`: focused report and interpretation limits.
- `03_selected_strategy_metrics.csv`: the single retained strategy value.
- `45_rolling_models_replay_check.csv`: saved-snapshot replay audit.
- `model_configuration.json`, `factor_definitions.csv`: Ensemble definition.
- `prediction_price_join_audit.json`, `five_factor_value_rank_check.json`, `original_rankic_recomputation.csv`: supporting audits.

Separate Ranker comparisons, other strategy tables, charts and final-year annualised-return presentation were removed from this external deliverable. Original research material remains separate. V1 demonstrates component training only and has no external prediction or backtest outputs. A verified complete replay is retained under FINAL_OUTPUTS/01_saved_model_replay/verified_replay/ from the project root.

---

<a id="readme-zh"></a>

## 中文

本目录保存三组件 Ensemble 的专项已训练模型证据。外部模拟仅提供 Common210 FullHistory 区间上的 `Top5_NoLoss13w`。

保留的结果文件：

- `02_ensemble_evaluation_backtest_report.md`：专项报告与解释局限。
- `03_selected_strategy_metrics.csv`：唯一保留策略的指标。
- `45_rolling_models_replay_check.csv`：保存快照的回放审计。
- `model_configuration.json`、`factor_definitions.csv`：Ensemble 定义。
- `prediction_price_join_audit.json`、`five_factor_value_rank_check.json`、`original_rankic_recomputation.csv`：辅助审计材料。

本外部交付已移除独立 Ranker 对比、其他策略表格和图表，以及最后一年的年化收益展示。原始研究资料单独保留。V1 仅演示组件训练，没有外部预测或回测输出。项目根目录下的 `FINAL_OUTPUTS/01_saved_model_replay/verified_replay/` 保存完整且验证通过的回放。
