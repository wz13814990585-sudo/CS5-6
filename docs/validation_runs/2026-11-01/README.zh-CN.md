# 验证证据

[English](README.md) | **中文**

<a id="readme-zh"></a>

这些记录来自 macOS 上使用固定依赖和已纳入版本控制的运行代码进行的真实本地执行。记录中的四条命令全部成功退出。归档 JSON 和控制台日志中的机器专属项目路径前缀已替换为 `<project>/`，哈希与数值保持不变。

- `commands.json`：执行命令、退出码和实际耗时。
- `environment.json`：已安装的受控运行环境和必需的已处理输入。
- `regression.log`：87 项回归测试全部通过，没有跳过项。
- `frozen_replay_manifest.json`、`prediction_verification.json`、`backtest_verification.json`：完整历史回放及独立账户核验结果。
- `training_manifest.json`、`training_data_audit.json`、`training_model_manifest.json`：数据准备、45 个新拟合的组件模型，以及哈希和保存/重新加载一致性验证。
- `frozen_replay.log`、`training_full.log`：命令输出。

生成的 CSV 和新训练模型保存在本地 `runs/validation_20261101_replay/` 与 `runs/validation_20261101_training/`，不纳入 Git；清单中的哈希用于标识这些文件。新训练权重没有替换冻结策略快照。这次历史验证没有修改 `FINAL_OUTPUTS/` 内的原始交付证据。若需要重新独立核验，请使用新的运行 ID 执行相同命令。
