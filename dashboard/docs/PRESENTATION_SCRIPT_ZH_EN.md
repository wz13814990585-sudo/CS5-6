# SafeCapital Dashboard 中英文对照演示讲稿

**版本 / Version：** Dashboard 1.4  
**整理日期 / Prepared：** 2026-11-02  
**建议时长 / Suggested duration：** 8–10 分钟，另留问答时间 / 8–10 minutes, plus questions

## 使用方法 / How to use this script

每一步包含操作、预期画面、中英文讲稿和过渡语。演示时选择一种语言照读即可，不需要两种语言都读；操作提示和核对表不用朗读。中英文都讲时，请预留约两倍时间。数值对应随项目交付的历史结果；换成新的研究结果后，应先核对页面再修改讲稿。

Each step contains actions, expected results, a Chinese script, an English script and a transition. Read one language during the presentation. Do not read the operating instructions or reference tables aloud. Allow roughly twice as much time if presenting both languages. The figures refer to the historical results delivered with this project; verify them again if the research results change.

**主线 / Storyline：** 选择股票 → 查看输入 → 解释模型排名和实际配置 → 查看原策略表现 → 导出 → 接入网站。  
Choose stocks → inspect inputs → explain rankings and actual allocations → review original strategy performance → export → demonstrate integration.

## 演示前准备 / Before the presentation

### 启动和打开页面 / Start and open the Dashboard

如果页面已经正常显示，保持现有服务运行即可。否则，在项目目录打开终端：

If the page already works, leave the existing service running. Otherwise, open a terminal in the project directory:

```bash
cd '/Users/april/Desktop/USYD 2026s2/5703/5703前端版本/SafeCapital_ensemble_external'
.venv-dashboard/bin/python dashboard/start.py
```

保持终端运行。提前打开以下页面，主讲时保留 Dashboard，其他页作为备用。

Keep the terminal running. Open these pages beforehand, using the Dashboard as the main presentation tab.

