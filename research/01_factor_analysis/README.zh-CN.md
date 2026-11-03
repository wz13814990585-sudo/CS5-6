# 因子筛选

[English](README.md) | **中文**

<a id="readme-zh"></a>

对 66 只训练股票的 45 个候选因子执行全样本 Rank IC 筛选，形成四类模型共用的因子集合。

### 运行方式（在项目根目录）

```bash
python research/01_factor_analysis/factor_analysis.py            # 默认读取 data/test_45_factors_weekly.csv
```

输出写入 `research/01_factor_analysis/outputs/`：

| 文件 | 内容 |
|---|---|
| `full_sample_factor_screening.csv` | 每个因子的覆盖率、平均 Rank IC、Rank ICIR、年度符号一致性、筛选状态及原因 |
| `weekly_rank_ic.csv` / `annual_rank_ic.csv` | 周度和年度 Rank IC |
| `factor_correlations.csv` / `high_correlation_pairs.csv` | 平均周度 Spearman 相关矩阵，以及 \|ρ\| ≥ 0.85 的因子对 |
| `seven_factor_results.csv` / `five_factor_comparison.csv` | 七因子筛选结果和财务因子设计比较 |
| `factor_sets.json` / `model_features.json` | 模型使用的 5 / 7 / 11 / 45 因子清单及筛选配置 |

`results/Factor_Analysis_Results_EN.xlsx` 是交付的结果工作簿，`Factor_Analysis_Guide_EN.docx` 说明研究方法。

### 筛选规则

- 使用每周横截面 Spearman Rank IC，并列值采用平均排名；每周至少有 20 只股票、因子至少有 5 个不同取值。宏观因子在同周股票间相同，因此 Rank IC 无定义，单独保留。
- 进入七因子的门槛：平均 Rank IC 的绝对值 ≥ 0.01，Rank ICIR 的绝对值 ≥ 0.08（未年化），在至少 60% 的合格年份中符号一致，覆盖率 ≥ 80%，至少有 104 个有效周。
- 去重：按平均 Rank IC 的绝对值从高到低贪心选择；若后续因子与已选因子的平均周度相关系数绝对值 ≥ 0.85，则标为相关替代项。与原始收益/波动率列相同的 4 个 `cs_rank_*` 列被移除。
- **7 因子**：`revenue_growth_yoy, ret_120d, cashflow_to_assets, ret_1d, ret_5d, close_location_value, body_range_ratio`。
- **11 因子**：上述 7 因子加 4 个宏观因子，即 VIX 水平、VIX 的 5 观测期变化、10 年减 2 年国债利差、10 年利率的 5 观测期变化。
- **5 因子**：事先按财务维度指定，并非通过 IC 门槛选出，分别是营收增长、经营盈利能力、现金流/资产、负债/资产和资产增长。
- **45 因子**：所有候选列。

> **局限：**筛选使用完整期间（2016-09-02 至 2026-08-21）的收益，因此之后将相同历史划为 Development / Validation / Final Test，并不能得到独立测试。最后一周 2026-08-28 没有下一周价格，已排除。
