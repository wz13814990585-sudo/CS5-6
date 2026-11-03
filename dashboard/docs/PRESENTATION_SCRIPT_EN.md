# SafeCapital Dashboard — English presentation script

Dashboard 1.4 · English-first client edition · 2026-11-03 · 8–10 minutes plus questions.

## How to use this script

Each step contains actions, expected results, an English script and transitions. Read the English script aloud; the action instructions and reference tables are for the presenter. An optional Chinese reference is available in PRESENTATION_SCRIPT_ZH_EN.md. The figures refer to the historical results delivered with this project; verify them again if the research results change.

Choose stocks → inspect inputs → explain rankings and actual allocations → review original strategy performance → export → demonstrate integration.

## Before the presentation

### Start and open the Dashboard

If the page already works, leave the existing service running. Otherwise, complete the installation in the package's root `START_HERE.md`, then open a terminal in the extracted project root (the directory containing `dashboard`):

```bash
.venv-dashboard/bin/python dashboard/start.py
```

For a Web package with customised configuration, append `--config config.toml`. On Windows use `.\.venv-dashboard\Scripts\python.exe dashboard/start.py`. Keep the terminal running. Open these pages beforehand, using the Dashboard as the main presentation tab.

| Page              | Link                                                             | Purpose                                      |
| ----------------- | ---------------------------------------------------------------- | -------------------------------------------- |
| English Dashboard | [English demo](http://127.0.0.1:8000/?lang=en#watchlist)         | English interface                            |
| Embedding example | [Host preview](http://127.0.0.1:8000/embed-example.html?lang=en) | Website integration demonstration            |
| API documentation | [API docs](http://127.0.0.1:8000/api/docs)                       | Optional developer walkthrough               |
| API definition    | [OpenAPI JSON](http://127.0.0.1:8000/api/openapi.json)           | Fallback if the documentation UI cannot load |

These addresses work on the computer running the service. Use screen sharing for a remote presentation. The API documentation UI uses an external CDN, so check it beforehand; the Dashboard can display its existing data offline.

### Set the starting state

| Action                                             | Check                                             |
| -------------------------------------------------- | ------------------------------------------------- |
| Choose English (or open the explicit English URL). | The interface matches your chosen script.         |
| Keep the default result version.                   | Use the same run throughout.                      |
| Open Watchlist.                                    | The stock selector is visible.                    |
| Click **Reset demo**, then **Load demo example**.  | The list contains SCL, TJX and CMG on 2026-08-28. |

Start with the Watchlist section on screen. If you lose your place, use Load demo example to restore the three stocks, the example date, and the chart/input filters.

## Step 1: Introduce the module

**45 seconds**

**Actions**

1. Stay on Watchlist and point to the search box, date and three selected stocks.
2. Keep the date and charts unchanged for the introduction.

**English script**

> Hello everyone. Today I will demonstrate our SafeCapital Dashboard. It brings the project's existing input data, model rankings and historical strategy results into one interface.
>
> Users can start with stocks they follow, then inspect their inputs, rankings and actual strategy selection on the same historical date. I will also demonstrate exports and the options for integrating this module into the client's website.
>
> We are viewing completed, verified historical research results. These queries do not retrain the models or rerun the backtest.

**Transition**

> Let's start with the user's first action: choosing stocks to follow.

## Step 2: Search and select stocks

**1 minute**

**Actions**

1. Search for `Chipotle`, show the CMG match and select it.
2. Point out that CMG is already followed, so the list still contains three stocks.
3. Search for `URBN` and select it; show the list growing from three to four stocks.
4. Click the × beside URBN to remove it.

The final list is SCL, TJX and CMG, dated 2026-08-28.

**English script**

> Users can search by ticker or company name. For example, searching for Chipotle finds the ticker CMG.
>
> They can follow several stocks, remove individual stocks or clear the list. Duplicate selections are avoided. The available choices are the 40 external evaluation stocks in this module, rather than every stock in the market.
>
> The watchlist determines which research results the user inspects. It does not change the original research universe or generate a new investment portfolio.

**Transition**

> Next, let's compare the model rankings with actual strategy selection for these three stocks.

## Step 3: Compare ranking and selection

**1 minute**

**Actions**

1. Load the demo example to restore the standard state.
2. Scroll to Your watchlist results.
3. Point to the rank, selection status and weight columns.

**Expected result: 2026-08-28**

| Ticker | Rank | Ensemble score | Selection    | Target | Actual |
| ------ | ---: | -------------: | ------------ | -----: | -----: |
| SCL    |    1 |         0.9250 | Selected     | 20.00% | 19.95% |
| TJX    |    2 |         0.8083 | Not selected |      — |      — |
| CMG    |    3 |         0.7917 | Selected     | 20.00% | 19.98% |

**English script**

> On the signal date of 28 August 2026, SCL, TJX and CMG rank first, second and third respectively.
>
> However, SCL and CMG appear in the saved strategy allocation, while TJX does not, despite ranking second. Model ranking and final strategy allocation are outputs from different stages. A high rank does not guarantee selection.
>
> For selected stocks, we show target weights and actual weights from the simulated rebalance. Integer shares, costs and cash constraints can cause small differences. These are historical allocations, not current live holdings.

**Transition**

> Let's use TJX to look more closely at its inputs, model outputs and strategy status.

## Step 4: Explain the inputs and outputs

**1 minute 30 seconds**

**Actions**

1. Click View details in the TJX row and scroll to the detail section.
2. Point to Inputs · five raw factors, Outputs · model assessment, and Result · strategy allocation. These sections stack vertically on a phone.
3. Highlight rank #2, score 0.8083 and Not selected.

**Input reference; no need to read every value**

| Factor                       | Displayed value |
| ---------------------------- | --------------: |
| Revenue growth, year on year |        0.116225 |
| Operating profitability      |        0.329211 |
| Cash flow to assets          |        0.223447 |
| Debt to assets               |        0.079374 |
| Asset growth, year on year   |        0.134974 |

**English script**

> There are two meanings of input here. The user enters viewing preferences: stocks and a date. The model inputs are the financial factors already stored in the project.
>
> On the left, we show five raw factors covering revenue growth, profitability, cash flow, debt and asset growth. The models use within-week percentile transformations of these inputs.
>
> In the middle, TJX ranks second with an ensemble score of approximately 0.8083. The component percentiles are 62.5%, 87.5% and 92.5%. These express relative rankings, not expected returns or probabilities of a price increase.
>
> On the right, TJX is absent from the saved weekly strategy allocation. The source results do not record a stock-specific rejection reason, so we do not infer one.

**Transition**

> These records are linked by ticker and signal date. Let's change the date to see that connection in action.

## Step 5: Demonstrate the shared date

**1 minute**

**Actions**

1. Return to Watchlist and select 2022-08-26.
2. Wait for the results and point out the changed rankings.
3. Visit Stocks & weights, Input data and Stock rankings, pointing out the shared date in each section.
4. Return to Watchlist and load the demo example to restore 2026-08-28.

On 2022-08-26, the ranks are 34, 23 and 35; none of these three stocks is selected. All four date selectors should agree.

**English script**

> I am changing the signal date to 26 August 2022. The same three stocks now have different rankings and selection results.
>
> This date is shared across the watchlist, stock allocations, rankings and output-aligned input table. That prevents us from using one week's inputs to explain another week's outputs.
>
> Earlier source data can also be inspected separately in Full source file mode. I will now restore the standard example before moving to the original strategy's overall performance.

## Step 6: Show original strategy performance

**1 minute 15 seconds**

**Actions**

1. Open Performance and point to the full-portfolio heading and date range.
2. Keep All history selected and show Account value.
3. Switch to Weekly return and Drawdown; hover over the chart to show a value.
4. Return to Account value afterwards.

**Metric reference**

| Metric                   |                   Value |
| ------------------------ | ----------------------: |
| Backtest signal period   | 2022-08-26 → 2026-08-28 |
| Signal weeks             |                     210 |
| Initial research capital |              100,000.00 |
| Final account value      |              149,330.61 |
| Total return             |                 +49.33% |
| Annualized return        |                  10.44% |
| Maximum drawdown         |                 −24.88% |
| Sharpe ratio             |                   0.543 |

**English script**

> This section shows the original strategy's full-portfolio backtest. It covers 210 signal weeks, from 26 August 2022 to 28 August 2026.
>
> The research account grows from 100,000 to approximately 149,330.61, with a total return of 49.33% and an annualized return of 10.44%. The drawdown chart shows the declines during the period, including a maximum drawdown of about 24.88%.
>
> The watchlist only changes which stocks we inspect. These returns always describe the original strategy's full portfolio, not a new portfolio of SCL, TJX and CMG. Amounts retain the original research account units. These historical simulations do not guarantee future performance.

**Transition**

> Users can also export the results for the stocks they are currently inspecting.

## Step 7: Export the current selection

**45 seconds**

**Actions**

1. Open Watchlist and load the demo example again.
2. Check the date and three stocks, then click Export current CSV.
3. Show the completed download; optionally open it in a spreadsheet application prepared beforehand.
4. Point to Export JSON without reading every field aloud.

The download contains the three followed stocks. TJX's weights are blank; CSV weights use decimal fractions, so 0.2 means 20%.

**English script**

> This export matches the current run, date and watchlist. It includes input factors, rankings, selection status and any available allocation weights.
>
> CSV is convenient for spreadsheet review, while JSON is suitable for software integration. Missing allocations remain empty rather than being converted to zero.
>
> This differs from a full source-file download: the watchlist export contains the current selection, while original-file downloads preserve the complete source data.

**Transition**

> Finally, I will show how the client can bring these capabilities into their website.

## Step 8: Demonstrate APIs and embedding

**1 minute 15 seconds**

**Actions**

1. Expand Backtest prices & provenance and open View current watchlist API JSON.
2. Point to the date, selected tickers, rows and selection status, then return to the Dashboard tab.
3. Open Input & output APIs and point to the stock catalog, input catalog and API documentation links.
4. Open the embedding example and click Explore strategies to reveal the module.
5. Load the demo example inside the frame to demonstrate the same interaction.

**English script**

> The research data used by the page is also available through APIs. This JSON response matches the date and stocks we selected, allowing the client to retrieve the same inputs, rankings and allocation status.
>
> There are two integration options. First, the client can add an entry to their website and embed the complete Dashboard in an iframe. This local example keeps the stock selector, date controls and exports available inside the frame.
>
> Second, the client can keep their own interface and use our APIs to display the results. Our module has its own stock universe, separate from the website's global asset selector.
>
> The standalone module and APIs are ready. Integration into the client's site still requires an agreed hosting address, authentication requirements and testing in their staging environment.

## Closing

**30 seconds**

Return to the main Dashboard's Watchlist with the standard three-stock example.

**English script**

> Today we started with stocks of interest, then inspected their inputs, model rankings, actual strategy allocations and the original portfolio's historical performance. We also demonstrated exports and integration options.
>
> This version makes the existing research results accessible through either the complete Dashboard or APIs for the client's own interface. Thank you. I am happy to take questions.

## Optional demonstrations: data boundaries

Skip these if time is limited.

### A. Unsupported stock (about 30 seconds)

Search for AAPL, show the unsupported-stock message, then clear the search or reload the example.

> This stock is outside the current external evaluation universe, so the system clearly marks it as unsupported. It does not generate results for stocks outside the research scope. Expanding the universe requires additional data and validation.

### B. Rankings without allocation data (about 45 seconds)

Select 2019-08-30 in Stock rankings, then return to Watchlist. Choose it from the rankings section because it is outside the 210-week allocation period. Reload the example afterwards.

> Some model rankings exist for this date, but no corresponding portfolio backtest allocation is available. The page therefore shows No allocation data rather than Not selected. These states have different meanings, and missing values are not displayed as zero.

## Questions and suggested answers

### Why is TJX not selected despite ranking second?

> Rankings are generated before the strategy filters are applied. The final allocation also depends on those rules. The source files do not store TJX's individual rejection reason for that week, so we can confirm the outcome without claiming a specific verified cause.

### Does selecting stocks recalculate returns?

> Not in this version. The watchlist only changes the viewing selection. Returns always come from the original strategy's full portfolio. Recalculating a portfolio from user-selected stocks would be a separate feature.

### Does 0.8083 mean an 80.83% return or chance of rising?

> No. It is the average of the three model components' weekly percentile scores. It is a relative ranking measure, not a return forecast or a probability.

### Can users upload data or view live results?

> The current input APIs query data already available in the project. Uploads, new predictions, live market feeds and scheduled updates require additional development and validation.

### What do the 66 and 40 stocks represent?

> The 66 stocks form the full training universe. The 40 stocks are a separate, non-overlapping external evaluation universe. The watchlist covers these 40 stocks, although historical data availability varies by date. ETFs are outside this research scope.

### Does this show that the strategy outperformed the market?

> We do not currently have a verified benchmark series matched to this universe, period and execution assumptions. The benchmark is shown as unavailable. We are presenting the strategy's historical results without claiming market outperformance.

### Can the client open this local link from another computer?

> This address points only to the computer running the service. The client can run the delivery package in their own environment. Website access requires deployment to an agreed address, followed by embedding or API access configuration and any required authentication.

### Why are actual weights not exactly 20%?

> Twenty percent is the target weight. The simulation uses integer shares and includes costs and cash constraints, so weights after rebalancing can differ slightly. Positions were liquidated after the final holding period; these figures describe historical allocations.

## If something goes wrong

| Situation                                  | Action                                                         | Suggested wording                                                                                                   |
| ------------------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Lost your place                            | Return to Watchlist and load the example.                      | “I will restore the standard example so the date and stocks are consistent.”                                        |
| Request times out                          | Check the local service and retry.                             | “This query has not returned yet. I will retry loading the saved results.”                                          |
| Embedded module does not load              | Use Retry module or the standalone link.                       | “The embedded module has its own error handling; we can also continue in the standalone view.”                      |
| API documentation UI does not load         | Use the prepared OpenAPI JSON.                                 | “I will show the fields through the API definition; the query endpoints can be checked separately.”                 |
| Service cannot be restored during the demo | Use the prepared screenshots and identify them as saved views. | “This is a saved validation screenshot, not the current live page. I will use it to explain how the data connects.” |

Backup screenshots: [English watchlist](client-watchlist-en.png), [TJX details](client-details-en.png), [mobile](client-mobile-en.png).

## Last reminders before presenting

- Selecting stocks does not generate a new portfolio.
- Model rank does not guarantee strategy selection.
- Original strategy returns are not watchlist returns.
- A historical signal date is not today's market date or an independently verified financial publication timestamp.
- No allocation data differs from Not selected; missing values differ from zero.
- The local embedding example is not a completed integration into the client's production site.

Further reference: [watchlist API](PRESENTATION_WATCHLIST.md), [API contract](API_V1.md), [validation](PRESENTATION_VALIDATION.md).
