# Historical prediction reference

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

`stock_rankings.csv` contains 13,517 stock-week rows across 366 weeks for the 40 external stocks. It is the unchanged reference from the model handoff, SHA-256 `d8e219d6749031117add13e13d8fbea15abecec87e190a0c72e92ec3d340d007`.

The default root command `python safecapital.py` regenerates scores from the original saved model files and external factor input, then compares them to this reference before backtesting the regenerated scores. It does not fit any models.

The older spelling `python safecapital.py --legacy-ensemble` is now a compatibility alias for the same frozen-model inference workflow. Realised-return and evaluation-label columns are excluded from prediction and trading.

---

<a id="readme-zh"></a>

## 中文

`stock_rankings.csv` 包含 40 只外部股票、366 个周次的 13,517 条股票—周记录。这是未修改的原始模型交付参考，SHA-256 为 `d8e219d6749031117add13e13d8fbea15abecec87e190a0c72e92ec3d340d007`。

根目录默认命令 `python safecapital.py` 使用原始保存模型和外部因子输入重新生成分数，先与本参考精确比较，再对重新生成的分数执行回测。该流程不拟合任何模型。

旧命令 `python safecapital.py --legacy-ensemble` 现在是相同冻结模型推断流程的兼容别名。已实现收益和评估标签列不参与预测或交易。
