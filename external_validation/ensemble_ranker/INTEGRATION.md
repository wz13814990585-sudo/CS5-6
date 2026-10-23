# 集成 Ranker 整合说明

来自 `XGBRanker_模型预测评估交接_20261021.zip`，仅去除压缩包内最外层同名目录，80 个来源文件及内部相对结构完整保留，包括 45 个滚动模型、输入、配置、代码、文档和 `outputs/current/` 已有结果。原代码、README、清单及结果内容均未修改；新增本说明不属于原 `package_manifest.json` 的交付清单。

## 入口及副作用（仅静态说明，本次未运行）

- `code/run_pipeline.py` 的 `replay` 会加载保存模型、重新预测并重算全部机器学习评估；`train` 会先重新训练，再预测和评估。两种模式都会写新的输出目录。
- `code/build_evaluation.py` 从保存预测重新计算指标并写新的评估目录。
- `code/verify_evaluation.py` 会重新计算并核对指标，还会刷新指定目录的 `verification.json`；不属于只读的字节校验。
- `code/check_package.py` 按原始清单读取文件并校验 SHA-256；本次未执行任何包内脚本，采用外部标准库文件核对。

代码以 `code/` 上一级为包根目录，`inputs/`、`models/` 与 `outputs/current/` 的默认相对路径均保留。代码中的本地模块及静态引用的现有输入、模型、已有结果齐备；运行环境没有在本次安装或验证。依赖版本原样保留于 `requirements.txt`：NumPy、pandas、SciPy、scikit-learn、XGBoost。原 README 说明的系统 OpenMP 依赖同样未在本次检查。

本次仅整理和静态检查。原包记录的历史运行、模型效果和验证结果作为来源证据保留，不代表本次重跑结论。
