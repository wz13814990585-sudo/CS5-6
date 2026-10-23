# 独立五因子 Ranker 整合说明

正式版本为 `XGBRanker_5factor_66train_40external_model_only.zip`：15 个原始文件原样保留，包括 `README.md`、两个 Python 脚本、9 个滚动模型、配置、模型清单和已保存预测。冻结参数以 `models/configuration.json` 和 `export_saved_models.py` 为准：`max_depth=2`、`min_child_weight=5`、`n_estimators=150`。

`XGBRanker_5factor_66train_40external_handoff.zip` 仅补充 `inputs/train66.csv`、`inputs/test40_with_prices.csv`、原始选参脚本 `run_external40_simulation.py`。其原 README 保持内容不变，改名为 `README_selection_source.md`。该脚本属于原始选参来源，不是另一套正式独立模型；候选搜索和来源说明不能替代 model_only 的冻结参数。

## 入口及副作用（仅静态说明，本次未运行）

- `run_saved_model_simulation.py` 的 `main()` 会读取保存模型、重新预测，然后无条件调用 `simulate()`，写出预测、Top5 净值及交易流水；没有仅预测开关。原 README 中“可进一步运行”的描述不能当作当前入口可选择跳过模拟的依据。
- `export_saved_models.py` 会按冻结参数重新训练并保存模型，还会写配置与清单；默认输出到当前工作目录下的 `models/`，可能覆盖同名已有模型。
- `run_external40_simulation.py` 会重新进行 Development 候选搜索、训练、外部预测、指标计算和 Top5 模拟；它以脚本所在目录为根读取 `inputs/`，并写入同根 `outputs/`。仅归档为选参来源，本次没有调用。

正式脚本的 `--train-file` / `--test-file` 为必填参数；`models/`、`outputs/` 默认值基于当前工作目录。本次未修改路径或算法，handoff 脚本与 `inputs/` 位于同层，原相对路径得以保留。

静态依赖为 Python、NumPy、pandas、XGBoost；这两个独立版源包没有锁定依赖版本的 requirements 文件。本次没有安装或导入这些第三方依赖，也未检查当前机器能否执行。新增文档以外的 19 个来源文件均按 ZIP 原字节保留。
