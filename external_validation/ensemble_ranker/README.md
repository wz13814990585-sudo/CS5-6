# Selected historical Ensemble models

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

The root entry point loads the 45 unchanged model JSON files from `saved_models/`, organised as three components times fifteen historical update dates. No call to model fitting is made. The external backtest exposes only Common210 FullHistory `Top5_NoLoss13w`. The saved model hashes are checked against `saved_models_manifest.json`, whose hashes were checked against the original handoff archive manifest during packaging.

`inputs/test40.csv` is the unchanged original external input. Its factor columns are used for historical inference. `predictions/stock_rankings.csv` provides the reference calendar and expected scores for exact replay validation. Future-return labels are excluded from model input.

`model_configuration.json` records component features, parameters and the equal-weight percentile formula. The manifest also preserves original training-window dates and label-observability metadata; inference does not require rerunning training.

Run from the project root with `python safecapital.py`. The selected models cover 2019-08-30 through 2026-08-28 and must be used only within their recorded historical intervals. They are not a live market-data service.

The `code/ranker_core.py` file supports the Ensemble Training Demonstration (V1). It is explicitly selected by `--retrain-v1`, uses the supplied corrected weekly training data and produces fitted component files only. It does not run an external backtest.

The original model training functions and original 66-stock data are also supplied under `training_reference/` and `inputs/train66.csv`. The optional original training wrapper can be inspected in `training_reference/train_models.py`; the documented V1 demonstration is in `docs/V1_RETRAINING.md` from the project root. Experimental models are saved to a new run folder; default inference continues to load the same delivered files from `saved_models/`. This freezes inference artifacts for reproducibility and does not claim that refitting is invariant across environments.

---

<a id="readme-zh"></a>

## 中文

根目录入口从 `saved_models/` 加载 45 个未改变的模型 JSON 文件，结构为 3 个组件 × 15 个历史更新日期，不调用模型拟合。外部回测仅提供 Common210 FullHistory 上的 `Top5_NoLoss13w`。保存模型的哈希与 `saved_models_manifest.json` 核对；打包时，该清单的哈希已与原始交付压缩包清单核验。

`inputs/test40.csv` 是未修改的原始外部输入，其因子列用于历史推断。`predictions/stock_rankings.csv` 提供参考日历和预期分数，用于精确回放校验。未来收益标签不进入模型输入。

`model_configuration.json` 记录组件特征、参数及等权百分位组合公式。清单还保留原始训练窗口日期和标签可观测性元数据；推断不需要重新训练。

在项目根目录运行 `python safecapital.py`。这些模型覆盖 2019-08-30 至 2026-08-28，只应在各自记录的历史生效区间内使用，不是实时行情服务。

`code/ranker_core.py` 支持 Ensemble 训练演示（V1），需通过 `--retrain-v1` 显式选择。它使用提供的修正后周度训练数据，仅输出拟合后的组件模型文件，不执行外部回测。

原始模型训练函数和原始 66 股数据也保存在 `training_reference/` 与 `inputs/train66.csv`。可选原始训练封装入口为 `training_reference/train_models.py`；正式 V1 演示说明位于项目根目录下的 `docs/V1_RETRAINING.md`。实验模型写入新的运行目录，默认推断仍读取 `saved_models/` 中同一批交付文件。这是通过冻结推断产物来保证复现，并不表示跨环境重新拟合的结果必然相同。
