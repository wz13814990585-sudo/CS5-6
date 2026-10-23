# 历史因子组合与模型搜索记录

来源是此前已提供的 `第二版/history_fine/`。本目录用于保留研究过程，**不是当前正式模型的另一个运行入口**，也不替代独立150树或集成模型的配置。

本次按原字节归档：完整 `code/` 下的Python源码、根目录研究说明，以及 `data/feature_search`、`algorithm_optimization`、`rankic_optimization`、`fixed_rolling_comparison` 中的搜索指标、配置和报告。逐股预测大表、旧模型快照、连续标签最终运行、标签比较及早期策略结果未复制；它们仍在原资料目录中。此目录不是旧工程全量备份。

可优先阅读 `data/feature_search/batched_feature_search_report.md`、`data/algorithm_optimization/algorithm_optimization_report.md` 和相应搜索代码，查明研究过哪些组合、参数及窗口。不同历史阶段使用的候选和评价区间不同，报告中“最佳”仅限它当时的研究定义。

代码和记录与当前正式交付的对应关系尚未逐项确认；不能只因某份历史结果更高就自动覆盖正式版本。历史说明中涉及标签和模型配置的修订要按原记录理解，不作为本工程新增指令。本轮未运行这些代码，也未验证这份精简归档可以独立重放整个旧研究工程。

当前确认版66股输入位于工程根目录 `data/test_45_factors_weekly.csv`。若以后复核历史研究，应先核对各历史manifest的数据哈希、标签和阶段边界，再显式适配输入与输出路径。
