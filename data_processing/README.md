# Data collection and cleaning reference

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

Reproduction starts from the supplied processed weekly data. Raw acquisition and reconstruction are outside this delivery scope. The scripts below document the upstream method; they are not steps required to reproduce the selected strategy or run the Ensemble training demonstration.

Run every script with the **project root as the working directory**; they read and write `data/`. They need network access (Yahoo Finance, SEC EDGAR, FRED) and an extra dependency. These are data-generation commands, not package checks. They write frozen-data paths, so run new acquisition experiments in a separate project copy:

```bash
pip install -r requirements-data.txt      # yfinance
export SEC_USER_AGENT="YourProject/1.0 your.name@example.com"   # SEC requires a contact e-mail
# Windows PowerShell: $env:SEC_USER_AGENT = "YourProject/1.0 your.name@example.com"
```

| Order | Script | Input → output |
|---|---|---|
| 1 | `fetch_and_clean.py` | Yahoo Finance → `data/Original_basic_data.csv`, `data/clean_basic_data.csv`, `data/audit/` |
| 2 | `build_technical_factors.py` | `clean_basic_data.csv` → `data/test_data_weekly.csv` (35 internal factors + target), `data/factor_definitions.csv` |
| 3 | `build_external_factors.py` | Weekly panel + SEC companyfacts (6 fundamental factors aligned to filing dates) + FRED (4 macro factors) → `data/test_45_factors_weekly.csv` |
| 4 | `collect_additional_40_staples.py` | Selects 40 external stocks not in the original list → `data/additional_40/*.csv` |
| 5 | `export_additional_40_excel.py` | Adds next-week open/close prices → `additional_40_five_factors_targets_final.xlsx` |

```bash
python data_processing/fetch_and_clean.py
python data_processing/build_technical_factors.py
python data_processing/build_external_factors.py
python data_processing/collect_additional_40_staples.py
python data_processing/export_additional_40_excel.py \
  --input data/additional_40/additional_40_weekly_5_factors.csv \
  --universe data/additional_40/additional_40_universe.csv \
  --daily data/additional_40/additional_40_daily_ohlcv.csv \
  --output data/additional_40/additional_40_five_factors_targets_final.xlsx
```

(Step 5's default paths point next to the script, so pass the arguments explicitly.)

### Notes

- `collect_sec_fundamentals.py` is the SEC helper module called by the historical acquisition steps 3 and 4.
- Keep new data-acquisition experiments separate from the supplied processed inputs.
- Downloaded data changes as sources are revised, so reruns are not guaranteed to match the frozen files in `data/` byte for byte; see `data/README.md`.

- The supplied scripts are later repaired versions; historical research files came from an earlier version. Rebuilding those sources is not part of this delivery. The documented reproduction uses the supplied weekly panels.

---

<a id="readme-zh"></a>

## 中文

复现从提供的已处理周度数据开始，原始采集和重建不属于本次交付范围。以下脚本记录上游方法，不是复现所选策略或运行 Ensemble 训练演示的必要步骤。

所有脚本都应以**项目根目录作为工作目录**运行；它们读取和写入 `data/`。运行需要网络访问 Yahoo Finance、SEC EDGAR、FRED，并安装额外依赖。这些命令会生成数据，不是交付包检查；它们会写入冻结数据所在路径，因此新的采集实验应在独立项目副本中执行。

```bash
pip install -r requirements-data.txt      # 安装 yfinance
export SEC_USER_AGENT="YourProject/1.0 your.name@example.com"   # SEC 要求提供联系邮箱
# Windows PowerShell: $env:SEC_USER_AGENT = "YourProject/1.0 your.name@example.com"
```

| 顺序 | 脚本 | 输入 → 输出 |
|---|---|---|
| 1 | `fetch_and_clean.py` | Yahoo Finance → `data/Original_basic_data.csv`、`data/clean_basic_data.csv`、`data/audit/` |
| 2 | `build_technical_factors.py` | `clean_basic_data.csv` → `data/test_data_weekly.csv`（35 个内部因子及目标标签）、`data/factor_definitions.csv` |
| 3 | `build_external_factors.py` | 周度面板 + SEC companyfacts（按申报日期对齐的 6 个基本面因子）+ FRED（4 个宏观因子）→ `data/test_45_factors_weekly.csv` |
| 4 | `collect_additional_40_staples.py` | 选择不在原股票列表中的 40 只外部股票 → `data/additional_40/*.csv` |
| 5 | `export_additional_40_excel.py` | 加入下一周开盘价/收盘价 → `additional_40_five_factors_targets_final.xlsx` |

```bash
python data_processing/fetch_and_clean.py
python data_processing/build_technical_factors.py
python data_processing/build_external_factors.py
python data_processing/collect_additional_40_staples.py
python data_processing/export_additional_40_excel.py \
  --input data/additional_40/additional_40_weekly_5_factors.csv \
  --universe data/additional_40/additional_40_universe.csv \
  --daily data/additional_40/additional_40_daily_ohlcv.csv \
  --output data/additional_40/additional_40_five_factors_targets_final.xlsx
```

第 5 步的默认路径指向脚本所在目录，因此需要显式传入上述参数。

### 注意事项

- `collect_sec_fundamentals.py` 是历史采集步骤 3 和 4 调用的 SEC 辅助模块。
- 新的数据采集实验应与提供的已处理输入分开保存。
- 数据源会修订历史内容，重新下载不保证与 `data/` 内冻结文件逐字节一致；详见 `data/README.md`。
- 当前脚本是后续修复版本，历史研究文件由更早的版本生成。重建这些来源不属于本次交付，文档中的复现流程使用已提供的周度面板。
