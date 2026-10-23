# 外部 40 只股票版：非集成五因子 XGBRanker

## 目的

这是非集成五因子 XGBRanker 的重新整理版，专门与
`XGBRanker_模型预测评估交接_20261021.zip` 的数据结构对齐：

- `train66.csv` 的 66 只股票只用于模型训练和 Development 阶段的超参数选择；
- `test40_with_prices.csv` 的 40 只股票只作为外部测试和投资模拟对象；
- 训练股票与测试股票没有代码重叠；
- 40 只股票的 target、买入价和卖出价不会进入模型拟合或超参数选择。

这版不是三个子模型的等权集成，而是一个独立的五因子 XGBRanker，方便与集成模型进行模型层面的对照。

## 实验配置

- 模型：XGBRanker，`rank:pairwise`；
- 因子：revenue growth、operating profitability、cash flow/assets、debt/assets、asset growth；
- 训练窗口：过去 312 周，即 6 年；
- 更新频率：每 26 周重新训练一次；
- 相关性输入：每周横截面 percentile rank；
- 训练标签：66 只股票内部按当周下一周收益排序为 0--4 五档 relevance label；
- 超参数：12 组 `max_depth × min_child_weight × n_estimators` 组合；
- 选择流程：只用 66 只股票的 Development 滚动预测选择参数，先通过 Mean Rank IC、Rank ICIR 和正 Rank IC 周占比门槛，再按 Top-5 年化超额收益选最优组；
- 外部测试：冻结 Development 选出的参数，在 40 只股票上按历史滚动窗口预测。

如果 Development 没有候选通过门槛，脚本会明确记录并使用 Development Top-5 超额收益最高的候选，以保证包仍可运行；请在报告中把这种情况标为 fallback，而不要称为通过了预设门槛。

## 真实投资模拟规则

- 每个信号周选择预测排名最高的 5 只股票；
- 预算等额分配；
- 使用整数股数，不使用小数股；
- 余额现金保留，不强行满仓；
- `buy_price` 作为下一周首个交易日开盘价代理；
- `sell_price` 作为下一周最后交易日收盘价代理；
- 买入和卖出各扣 10 bps（0.1%）；
- 初始资金 AUD 100,000；
- 输出每周净值、交易明细、总收益、年化收益、手续费和最大回撤。

## 运行

在本目录运行：

```bash
python run_external40_simulation.py
```

脚本会生成：

- `outputs/development_candidate_scores.csv`：12 组候选的 Development 指标和选择结果；
- `outputs/external_test_predictions.csv`：40 只外部股票的滚动预测排名；
- `outputs/external_test_metrics.csv`：外部测试 Rank IC 等指标；
- `outputs/weekly_nav.csv`：每周净值和回撤；
- `outputs/trade_ledger.csv`：整数股数、买卖价、手续费和单笔交易盈亏；
- `outputs/simulation_summary.csv`：完整外部预测期和最后 51 周摘要；
- `outputs/run_manifest.json`：训练股票池、测试股票池、窗口和模拟规则核验信息。

## 与集成模型交接包的区别

集成模型交接包是“三个 XGBRanker 子模型 + 等权集成”，66 只股票训练、40 只股票测试。本包是“单个五因子 XGBRanker”，同样采用 66/40 外部测试划分，但不做三个子模型的集成，也不把 40 只股票用于调参。
