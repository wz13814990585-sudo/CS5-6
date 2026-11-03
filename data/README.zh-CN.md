# 数据版本与复现边界

[English](README.md) | **中文**

<a id="readme-zh"></a>

**本项目的复现从提供的已处理周度数据开始。原始数据采集和重建不属于本次交付范围。**

| 输入 | 用途 |
|---|---|
| `test_45_factors_weekly.csv` | 原始四模型研究：66 只股票、522 个信号周，2016-09-02 至 2026-08-28 |
| `reproducible/train66_corrected_complete.csv` | Ensemble 训练演示：66 只股票、521 个完整信号周，2016-09-02 至 2026-08-21 |
| `reproducible/train_universe.csv` | 校验训练股票池 |
| `clean_basic_data.csv` | 必需的日度复权收盘价参考，用于核验训练演示中的每个标签，包括缺口相邻周和最后一周的标签 |
| `additional_40/additional_40_five_factors_targets_final.xlsx` | 已处理的外部因子、标签和价格代理值 |
| `external_validation/ensemble_ranker/inputs/test40.csv`（相对项目根目录） | 冻结模型推断使用的原始外部因子 |
| `external_validation/shared_inputs/inputs/test40_with_prices.csv`（相对项目根目录） | 所选策略回放使用的外部价格面板 |

原始 Ensemble 训练输入保存在 `external_validation/ensemble_ranker/inputs/`。原始研究数据和修正后的训练数据是不同版本，互相替换会改变实验。

除上述必需的日度标签核验参考外，其他中间表和 `data_processing/` 源码用于保留方法来源。部分历史输入生成后，采集脚本又做过修订。复现所交付策略结果不依赖重新运行这些脚本，训练演示也不要求或提供原始来源重建。旧 `raw_inputs/` 目录仅保留范围说明。

提供的周度面板中的因子与标签定义了复现输入约定。冻结预测流程不使用未来标签。价格属于报价代理值；财务数据发布时间、历史修订和真实成交仍属于解释上的局限，而不是本次原始数据重建交付内容。
