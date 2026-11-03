# Processed external price input

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

`inputs/test40_with_prices.csv` supplies the prices and weekly rows used by the frozen Ensemble strategy replay. The default runner joins it to regenerated predictions by date and ticker.

This directory contains no standalone model fitting or simulation. The Ensemble training demonstration reads only the processed training data under `data/reproducible/`.

---

<a id="readme-zh"></a>

## 中文

`inputs/test40_with_prices.csv` 提供冻结 Ensemble 策略回放使用的价格与周度记录。默认运行器按日期和股票代码，将其与重新生成的预测连接。

本目录不包含独立模型拟合或模拟入口。Ensemble 训练演示仅以 `data/reproducible/` 中的已处理训练数据作为训练面板。
