# 冻结模型

[English](README.md) | **中文**

<a id="readme-zh"></a>

根目录入口从 `saved_models/` 加载 45 个未改变的模型 JSON 文件，结构为 3 个组件 × 15 个历史更新日期，不调用模型拟合。外部回测仅提供 Common210 FullHistory 上的 `Top5_NoLoss13w`。保存模型的哈希与 `saved_models_manifest.json` 核对；打包时，该清单的哈希已与原始交付压缩包清单核验。

`inputs/test40.csv` 是未修改的原始外部输入，其因子列用于历史推断。`predictions/stock_rankings.csv` 提供参考日历和预期分数，用于精确回放校验。未来收益标签不进入模型输入。

`model_configuration.json` 记录组件特征、参数及等权百分位组合公式。清单还保留原始训练窗口日期和标签可观测性元数据；推断不需要重新训练。

在项目根目录运行 `python safecapital.py`。这些模型覆盖 2019-08-30 至 2026-08-28，只应在各自记录的历史生效区间内使用，不是实时行情服务。

`code/ranker_core.py` 支持 Ensemble 训练演示（V1），需通过 `--retrain-v1` 显式选择。它使用提供的修正后周度训练数据，仅输出拟合后的组件模型文件，不执行外部回测。

原始模型训练函数和原始 66 股数据也保存在 `training_reference/` 与 `inputs/train66.csv`。可选原始训练封装入口为 `training_reference/train_models.py`；正式 V1 演示说明位于项目根目录下的 `docs/V1_RETRAINING.md`。实验模型写入新的运行目录，默认推断仍读取 `saved_models/` 中同一批交付文件。这是通过冻结推断产物来保证复现，并不表示跨环境重新拟合的结果必然相同。
