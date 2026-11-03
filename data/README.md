# Supplied data and reproduction boundary

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

**Reproduction in this project starts from the supplied processed weekly data. Raw data acquisition and reconstruction are outside the scope of this delivery.**

| Input | Use |
|---|---|
| `test_45_factors_weekly.csv` | Original four-model research: 66 stocks and 522 signal weeks, 2016-09-02 to 2026-08-28 |
| `reproducible/train66_corrected_complete.csv` | Ensemble training demonstration: 66 stocks and 521 complete signal weeks, 2016-09-02 to 2026-08-21 |
| `reproducible/train_universe.csv` | Training universe validation |
| `clean_basic_data.csv` | Required daily adjusted-close reference for verifying every training-demonstration label, including gap-adjacent and final-week labels |
| `additional_40/additional_40_five_factors_targets_final.xlsx` | Processed external factors, labels and price proxies |
| `external_validation/ensemble_ranker/inputs/test40.csv` (project-relative) | Original external factors used by frozen model inference |
| `external_validation/shared_inputs/inputs/test40_with_prices.csv` (project-relative) | External price panel used by the selected strategy replay |

Original Ensemble training inputs are retained under `external_validation/ensemble_ranker/inputs/`. Original research and corrected training data are separate versions; replacing one with the other changes the experiment.

Apart from the required daily label-verification reference above, other intermediate tables and `data_processing/` source are retained as method provenance. The acquisition scripts were revised after some historical inputs were produced. They are not prerequisites for reproducing the supplied strategy result, and no raw-source rebuild is required or exposed by the training demonstration. The old `raw_inputs/` folder is only a scope note.

Factors and labels in the supplied weekly panels define the reproduction input contract. The frozen prediction path excludes future labels. Prices are quote proxies; financial publication timing, historical revisions and actual trading fills remain interpretation limits rather than raw-reconstruction deliverables.

---

<a id="readme-zh"></a>

## 中文

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
