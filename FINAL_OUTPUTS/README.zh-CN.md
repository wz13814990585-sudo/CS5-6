# 最终输出目录

[English](README.md) | **中文**

<a id="readme-zh"></a>

| 目录 | 内容 |
|---|---|
| `01_saved_model_replay/` | 冻结 Ensemble 的 Top5_NoLoss13w、Common210 FullHistory 结果，以及模型、因子与排名审计材料 |
| `01_saved_model_replay/verified_replay/` | 重新生成的预测、每周资金、所选策略汇总以及验证通过的记录 |
| `03_project_report/` | 原始四模型研究章节 |

V1 是训练方法演示，说明位于项目根目录下的 `docs/V1_RETRAINING.md`，不包含外部预测或回测结果。

`FILE_MANIFEST.csv` 记录本目录内文件的字节数和 SHA-256，清单自身除外。策略规则和以已处理周度数据为起点的复现边界，见[根目录 README](../README.zh-CN.md#readme-zh)。
