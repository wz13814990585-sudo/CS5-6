# Validation evidence: 2026-11-01

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

These records come from actual local runs of the checked-in runtime on macOS with the pinned dependencies. All four recorded commands exited successfully. Machine-specific project prefixes in archived JSON and console logs are replaced with `<project>/`; hashes and numerical values are unchanged.

- `commands.json`: commands, exit codes and measured execution times.
- `environment.json`: installed controlled runtime and required processed inputs.
- `regression.log`: all 87 regression tests passed, with no skips.
- `frozen_replay_manifest.json`, `prediction_verification.json`, `backtest_verification.json`: complete historical replay and independent accounting results.
- `training_manifest.json`, `training_data_audit.json`, `training_model_manifest.json`: preparation, all 45 newly fitted component models and their hashes/save-load verification.
- `frozen_replay.log`, `training_full.log`: command output.

Generated CSVs and newly trained model files remain in the local `runs/validation_20261101_replay/` and `runs/validation_20261101_training/` directories, excluded from Git. The manifest hashes identify them. No new training weights replace the frozen strategy snapshots. Original delivered evidence under `FINAL_OUTPUTS/` is unchanged. Re-run the commands with a new run ID to create a fresh independent check.

---

<a id="readme-zh"></a>

## 中文

这些记录来自 macOS 上使用固定依赖和已纳入版本控制的运行代码进行的真实本地执行。记录中的四条命令全部成功退出。归档 JSON 和控制台日志中的机器专属项目路径前缀已替换为 `<project>/`，哈希与数值保持不变。

- `commands.json`：执行命令、退出码和实际耗时。
- `environment.json`：已安装的受控运行环境和必需的已处理输入。
- `regression.log`：87 项回归测试全部通过，没有跳过项。
- `frozen_replay_manifest.json`、`prediction_verification.json`、`backtest_verification.json`：完整历史回放及独立账户核验结果。
- `training_manifest.json`、`training_data_audit.json`、`training_model_manifest.json`：数据准备、45 个新拟合的组件模型，以及哈希和保存/重新加载一致性验证。
- `frozen_replay.log`、`training_full.log`：命令输出。

生成的 CSV 和新训练模型保存在本地 `runs/validation_20261101_replay/` 与 `runs/validation_20261101_training/`，不纳入 Git；清单中的哈希用于标识这些文件。新训练权重没有替换冻结策略快照。这次历史验证没有修改 `FINAL_OUTPUTS/` 内的原始交付证据。若需要重新独立核验，请使用新的运行 ID 执行相同命令。
