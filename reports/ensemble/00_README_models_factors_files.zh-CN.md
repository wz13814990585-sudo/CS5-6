# 模型、因子与证据

[English](00_README_models_factors_files.md) | **中文**

<a id="readme-zh"></a>

本目录保存三组件 Ensemble 的专项已训练模型证据。外部模拟仅提供 Common210 FullHistory 区间上的 `Top5_NoLoss13w`。

保留的结果文件：

- `02_ensemble_evaluation_backtest_report.md`：专项报告与解释局限。
- `03_selected_strategy_metrics.csv`：唯一保留策略的指标。
- `45_rolling_models_replay_check.csv`：保存快照的回放审计。
- `model_configuration.json`、`factor_definitions.csv`：Ensemble 定义。
- `prediction_price_join_audit.json`、`five_factor_value_rank_check.json`、`original_rankic_recomputation.csv`：辅助审计材料。

本外部交付已移除独立 Ranker 对比、其他策略表格和图表，以及最后一年的年化收益展示。原始研究资料单独保留。V1 仅演示组件训练，没有外部预测或回测输出。项目根目录下的 `FINAL_OUTPUTS/01_saved_model_replay/verified_replay/` 保存完整且验证通过的回放。
