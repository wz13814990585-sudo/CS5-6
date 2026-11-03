# 所选外部策略账户引擎

[English](README.md) | **中文**

<a id="readme-zh"></a>

`external40/integer_backtest.py` 为冻结 Ensemble 回放提供组合准备、整数股交易执行和绩效计算。在项目根目录运行 `python safecapital.py` 即可执行所选策略。

`pipeline/trading.py:independent_case` 根据内存中的交易与持仓独立重建选股和账户过程。已删除的独立模型对比、恢复辅助流程以及 V1 外部回测，在当前交付中均无运行入口。

13 周过滤、Top5 配置和保留输出见根目录 README。原始四模型研究使用另一套引擎，位于 `research/06_evaluation_backtest/`。
