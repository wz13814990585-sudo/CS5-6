/** UI copy only. API field names, original downloads and data values stay stable. */
export const english: Record<string, string> = {
  "可关注股票清单 JSON": "Supported stocks JSON",
  关注股票: "Watchlist",
  组合表现: "Performance",
  "从关注的股票出发，查看真实输入、模型排名与历史策略结果。":
    "Start with stocks you follow. Inspect real inputs, model rankings and historical strategy results.",
  原策略完整组合表现: "Original strategy · full portfolio",
  "以下指标覆盖原策略完整回测，不是关注股票组成的新组合收益。":
    "These metrics cover the original strategy’s full backtest. They are not the returns of a new watchlist portfolio.",
  该日期无对齐数据: "No aligned data for this date",
  "完整源文件使用独立日期浏览；不会更改统一研究日期。":
    "Full source files use an independent date filter; the shared research date stays unchanged.",
  "此处与统一历史信号日期同步；切换日期会同步关注、排名和配置。":
    "This date is shared with your watchlist, rankings and strategy allocation.",
  回测区间外: "Outside backtest period",
  已入选策略: "Selected",
  未入选策略: "Not selected",
  暂无法判断: "Unavailable",
  该日期无配置: "No allocation data",
  "已关注 {ticker}": "Following {ticker}",
  "已移除 {ticker}": "Removed {ticker}",
  "示例已载入：对照排名与策略入选情况。":
    "Example loaded. Compare model rank with strategy selection.",
  "已重置关注列表、日期和图表筛选。":
    "Watchlist, date and chart filters reset.",
  从你关注的股票开始: "Start with stocks you follow",
  "选择股票，查看同一历史日期的输入、模型排名与策略配置。":
    "Choose stocks to inspect inputs, model rankings and allocations on the same historical date.",
  重置演示: "Reset demo",
  载入演示示例: "Load demo example",
  研究查看流程: "Research walkthrough",
  选择关注股票: "Choose stocks",
  查看输入与排名: "Inspect inputs & rankings",
  查看原策略表现: "View original performance",
  添加关注股票: "Add stocks to follow",
  "搜索代码或公司名称，例如 SCL、Chipotle":
    "Search ticker or company, e.g. SCL, Chipotle",
  可关注的研究股票: "Supported research stocks",
  "不在当前支持的股票列表中。请从研究股票池中选择，不会为未支持的股票生成结果。":
    "No supported stock matches. Choose from the research universe; no results are generated for unsupported stocks.",
  "找到 {count} 只股票；继续输入可缩小范围。":
    "{count} stocks found. Keep typing to narrow the list.",
  "仅查看本模块的 {count} 只外部评估股票；与客户网站的全局资产选择器独立。":
    "Browse this module’s {count} external evaluation stocks, independently of the host site’s global asset selector.",
  统一历史信号日期: "Shared historical signal date",
  前一个研究周: "Previous research week",
  后一个研究周: "Next research week",
  "同步关注结果、持仓、排名和对齐输入。":
    "Syncs watchlist results, holdings, rankings and aligned inputs.",
  "正在读取可关注的股票…": "Loading supported stocks…",
  "已关注 {count} 只": "Following {count} stocks",
  "移除 {ticker}": "Remove {ticker}",
  清空关注: "Clear watchlist",
  "关注列表只改变查看范围，不重新计算组合。下方收益始终属于原策略完整组合。":
    "Your watchlist changes what you inspect, without recalculating the portfolio. Returns below always describe the original strategy’s full portfolio.",
  先选一只你想了解的股票: "Choose a stock to explore",
  "或载入 SCL、TJX、CMG 示例，看看排名和实际入选有何不同。":
    "Or load SCL, TJX and CMG to see how model rank differs from actual strategy selection.",
  用真实示例开始: "Start with a real example",
  我的关注结果: "Your watchlist results",
  历史研究结果: "Historical research results",
  "导出当前 CSV": "Export current CSV",
  "导出 JSON": "Export JSON",
  "正在按同一日期关联输入、排名和配置…":
    "Matching inputs, rankings and allocations by date…",
  关注股票研究结果: "Watchlist research results",
  策略入选状态: "Strategy selection",
  操作: "Action",
  "查看 {ticker} 详情": "View {ticker} details",
  查看详情: "View details",
  "得分是当周的相对排名参考，不是预计收益。未入选与没有配置记录是两种不同状态。":
    "Scores express relative weekly rankings, not expected returns. Not selected and no allocation data are different states.",
  关注股票详情: "Stock research details",
  "输入：五个原始因子": "Inputs · five raw factors",
  "匹配的输入文件暂不可用。": "Matching input files are unavailable.",
  "该股票在此日期没有对齐的因子记录。":
    "No aligned factor record exists for this stock on this date.",
  "因子以原始数值展示；模型使用同周股票百分位转换后的输入。":
    "Factors are shown as raw values; model inputs use within-week stock percentile transforms.",
  "输出：模型评价": "Outputs · model assessment",
  当周模型排名: "Weekly model rank",
  "模型组件 {n} 百分位": "Component {n} percentile",
  "该股票在此日期没有保存的模型排名。":
    "No saved model ranking exists for this stock on this date.",
  "结果：策略配置": "Result · strategy allocation",
  "这只股票没有进入当周保存的策略配置。排名靠前不保证入选。":
    "This stock is absent from the saved weekly allocation. A high rank does not guarantee selection.",
  "缺少此日期的已验证配置，不能判断是否入选。":
    "A verified allocation is unavailable for this date; selection cannot be determined.",
  "保存结果没有逐股过滤原因，因此不推断具体未入选理由。":
    "The saved results contain no per-stock rejection reasons, so no specific reason is inferred.",
  "权重为下一周开盘代理价调仓后的历史配置，包含整数股与现金约束。":
    "Weights reflect historical rebalancing at next-week open proxies, with integer-share and cash constraints.",
  "最后持有期结束时已清仓，展示的历史配置不代表当前持仓。":
    "Positions were liquidated at the end of the final holding period. These historical allocations are not current holdings.",
  查看回测价格与数据来源: "Backtest prices & provenance",
  "价格是下一周开盘和收盘的历史回测代理价，不是当前行情或未来价格预测。":
    "Prices are next-week open and close proxies used in the historical backtest, not live quotes or future price forecasts.",
  "该日期的对齐回测价格不可用。":
    "Aligned backtest prices are unavailable for this date.",
  "金额沿用原研究账户单位，币种未声明。":
    "Amounts retain the original research account units; currency is unspecified.",
  "查看当前关注接口 JSON": "View current watchlist API JSON",
  "请求超时，请检查本地服务后重试。":
    "Request timed out. Check the local service and retry.",
  "无法连接研究服务，请检查服务是否正在运行。":
    "Unable to connect. Check that the research service is running.",
  "服务返回了无法读取的数据，请重试。":
    "The service returned unreadable data. Please retry.",
  "未找到对应的结果，请重新选择。":
    "Result not found. Please select another run.",
  "无法读取结果，请确认 Dashboard 服务正在运行。":
    "Unable to load results. Check that the Dashboard service is running.",
  重试: "Retry",
  "没有可用的已验证结果。请先运行默认流程，再重启 Dashboard 服务。":
    "No verified results available. Run the default workflow, then restart the Dashboard service.",
  "SafeCapital 历史策略研究": "SafeCapital historical strategy research",
  "浏览器不允许复制，请选中下面的代码手动复制。":
    "Clipboard access is unavailable. Select and copy the code below manually.",
  关闭导航遮罩: "Close navigation",
  工作空间: "WORKSPACE",
  主导航: "Main navigation",
  策略总览: "Overview",
  输入数据: "Input data",
  股票排名: "Stock rankings",
  验证与下载: "Verification & files",
  输入输出接口: "Input & output APIs",
  "每个结果，都有依据": "Evidence behind every result",
  "读取真实回放记录，展示已通过校验的历史策略结果。":
    "Explore historical strategy results from verified replay records.",
  只读研究模式: "Read-only research",
  打开导航: "Open navigation",
  研究工作台: "Research workspace",
  历史策略: "Historical strategy",
  历史结果: "Historical results",
  "让策略表现，一目了然": "Strategy performance, clearly",
  "查看真实输入因子与价格，对照模型排名和组合历史表现。":
    "Explore real factors and prices alongside model rankings and portfolio history.",
  "历史回测 · 非实时行情": "Historical backtest · Not live market data",
  结果版本: "Result version",
  文件哈希校验通过: "File hashes verified",
  "正在读取已验证的运行结果…": "Loading verified run results…",
  期末账户资金: "Final account value",
  "初始资金 {value}": "Initial capital {value}",
  累计收益: "Total return",
  "年化收益 {value}": "Annualized return {value}",
  最大回撤: "Maximum drawdown",
  "完整回测区间 · 峰值至谷值": "Full backtest · Peak to trough",
  夏普比率: "Sharpe ratio",
  "覆盖 {count} 个信号周": "Across {count} signal weeks",
  回测图表: "Backtest chart",
  看见资金的每一步: "Follow the portfolio over time",
  图表区间: "Chart period",
  "末 52 周": "Last 52 weeks",
  "末 156 周": "Last 156 weeks",
  全部: "All history",
  图表指标: "Chart metric",
  账户资金: "Account value",
  每周收益: "Weekly return",
  历史回撤: "Drawdown",
  "{metric}曲线；完整数值可下载每周资金 CSV":
    "{metric} chart. Download the weekly account CSV for all values.",
  每周净收益率: "Weekly net return",
  相对历史峰值的回撤: "Drawdown from the historical peak",
  期末资金: "Closing account value",
  当周净收益: "Weekly net return",
  "信号日期 {date}": "Signal date {date}",
  "横轴为信号日期；资金为对应持有期末值。顶部指标始终对应完整回测区间。":
    "The x-axis shows signal dates; account values are measured at the end of each holding period. Headline metrics always cover the full backtest.",
  三个模型组件: "Three model components.",
  "一个组合策略。": "One portfolio strategy.",
  "按周综合模型排名，以过去 13 周非负收益筛选，最多选择 5 只股票。":
    "Combine weekly model rankings, filter for non-negative returns over the prior 13 weeks, and select up to five stocks.",
  组合方式: "Ensemble method",
  三组件等权: "Three equal-weight components",
  模型快照: "Model snapshots",
  "{count} 个": "{count}",
  单只目标权重: "Target weight per stock",
  交易成本: "Transaction cost",
  "单边 {cost} bps": "{cost} bps per side",
  调仓频率: "Rebalancing",
  每周: "Weekly",
  查看结果依据: "View result evidence",
  每周股票排名: "Weekly stock rankings",
  "{count} 只股票池": "{count}-stock universe",
  下载全部排名: "Download all rankings",
  信号日期: "Signal date",
  上一个信号周: "Previous signal week",
  下一个信号周: "Next signal week",
  搜索股票代码: "Search stock ticker",
  "搜索股票代码，例如 ANF": "Search ticker, e.g. ANF",
  清空搜索: "Clear search",
  排名: "Rank",
  股票代码: "Ticker",
  集成得分: "Ensemble score",
  "三个组件的周内百分位得分的等权平均；不是收益预测":
    "Equal-weight mean of three within-week percentile scores; not a return forecast",
  "组件 1 百分位": "Component 1 percentile",
  "组件 2 百分位": "Component 2 percentile",
  "组件 3 百分位": "Component 3 percentile",
  "正在读取排名…": "Loading rankings…",
  "没有匹配的股票，试试其他代码。": "No matching stocks. Try another ticker.",
  "共 {count} 条匹配结果 · 每页 10 条":
    "{count} matching results · 10 per page",
  正在加载: "Loading…",
  "· 分数越高，模型排序越靠前":
    "· Higher scores indicate a higher model ranking",
  上一页: "Previous page",
  下一页: "Next page",
  "真实运行，可追溯": "Real runs. Traceable results.",
  校验通过: "Verified",
  "股票 × 周预测记录": "Stock-week predictions",
  预测信号周: "Prediction weeks",
  组合回测周: "Portfolio backtest weeks",
  运行完成时间: "Run completed",
  "{time}（本地时间）": "{time} (local time)",
  预测覆盖: "Prediction coverage",
  回测覆盖: "Backtest coverage",
  结果编号: "Run ID",
  "另有 {count} 份不完整或未通过校验的记录，未用于展示。":
    "{count} incomplete or unverified runs were excluded from this view.",
  把研究结果带走: "Take the research with you",
  "下载当前版本的原始文件，继续分析或核对。":
    "Download original files for this run to analyze or verify the results.",
  回测汇总: "Backtest summary",
  "收益、风险与交易成本": "Return, risk and transaction costs",
  每周资金: "Weekly account values",
  "210 周账户变化与净收益": "210 weeks of account values and net returns",
  运行校验清单: "Run verification manifest",
  运行状态与原始文件哈希: "Run status and original file hashes",
  "{count} 周账户变化与净收益":
    "{count} weeks of account values and net returns",
  "输入与输出，都有查询接口": "Query inputs and outputs via API",
  "直接读取现有输入和已验证结果，也可以嵌入完整 Dashboard。":
    "Query existing inputs and verified results, or embed the complete Dashboard.",
  "输入清单 JSON": "Input catalog JSON",
  当前日期输出排名: "Rankings for selected date",
  "输出汇总 JSON": "Output summary JSON",
  "完整 API 文档": "Full API documentation",
  预览嵌入模式: "Preview embedded mode",
  查看网站嵌入示例: "View website embedding example",
  "正式接入时，将地址换成部署域名，并在服务端允许客户域名。未配置公开域名时，代码中的本机地址仅供当前设备预览。":
    "For integration, use the deployed URL and allow the client site's origin on the server. Until a public URL is configured, localhost links only work on this device.",
  已复制: "Copied",
  复制代码: "Copy code",
  "历史研究结果不代表未来收益。价格为回测代理值，排名不等同于投资建议。":
    "Historical research does not guarantee future returns. Prices are backtest proxies; rankings are not investment advice.",
  暂时无法读取输入数据: "Unable to load input data right now.",
  请选中地址手动复制: "Select and copy the URL manually.",
  "从输入，看懂输出": "Understand results through inputs",
  "查看当前运行所对应的现有输入；选择一只股票，即可对照它的输出排名。":
    "Explore inputs linked to this run. Select a stock to compare it with its output ranking.",
  "现有数据 · 只读查询": "Existing data · Read-only",
  重新读取: "Reload",
  "正在验证输入与本次结果的对应关系…": "Checking that inputs match this run…",
  "5 个因子 + 历史回测价格": "5 factors + historical backtest prices",
  "{count} 个模型组件": "{count} model components",
  "{count} 个已保存快照": "{count} saved snapshots",
  排名与回测: "Rankings & backtest",
  按日期和股票代码关联: "Linked by date and ticker",
  "下载完整输入 CSV": "Download full input CSV",
  "源文件记录 · {count} 个信号周": "Source records · {count} signal weeks",
  与本次预测输出对齐的记录: "Records aligned with this prediction",
  与本次回测输出对齐的记录: "Records aligned with this backtest",
  "{count} 只": "{count} stocks",
  源文件股票池: "Source stock universe",
  输入与运行记录哈希一致: "Input hashes match this run",
  "源文件范围：{start} — {end}。表格显示 6 位小数；接口返回数值，下载保留原始文件。可左右滚动查看全部字段。":
    "Source range: {start} — {end}. Tables show 6 decimal places; the API returns numeric values and downloads preserve original files. Scroll horizontally to see all fields.",
  查看范围: "Scope",
  与本次输出对齐: "Aligned with this output",
  完整源文件: "Full source file",
  输入日期: "Input date",
  搜索输入股票代码: "Search input ticker",
  输入数据表: "Input data table",
  对应输出: "Linked output",
  "正在读取输入…": "Loading inputs…",
  "这个日期没有匹配的股票。": "No matching stocks for this date.",
  查看输出: "View output",
  不在预测区间: "Outside prediction period",
  "共 {count} 条匹配输入 · 每页 10 条": "{count} matching inputs · 10 per page",
  读取中: "Loading…",
  输入上一页: "Previous input page",
  输入下一页: "Next input page",
  当前输入查询接口: "Current input query URL",
  复制地址: "Copy URL",
  "打开 JSON": "Open JSON",
  "仅查询现有数据。完整 CSV 还包含研究标签等列；表格查询只返回上面列出的字段，target1 / target2 不参与预测或选股。":
    "Queries read existing data. Full CSV files include research labels and other columns; table queries return only the fields above. target1 / target2 are not used for prediction or stock selection.",
  接口地址已复制: "API URL copied",
  字段说明与文件校验: "Field details & file verification",
  "原文件 SHA-256：": "Original file SHA-256: ",
  随项目交付的验证结果: "Verified results included with the project",
  本地历史回放: "Local historical replay",
  "策略过滤前的模型排名，不是实际持仓或买卖指令。":
    "Model rankings before strategy filtering; not actual holdings or trading instructions.",
  模型因子输入: "Model factor inputs",
  回测价格输入: "Backtest price inputs",
  "原始因子按同周股票转换为百分位后输入模型；研究标签不参与预测。":
    "Raw factors are converted to within-week stock percentiles before entering the model. Research labels are not used for prediction.",
  "下一周开盘/收盘代理价用于历史模拟；更早日期也可能用于 13 周过滤回看。":
    "Next-week open/close price proxies are used for historical simulation. Earlier dates may also support the 13-week lookback filter.",
  公司名称: "Company name",
  营收同比增长: "Revenue growth YoY",
  经营盈利能力: "Operating profitability",
  "现金流 / 资产": "Cash flow / assets",
  "负债 / 资产": "Debt / assets",
  资产同比增长: "Asset growth YoY",
  下一周开盘代理价: "Next-week open proxy",
  下一周收盘代理价: "Next-week close proxy",
  "缺少与本次运行一致的输入文件，或输入校验未通过；输出仍可独立查看。":
    "Matching input files are missing or failed verification. Verified outputs are still available.",
  请求参数不符合接口约定: "Request parameters do not match the API contract.",
  "服务暂时不可用，请提供请求编号联系维护人员":
    "Service temporarily unavailable. Contact the maintainer with the request ID.",
  "没有可用的已验证结果，请运行默认流程后重启 Dashboard":
    "No verified results available. Run the default workflow and restart the Dashboard.",
  未找到校验通过的回放结果: "No matching verified replay found.",
  "该日期没有预测记录，请选择可用信号日期":
    "No predictions for this date. Select an available signal date.",
  "语言 / Language": "Language / 语言",
  "SafeCapital · 策略研究工作台": "SafeCapital · Strategy Research Workspace",
  "SafeCapital 历史策略研究：真实模型排名、资金曲线与验证记录。":
    "SafeCapital historical strategy research: real model rankings, account curves and verification records.",
  历史模拟: "Historical simulation",
  模型股票策略: "Model-Based Stock Strategies",
  股票与权重: "Stocks & weights",
  基于模型的: "Model-Based",
  股票策略: "Stock Strategies",
  "探索模型选出的股票组合，查看其历史表现与风险。":
    "Explore model-selected stock portfolios and inspect their historical performance and risk.",
  年化收益: "Annualized return",
  "完整区间 · 每年 52 周": "Full history · 52 weeks per year",
  "初始研究资金 {value}": "Initial research capital {value}",
  "历史模拟 · 独立股票池": "Historical simulation · Independent universe",
  策略选中的股票: "Stocks selected by the strategy",
  "查看历史信号对应的配置，区分目标权重与模拟成交后的实际权重。":
    "Explore historical allocations. Compare target weights with simulated weights after execution.",
  "暂时无法读取组合配置；其余研究结果仍可查看。":
    "Allocation data is unavailable. Other research results remain accessible.",
  "正在读取已验证的组合配置…": "Loading verified portfolio allocations…",
  历史股票配置表: "Historical stock allocation",
  模型排名: "Model rank",
  目标权重: "Target weight",
  实际权重: "Actual weight",
  股数: "Shares",
  查看排名: "View ranking",
  "本周未选中股票，组合持有现金。":
    "No stocks selected this week. The portfolio holds cash.",
  现金权重: "Cash weight",
  "配置时点：下一周开盘代理价成交后":
    "Allocation: after execution at next-week open proxies",
  "此表为最后持有期内的配置；回测结束时已清仓，不代表当前持仓。":
    "This shows the final holding-period allocation. Positions were liquidated at the end of the backtest; these are not current holdings.",
  "该日期没有组合回测记录。": "No portfolio backtest records for this date.",
  "匹配的组合配置暂不可用，未用模型前五名替代。":
    "Matching allocations are unavailable. Raw top-five model rankings are not substituted.",
  一个明确的研究范围: "A clearly defined research scope",
  训练股票池: "Training universe",
  独立外部评估股票: "Separate external stocks",
  当前信号可用股票: "Available on this signal date",
  信号频率: "Signal frequency",
  "仅股票，不包含 ETF；与客户页面的单一资产选择器独立。":
    "Equities only, no ETFs. Independent of the client page’s single-asset selector.",
  基准比较: "Benchmark comparison",
  不可用: "Unavailable",
  "未提供与本股票池、区间和交易假设一致的已验证基准序列。":
    "No verified benchmark series matching this universe, period and execution assumptions is supplied.",
  "与报告中的较短最终测试区间分开呈现。":
    "Presented separately from the report’s shorter final-test period.",
  "方法、假设与数据关系": "Methodology, assumptions & data relationships",
  模型与执行: "Model & execution",
  "三个冻结模型组件按周形成排名；使用可观察的过去 13 周非负收益过滤，再选择最多五只股票。":
    "Three frozen model components rank stocks weekly. An observable trailing 13-week non-negative return filter is applied before selecting up to five stocks.",
  "目标权重每只 20%；整数股、交易费用及现金约束会使实际权重略有差异。":
    "Target weight is 20% per stock. Integer shares, fees and cash constraints can change actual weights.",
  "使用下一周开盘与收盘代理价进行历史模拟，每次买入或卖出收取 10 bps；不表示真实成交。":
    "Historical simulation uses next-week open and close proxies with 10 bps per buy or sell. These are not actual market fills.",
  "年化约定：每年 52 周，(期末资金 / 初始资金)^(52 / 周数) − 1。":
    "Annualization: 52 weeks per year, (final capital / initial capital)^(52 / weeks) − 1.",
  数据边界与来源: "Data boundaries & provenance",
  "完整训练股票池有 66 只，早期快照实际可用股票数随历史数据覆盖而变化；外部 40 只股票与训练股票不重叠。":
    "The full training universe contains 66 stocks; availability in earlier snapshots varies with historical coverage. The 40 external stocks do not overlap with training stocks.",
  "原结果未声明币种，金额沿用研究账户单位。财务数据的独立发布时间戳不可用，信号日期不等于发布时间。":
    "The source does not declare a currency; amounts retain research account units. Independent financial publication timestamps are unavailable. Signal dates are not publication timestamps.",
  "独立命名空间内的关系：模型 → 运行 → 周度信号 → 股票配置 → 回测指标。不会合并客户其他模块的本体或结果。":
    "Relationships within this module: model → run → weekly signal → stock allocation → backtest metrics. The client’s other module ontologies and results remain separate.",
  "配置从既有回测引擎离线导出，与原资金序列逐周核对；页面不会启动训练或实时预测。":
    "Allocations are exported offline from the existing backtest engine and reconciled against every original weekly account value. The page does not start training or live predictions.",
  原资金序列最大误差: "Maximum original account-series error",
  独立账户核验: "Independent accounting checks",
  "查看模块数据合同 JSON": "View module contract JSON",
};
