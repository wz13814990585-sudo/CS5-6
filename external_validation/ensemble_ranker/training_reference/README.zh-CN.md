# 原始训练参考

[English](README.md) | **中文**

<a id="readme-zh"></a>

`ranker_core.py` 和 `prediction_helpers.py` 是原始模型交付中的未修改文件。它们的源码哈希以及原始 `../inputs/train66.csv` 的哈希记录在 `../saved_models_manifest.json` 中。

`train_models.py` 是打包时提供的封装，调用原始函数，只将新权重写入项目 `runs/` 下的新目录。它会检查 45 个冻结推断文件未发生变化，不部署新输出，也不会让默认预测器使用新训练权重。

在项目根目录运行：

```bash
python external_validation/ensemble_ranker/training_reference/train_models.py --n-jobs 4
```

完整运行拟合 45 个快照；`--profile smoke` 只拟合最新的 3 个。输入因子、训练标签构造、组件超参数、重新拟合间隔和随机种子均由原始代码定义。本实验使用原始数据，与使用修正数据的 V1 流程分开。
