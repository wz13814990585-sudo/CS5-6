# 五因子 XGBRanker：模型和代码交接包

本包只保留代码、配置、已经训练好的模型文件，以及对 40 只外部股票生成的预测结果；不包含训练数据和原始 40 股票输入数据。

## 模型结构

- 模型：独立的五因子 XGBRanker，不是三个子模型的等权集成；
- 训练股票池：66 只股票；
- 外部测试股票池：40 只股票；
- 训练股票与测试股票没有重叠；
- 训练窗口：312 周（6 年）；
- 更新频率：每 26 周重新训练；
- 因子：收入增长、经营盈利能力、现金流/资产、负债/资产、资产增长；
- Development 阶段在 66 只股票上选择参数；
- 固定参数：`max_depth=2`、`min_child_weight=5`、`n_estimators=150`；
- 训练目标：每周横截面 0--4 五档 relevance label。

## 文件说明

- `models/*.json`：9 个已训练的滚动模型，每个模型都只使用 66 只股票历史数据训练；
- `models/model_manifest.csv`：每个模型的重新训练日期和训练历史范围；
- `models/configuration.json`：模型配置；
- `predictions/external_test_predictions.csv`：使用上述模型对 40 只外部股票生成的逐周预测分数和排名；
- `export_saved_models.py`：如果有 66 只股票训练数据，可以重新生成模型文件；
- `run_saved_model_simulation.py`：读取外部 40 只股票数据，生成预测排名，并可进一步运行 Top5 真实交易模拟。

## 使用已保存模型

需要另行准备 40 只股票的输入文件，至少包含：

```text
date, ticker, target1, buy_price, sell_price,
revenue_growth_yoy, operating_profitability,
cashflow_to_assets, debt_to_assets, asset_growth_yoy
```

运行：

```bash
python run_saved_model_simulation.py --test-file path/to/test40_with_prices.csv
```

脚本会使用保存好的模型进行预测，不会用 40 只股票重新训练或调参。若运行模拟，规则为 Top5、等额资金、整数股数、剩余现金保留，买卖双方各 10 bps。

## 重新生成模型

如果需要从 66 只股票重新训练模型：

```bash
python export_saved_models.py --train-file path/to/train66.csv --output-dir models
```

该过程不会读取 40 只股票，也不会使用 40 只股票的标签进行选参。