| 页面 / Page | 地址 / Link | 用途 / Purpose |
|---|---|---|
| 中文 Dashboard | [中文演示](http://127.0.0.1:8000/?lang=zh#watchlist) | 中文界面 / Chinese interface |
| English Dashboard | [English demo](http://127.0.0.1:8000/?lang=en#watchlist) | 英文界面 / English interface |
| 网站嵌入示例 / Embedding example | [打开示例](http://127.0.0.1:8000/embed-example.html?lang=en) | 演示外层页面入口 / Demonstrate the host-page entry |
| API 文档 / API documentation | [API docs](http://127.0.0.1:8000/api/docs) | 技术问答备用 / Optional developer walkthrough |
| API 定义 / API definition | [OpenAPI JSON](http://127.0.0.1:8000/api/openapi.json) | 文档界面无法加载时使用 / Fallback if the documentation UI cannot load |

这些地址只在运行服务的电脑上可用；远程会议使用屏幕共享。API 文档界面依赖外部 CDN，演示前确认能打开；Dashboard 的已有数据展示可以离线运行。

These addresses work on the computer running the service. Use screen sharing for a remote presentation. The API documentation UI uses an external CDN, so check it beforehand; the Dashboard can display its existing data offline.

### 恢复演示起点 / Set the starting state

| 操作 / Action | 核对 / Check |
|---|---|
| 选择「中文」或「English」。 / Choose the presentation language. | 按钮语言与准备朗读的讲稿一致。 / The interface matches your chosen script. |
| 保持默认「结果版本 / Result version」。 / Keep the default result version. | 整场演示使用同一份结果。 / Use the same run throughout. |
| 点击「关注股票 / Watchlist」。 / Open Watchlist. | 股票选择区域可见。 / The stock selector is visible. |
| 点击「重置演示 / Reset demo」，再点「载入演示示例 / Load demo example」。 | 关注列表为 SCL、TJX、CMG，日期为 2026-08-28。 / The list contains SCL, TJX and CMG on 2026-08-28. |

正式开场前停留在关注区域。演示过程中若走乱，回到这里点击「载入演示示例」恢复这组三只股票、默认示例日期及图表/输入筛选。

Start with the Watchlist section on screen. If you lose your place, use Load demo example to restore the three stocks, the example date, and the chart/input filters.

## 第 1 步：介绍模块用途 / Step 1: Introduce the module

**建议用时 / Time：45 秒 / 45 seconds**

**怎么操作 / Actions**

1. 停留在「关注股票 / Watchlist」，指向搜索框、日期和已关注的三只股票。 / Stay on Watchlist and point to the search box, date and three selected stocks.
2. 暂时不要切换日期或图表。 / Keep the date and charts unchanged for the introduction.

**中文照读**

> 大家好，今天我会演示我们的 SafeCapital Dashboard。它把项目已有的输入数据、模型排名和历史策略结果放在同一个界面中。
>
> 用户可以先选择自己关注的股票，再查看它们在同一个历史日期的输入、排名，以及是否进入实际策略配置。最后，我会展示结果导出，以及这个模块如何接入客户的网站。
>
> 今天展示的是已经完成并通过校验的历史研究结果。页面中的查询不会重新训练模型或重新运行回测。

**English script**

> Hello everyone. Today I will demonstrate our SafeCapital Dashboard. It brings the project's existing input data, model rankings and historical strategy results into one interface.
>
> Users can start with stocks they follow, then inspect their inputs, rankings and actual strategy selection on the same historical date. I will also demonstrate exports and the options for integrating this module into the client's website.
>
> We are viewing completed, verified historical research results. These queries do not retrain the models or rerun the backtest.

**过渡 / Transition**

> 中文：我们先从用户最直接的操作——选择关注股票——开始。  
> English: Let's start with the user's first action: choosing stocks to follow.

## 第 2 步：展示股票搜索和多选 / Step 2: Search and select stocks

**建议用时 / Time：1 分钟 / 1 minute**

**怎么操作 / Actions**

1. 在「添加关注股票 / Add stocks to follow」输入 `Chipotle`，展示搜索结果 CMG，并点击它。 / Search for `Chipotle`, show the CMG match and select it.
2. 指出 CMG 已在列表中，因此仍为三只股票，没有重复行。 / Point out that CMG is already followed, so the list still contains three stocks.
3. 搜索 `URBN`，点击建议结果；展示列表从三只变成四只。 / Search for `URBN` and select it; show the list growing from three to four stocks.
4. 点击 URBN 标签旁的 ×，回到三只股票。 / Click the × beside URBN to remove it.

**预期画面 / Expected result：** 最终仍为 SCL、TJX、CMG；日期为 2026-08-28。 / The final list is SCL, TJX and CMG, dated 2026-08-28.

**中文照读**

> 用户可以输入股票代码，也可以输入公司名称。例如，搜索 Chipotle 会找到股票代码 CMG。
>
> 这里支持多选、移除和清空关注列表，也会避免重复添加。目前可选择的是本模块已有的 40 只外部评估股票，不是整个市场的所有股票。
>
> 用户的关注偏好决定要查看哪些研究结果，不会改变原研究股票池，也不会自动生成一个新的投资组合。

**English script**

> Users can search by ticker or company name. For example, searching for Chipotle finds the ticker CMG.
>
> They can follow several stocks, remove individual stocks or clear the list. Duplicate selections are avoided. The available choices are the 40 external evaluation stocks in this module, rather than every stock in the market.
>
> The watchlist determines which research results the user inspects. It does not change the original research universe or generate a new investment portfolio.

**过渡 / Transition**

> 中文：接下来，我们看这三只股票的模型排名与实际策略入选情况。  
> English: Next, let's compare the model rankings with actual strategy selection for these three stocks.

## 第 3 步：解释排名与策略入选 / Step 3: Compare ranking and selection

**建议用时 / Time：1 分钟 / 1 minute**

**怎么操作 / Actions**

1. 点击「载入演示示例 / Load demo example」，确保回到标准状态。 / Load the demo example to restore the standard state.
2. 向下滚到「我的关注结果 / Your watchlist results」。 / Scroll to Your watchlist results.
3. 依次指向「模型排名 / Model rank」「策略入选状态 / Strategy selection」和权重列。 / Point to the rank, selection status and weight columns.

**预期画面 / Expected result：2026-08-28**

| 股票 / Ticker | 排名 / Rank | 集成得分 / Ensemble score | 状态 / Selection | 目标权重 / Target | 实际权重 / Actual |
|---|---:|---:|---|---:|---:|
| SCL | 1 | 0.9250 | 已入选 / Selected | 20.00% | 19.95% |
| TJX | 2 | 0.8083 | 未入选 / Not selected | — | — |
| CMG | 3 | 0.7917 | 已入选 / Selected | 20.00% | 19.98% |

**中文照读**

> 在 2026 年 8 月 28 日这个信号日期，SCL、TJX 和 CMG 的模型排名分别是第一、第二和第三。
>
> 但我们可以看到，SCL 和 CMG 入选了当周策略，排名第二的 TJX 没有入选。这说明模型排名与最终策略配置是不同阶段的输出；排名靠前不保证进入实际配置。
>
> 对已经入选的股票，页面展示目标权重和模拟调仓后的实际权重。整数股、费用和现金约束会让实际权重与目标略有差异。这里展示的是历史配置，不是今天的真实持仓。

**English script**

> On the signal date of 28 August 2026, SCL, TJX and CMG rank first, second and third respectively.
>
> However, SCL and CMG appear in the saved strategy allocation, while TJX does not, despite ranking second. Model ranking and final strategy allocation are outputs from different stages. A high rank does not guarantee selection.
>
> For selected stocks, we show target weights and actual weights from the simulated rebalance. Integer shares, costs and cash constraints can cause small differences. These are historical allocations, not current live holdings.

**过渡 / Transition**

> 中文：我们以 TJX 为例，进一步看它的输入、模型输出和策略状态。  
> English: Let's use TJX to look more closely at its inputs, model outputs and strategy status.

## 第 4 步：讲清楚输入与输出 / Step 4: Explain the inputs and outputs

**建议用时 / Time：1 分 30 秒 / 1 minute 30 seconds**

**怎么操作 / Actions**

1. 在 TJX 这一行点击「查看详情 / View details」，向下滚到详情区域。 / Click View details in the TJX row and scroll to the detail section.
2. 从左到右指向「输入：五个原始因子」「输出：模型评价」「结果：策略配置」。手机上这三栏会纵向排列。 / Point to Inputs · five raw factors, Outputs · model assessment, and Result · strategy allocation. These sections stack vertically on a phone.
3. 指出排名 `#2`、集成得分 `0.8083` 和「未入选策略 / Not selected」。 / Highlight rank #2, score 0.8083 and Not selected.

**输入核对表，不必逐项读数 / Input reference; no need to read every value**

| 因子 / Factor | TJX 页面数值 / Displayed value |
|---|---:|
| 营收同比增长 / Revenue growth, year on year | 0.116225 |
| 经营盈利能力 / Operating profitability | 0.329211 |
| 现金流 / 资产 / Cash flow to assets | 0.223447 |
| 负债 / 资产 / Debt to assets | 0.079374 |
| 资产同比增长 / Asset growth, year on year | 0.134974 |

**中文照读**

> 这里有两种不同含义的输入。用户在页面中输入的是查看偏好，也就是股票和日期；模型使用的输入则是项目已有的财务因子。
>
> 左侧展示五个原始因子，涵盖营收增长、盈利能力、现金流、负债和资产增长。模型内部还会按同周股票进行百分位转换。
>
> 中间是模型输出。TJX 当周排名第二，集成得分约为 0.8083。三个组件的百分位是 62.5%、87.5% 和 92.5%。这些反映相对排序，不代表预计收益率，也不是上涨概率。
>
> 右侧显示 TJX 未进入当周保存的策略配置。原结果没有记录逐只股票的排除原因，所以这里不推断它为什么没有入选。

**English script**

> There are two meanings of input here. The user enters viewing preferences: stocks and a date. The model inputs are the financial factors already stored in the project.
>
> On the left, we show five raw factors covering revenue growth, profitability, cash flow, debt and asset growth. The models use within-week percentile transformations of these inputs.
>
> In the middle, TJX ranks second with an ensemble score of approximately 0.8083. The component percentiles are 62.5%, 87.5% and 92.5%. These express relative rankings, not expected returns or probabilities of a price increase.
>
> On the right, TJX is absent from the saved weekly strategy allocation. The source results do not record a stock-specific rejection reason, so we do not infer one.

**过渡 / Transition**

> 中文：这些数据都按股票代码和信号日期关联。我们现在切换日期，看看这种关联如何工作。  
> English: These records are linked by ticker and signal date. Let's change the date to see that connection in action.

## 第 5 步：演示统一历史日期 / Step 5: Demonstrate the shared date

**建议用时 / Time：1 分钟 / 1 minute**

**怎么操作 / Actions**

1. 回到「关注股票 / Watchlist」，把「统一历史信号日期 / Shared historical signal date」改为 `2022-08-26`。 / Return to Watchlist and select 2022-08-26.
2. 等待关注结果加载，指出排名已经改变。 / Wait for the results and point out the changed rankings.
3. 点击顶部「股票与权重 / Stocks & weights」；再点「输入数据 / Input data」和「股票排名 / Stock rankings」，分别指出所选日期相同。 / Visit Stocks & weights, Input data and Stock rankings, pointing out the shared date in each section.
4. 回到「关注股票 / Watchlist」，点击「载入演示示例 / Load demo example」，恢复 `2026-08-28`。 / Return to Watchlist and load the demo example to restore 2026-08-28.

**预期画面 / Expected result：** 2022-08-26 时，SCL、TJX、CMG 的排名分别为 34、23、35，三只均未入选当周策略。四处日期应一致。 / On 2022-08-26, the ranks are 34, 23 and 35; none of these three stocks is selected. All four date selectors should agree.

**中文照读**

> 现在我把信号日期改为 2022 年 8 月 26 日。我们看到，同样三只股票在这一周有不同的排名和策略状态。
>
> 这个日期会同步到关注结果、股票配置、排名以及与输出对齐的输入表。这样就能避免拿一周的输入去解释另一周的输出。
>
> 如果需要检查更早的原始数据，也可以在输入区域切换到完整源文件模式，使用独立日期浏览。现在我先恢复标准示例，继续展示整体策略表现。

**English script**

> I am changing the signal date to 26 August 2022. The same three stocks now have different rankings and selection results.
>
> This date is shared across the watchlist, stock allocations, rankings and output-aligned input table. That prevents us from using one week's inputs to explain another week's outputs.
>
> Earlier source data can also be inspected separately in Full source file mode. I will now restore the standard example before moving to the original strategy's overall performance.

## 第 6 步：展示原策略完整组合表现 / Step 6: Show original strategy performance

**建议用时 / Time：1 分 15 秒 / 1 minute 15 seconds**

**怎么操作 / Actions**

1. 点击顶部「组合表现 / Performance」，先指向「原策略完整组合表现 / Original strategy · full portfolio」和日期区间。 / Open Performance and point to the full-portfolio heading and date range.
2. 保持「全部 / All history」，展示「账户资金 / Account value」。 / Keep All history selected and show Account value.
3. 依次点击「每周收益 / Weekly return」和「历史回撤 / Drawdown」，在曲线上悬停展示提示。 / Switch to Weekly return and Drawdown; hover over the chart to show a value.
4. 结束时切回「账户资金 / Account value」。 / Return to Account value afterwards.

**指标核对表 / Metric reference**

| 指标 / Metric | 示例值 / Value |
|---|---:|
| 回测信号区间 / Backtest signal period | 2022-08-26 → 2026-08-28 |
| 信号周数 / Signal weeks | 210 |
| 初始研究资金 / Initial research capital | 100,000.00 |
| 期末账户资金 / Final account value | 149,330.61 |
| 累计收益 / Total return | +49.33% |
| 年化收益 / Annualized return | 10.44% |
| 最大回撤 / Maximum drawdown | −24.88% |
| 夏普比率 / Sharpe ratio | 0.543 |

**中文照读**

> 这一部分展示原策略完整组合的回测表现，信号区间从 2022 年 8 月 26 日到 2026 年 8 月 28 日，共 210 周。
>
> 研究账户从十万增长到约十四万九千三百三十点六一，累计收益约 49.33%，年化收益约 10.44%。回撤图帮助我们看到期间的下跌风险，最大回撤约为 24.88%。
>
> 需要明确的是，关注列表只改变我们查看哪些股票。这里的收益始终属于原策略完整组合，不是 SCL、TJX 和 CMG 组成的新组合收益。金额沿用原研究账户单位；这些是历史模拟结果，不保证未来表现。

**English script**

> This section shows the original strategy's full-portfolio backtest. It covers 210 signal weeks, from 26 August 2022 to 28 August 2026.
>
> The research account grows from 100,000 to approximately 149,330.61, with a total return of 49.33% and an annualized return of 10.44%. The drawdown chart shows the declines during the period, including a maximum drawdown of about 24.88%.
>
> The watchlist only changes which stocks we inspect. These returns always describe the original strategy's full portfolio, not a new portfolio of SCL, TJX and CMG. Amounts retain the original research account units. These historical simulations do not guarantee future performance.

**过渡 / Transition**

> 中文：除了在页面查看，用户还可以导出当前关注股票的结果。  
> English: Users can also export the results for the stocks they are currently inspecting.

## 第 7 步：展示当前选择导出 / Step 7: Export the current selection

**建议用时 / Time：45 秒 / 45 seconds**

**怎么操作 / Actions**

1. 点击「关注股票 / Watchlist」，再点「载入演示示例 / Load demo example」。 / Open Watchlist and load the demo example again.
2. 核对 `2026-08-28` 和 SCL、TJX、CMG，点击「导出当前 CSV / Export current CSV」。 / Check the date and three stocks, then click Export current CSV.
3. 展示浏览器的下载完成提示；若已提前准备表格软件，可打开文件，展示三条记录。 / Show the completed download; optionally open it in a spreadsheet application prepared beforehand.
4. 指向「导出 JSON / Export JSON」，不必现场展开所有字段。 / Point to Export JSON without reading every field aloud.

**预期结果 / Expected result：** 下载文件名为 `cs5_6_equity-watchlist-2026-08-28.csv`（重复下载时浏览器可能加后缀），含三只关注股票。TJX 的权重为空；CSV 权重使用小数比例，`0.2` 表示 20%。 / The download contains the three followed stocks. TJX's weights are blank; CSV weights use decimal fractions, so 0.2 means 20%.

**中文照读**

> 这个导出对应当前结果版本、当前日期和当前关注股票，包含输入因子、排名、策略状态以及可用的权重信息。
>
> CSV 适合用表格软件检查，JSON 适合给其他系统读取。对于缺失的配置，系统保留空值，不把它当成零。
>
> 这与下载完整原始输入文件不同：关注区导出的是当前选择，原始文件下载仍保留完整源数据。

**English script**

> This export matches the current run, date and watchlist. It includes input factors, rankings, selection status and any available allocation weights.
>
> CSV is convenient for spreadsheet review, while JSON is suitable for software integration. Missing allocations remain empty rather than being converted to zero.
>
> This differs from a full source-file download: the watchlist export contains the current selection, while original-file downloads preserve the complete source data.

**过渡 / Transition**

> 中文：最后，我展示客户如何把这些功能放进自己的网站。  
> English: Finally, I will show how the client can bring these capabilities into their website.

## 第 8 步：展示接口与网站嵌入 / Step 8: Demonstrate APIs and embedding

**建议用时 / Time：1 分 15 秒 / 1 minute 15 seconds**

**怎么操作 / Actions**

1. 在关注详情底部展开「查看回测价格与数据来源 / Backtest prices & provenance」，点击「查看当前关注接口 JSON / View current watchlist API JSON」。 / Expand Backtest prices & provenance and open View current watchlist API JSON.
2. 在新标签页中指出 `signal_date`、`requested_tickers`、`rows` 和 `selection_status`；随后返回 Dashboard 标签页。 / Point to the date, selected tickers, rows and selection status, then return to the Dashboard tab.
3. 点击顶部「输入输出接口 / Input & output APIs」，指出股票清单、输入清单和完整 API 文档入口。 / Open Input & output APIs and point to the stock catalog, input catalog and API documentation links.
4. 点击「查看网站嵌入示例 / View website embedding example」。在新页面点击「查看策略 → / Explore strategies →」，等待模块出现。 / Open the embedding example and click Explore strategies to reveal the module.
5. 在框内点击「载入演示示例 / Load demo example」，展示同样的交互。 / Load the demo example inside the frame to demonstrate the same interaction.

**中文照读**

> 页面使用的研究结果也通过接口提供。这里的 JSON 对应刚才选择的日期和股票，客户可以读取相同的输入、排名和配置状态。
>
> 接入有两种方式。第一种是在客户网站新增入口，用 iframe 嵌入我们的完整 Dashboard。现在看到的是本地嵌入示例，框内仍然可以选择股票、切换日期和导出结果。
>
> 第二种是由客户保留自己的页面设计，调用我们的接口来展示数据。模块使用独立股票池，不会把这里的关注列表当成客户网站的全局资产选择器。
>
> 当前已经完成独立模块和接口。正式接入还需要客户确认部署地址、登录要求和测试环境，并完成网站集成验收。

**English script**

> The research data used by the page is also available through APIs. This JSON response matches the date and stocks we selected, allowing the client to retrieve the same inputs, rankings and allocation status.
>
> There are two integration options. First, the client can add an entry to their website and embed the complete Dashboard in an iframe. This local example keeps the stock selector, date controls and exports available inside the frame.
>
> Second, the client can keep their own interface and use our APIs to display the results. Our module has its own stock universe, separate from the website's global asset selector.
>
> The standalone module and APIs are ready. Integration into the client's site still requires an agreed hosting address, authentication requirements and testing in their staging environment.

## 结束语 / Closing

**建议用时 / Time：30 秒 / 30 seconds**

**操作 / Action：** 返回主 Dashboard 的「关注股票 / Watchlist」页面，保留标准三股票示例。 / Return to the main Dashboard's Watchlist with the standard three-stock example.

**中文照读**

> 今天我们从选择关注股票开始，查看了对应的输入数据、模型排名、实际策略配置和整体历史表现，也演示了导出与网站接入方式。
>
> 这个版本让用户能够清楚查看已有研究结果，也为客户提供了两种使用方式：直接嵌入 Dashboard，或通过接口构建自己的界面。谢谢大家，接下来欢迎提问。

**English script**

> Today we started with stocks of interest, then inspected their inputs, model rankings, actual strategy allocations and the original portfolio's historical performance. We also demonstrated exports and integration options.
>
> This version makes the existing research results accessible through either the complete Dashboard or APIs for the client's own interface. Thank you. I am happy to take questions.

## 可选演示：数据边界 / Optional demonstrations: data boundaries

时间不足可跳过，不影响主流程。 / Skip these if time is limited.

### A. 不支持的股票 / Unsupported stock（约 30 秒 / about 30 seconds）

**操作 / Action：** 在关注搜索框输入 `AAPL`，展示无匹配提示；然后清空搜索框或点击载入示例。 / Search for AAPL, show the unsupported-stock message, then clear the search or reload the example.

> 中文：这个股票不在当前外部评估股票池中，所以系统明确提示不支持。它不会为研究范围外的股票生成结果；扩大股票池需要另外准备数据并验证模型流程。
>
> English: This stock is outside the current external evaluation universe, so the system clearly marks it as unsupported. It does not generate results for stocks outside the research scope. Expanding the universe requires additional data and validation.

### B. 有排名但没有配置 / Rankings without allocation data（约 45 秒 / about 45 seconds）

**操作 / Actions：** 在顶部「股票排名 / Stock rankings」的日期菜单选择 `2019-08-30`，再返回关注区域。这个日期不在关注区通常提供的 210 周回测日期内，因此从排名区域选择。最后点击载入示例恢复。 / Select 2019-08-30 in Stock rankings, then return to Watchlist. Choose it from the rankings section because it is outside the 210-week allocation period. Reload the example afterwards.

> 中文：这一天有部分模型排名，但没有对应的组合回测配置。所以页面显示“该日期无配置”，而不是“未入选”。这两种状态含义不同，缺失的数据也不会被显示成零。
>
> English: Some model rankings exist for this date, but no corresponding portfolio backtest allocation is available. The page therefore shows No allocation data rather than Not selected. These states have different meanings, and missing values are not displayed as zero.

## 问答备用 / Questions and suggested answers

### 1. 为什么 TJX 排名第二却没有入选？ / Why is TJX not selected despite ranking second?

> 中文：模型排名在策略过滤之前生成，最终配置还要经过策略规则。原文件没有保存 TJX 当周的逐股排除原因，因此我们可以确认它没有入选，但不会把某个具体原因当作已验证事实。
>
> English: Rankings are generated before the strategy filters are applied. The final allocation also depends on those rules. The source files do not store TJX's individual rejection reason for that week, so we can confirm the outcome without claiming a specific verified cause.

### 2. 选择几只喜欢的股票，会重新计算收益吗？ / Does selecting stocks recalculate returns?

> 中文：当前不会。关注列表只改变查看范围。展示的收益始终来自原策略完整组合；按用户选择重新回测属于另一个功能。
>
> English: Not in this version. The watchlist only changes the viewing selection. Returns always come from the original strategy's full portfolio. Recalculating a portfolio from user-selected stocks would be a separate feature.

### 3. 0.8083 是 80.83% 的收益或上涨概率吗？ / Does 0.8083 mean an 80.83% return or chance of rising?

> 中文：不是。它是三个模型组件当周百分位得分的平均值，用于相对排序，不是收益预测或概率。
>
> English: No. It is the average of the three model components' weekly percentile scores. It is a relative ranking measure, not a return forecast or a probability.

### 4. 可以上传新数据或查看实时结果吗？ / Can users upload data or view live results?

> 中文：目前的输入接口用于查询项目已有的数据。上传新数据、运行新预测、获取实时行情和定时更新，都需要另行开发与验证。
>
> English: The current input APIs query data already available in the project. Uploads, new predictions, live market feeds and scheduled updates require additional development and validation.

### 5. 66 只和 40 只分别是什么？ / What do the 66 and 40 stocks represent?

> 中文：66 只是完整训练股票池，40 只是与其不重叠的独立外部评估股票池。当前关注功能针对这 40 只股票；每个历史日期实际有数据的股票数量可能不同，研究范围不包含 ETF。
>
> English: The 66 stocks form the full training universe. The 40 stocks are a separate, non-overlapping external evaluation universe. The watchlist covers these 40 stocks, although historical data availability varies by date. ETFs are outside this research scope.

### 6. 能否证明策略跑赢市场？ / Does this show that the strategy outperformed the market?

> 中文：当前没有与本研究范围、日期和执行假设一致的已验证基准序列，所以页面将基准显示为不可用。今天展示的是策略本身的历史结果，不据此声称跑赢市场。
>
> English: We do not currently have a verified benchmark series matched to this universe, period and execution assumptions. The benchmark is shown as unavailable. We are presenting the strategy's historical results without claiming market outperformance.

### 7. 客户现在能直接打开本机链接吗？ / Can the client open this local link from another computer?

> 中文：这个地址只指向运行服务的电脑。客户可以拿到交付包在自己的环境运行；如果要从网站访问，需要部署到双方约定的地址，再配置嵌入或接口访问及登录要求。
>
> English: This address points only to the computer running the service. The client can run the delivery package in their own environment. Website access requires deployment to an agreed address, followed by embedding or API access configuration and any required authentication.

### 8. 为什么实际权重不是正好 20%？ / Why are actual weights not exactly 20%?

> 中文：20% 是目标权重。历史模拟使用整数股，并考虑费用与现金约束，所以调仓后的实际权重会略有差异。最后一个持有期结束后已清仓，因此这些数值表示历史配置。
>
> English: Twenty percent is the target weight. The simulation uses integer shares and includes costs and cash constraints, so weights after rebalancing can differ slightly. Positions were liquidated after the final holding period; these figures describe historical allocations.

## 现场故障时怎么说 / If something goes wrong

| 情况 / Situation | 操作 / Action | 可直接说 / Suggested wording |
|---|---|---|
| 操作顺序乱了 / Lost your place | 回到关注页，点击载入示例。 / Return to Watchlist and load the example. | “我先恢复标准示例，确保日期和股票一致。” / “I will restore the standard example so the date and stocks are consistent.” |
| 请求超时 / Request times out | 等待提示，检查本地服务，再点击重试。 / Check the local service and retry. | “这次查询暂时没有返回，我们重试读取保存的结果。” / “This query has not returned yet. I will retry loading the saved results.” |
| 嵌入页未响应 / Embedded module does not load | 使用页面的重新加载或独立 Dashboard 入口。 / Use Retry module or the standalone link. | “嵌入模块有独立的错误处理，我们也可以继续从独立页面查看。” / “The embedded module has its own error handling; we can also continue in the standalone view.” |
| API 文档界面打不开 / API documentation UI does not load | 打开预先准备的 OpenAPI JSON。 / Use the prepared OpenAPI JSON. | “我用离线可读的接口定义展示字段，查询接口仍可独立验证。” / “I will show the fields through the API definition; the query endpoints can be checked separately.” |
| 服务暂时无法恢复 / Service cannot be restored during the demo | 使用下方预先准备的截图，并明确这是保存画面。 / Use the prepared screenshots and identify them as saved views. | “这是已保存的验证截图，不是当前实时页面。我先用它说明数据关系。” / “This is a saved validation screenshot, not the current live page. I will use it to explain how the data connects.” |

备用截图 / Backup screenshots：[桌面关注结果 / Watchlist](watchlist-desktop.jpg) · [TJX 详情 / TJX details](watchlist-detail.jpg) · [手机搜索 / Mobile search](watchlist-mobile.jpg)。

## 上台前最后记住 / Last reminders before presenting

- **选择股票 ≠ 生成新组合。 / Selecting stocks does not generate a new portfolio.**
- **模型排名 ≠ 策略实际入选。 / Model rank does not guarantee strategy selection.**
- **原策略收益 ≠ 关注列表收益。 / Original strategy returns are not watchlist returns.**
- **历史信号日期 ≠ 当前市场日期，也不是已验证的财报发布时间。 / A historical signal date is not today's market date or an independently verified financial publication timestamp.**
- **没有配置记录 ≠ 未入选，缺失数值 ≠ 0。 / No allocation data differs from Not selected; missing values differ from zero.**
- **本地嵌入示例 ≠ 客户生产网站已完成接入。 / The local embedding example is not a completed integration into the client's production site.**

相关资料 / Further reference：[关注股票功能与接口](PRESENTATION_WATCHLIST.md) · [本版验收记录](PRESENTATION_VALIDATION.md) · [API 合同](API_V1.md)。
