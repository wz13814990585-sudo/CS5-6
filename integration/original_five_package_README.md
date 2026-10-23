# SafeCapital 五包整合版

将已确认的基础数据包、Random Forest、Ridge、XGBoost 和 XGBoostRanker 五个 ZIP 整理为一个工程，提供统一入口和独立运行目录。本次整合未执行数据下载、模型训练或回测；保留的结果均来自原交付包。

五包共有 27 个文件成员。同一份周频训练表在五包中重复出现，按 SHA-256 核对后合并为一份，因此保留 23 个不同的原始文件：8 个 Python 脚本、5 个数据 CSV、4 份模型说明、6 个结果 CSV。原始文件内容不变，来源、路径和哈希记录在 `integration/source_manifest.json`。

## 从哪里开始

在编辑器中打开本文件所在的整个文件夹。先读本说明，再按模型进入 `models/` 查看原始脚本与说明；原始 README 保留了当时 ZIP 内的相对路径，整合版使用根目录的 `run.py`。

```text
SafeCapital_五包整合版_20261022/
├── README.md                  本说明
├── run.py                     统一命令入口；无参数时只显示帮助
├── requirements.txt           四种模型所需依赖
├── requirements-data.txt      数据处理的附加依赖
├── data/                      五个原始数据文件；四种模型共用一份训练表
├── data_processing/           四个原始数据处理脚本
├── models/
│   ├── random_forest/         原始训练脚本与 README_standard.md
│   ├── ridge/                 原始训练脚本与 README.md
│   ├── xgboost/               原始训练脚本与 README.md
│   └── xgboost_ranker/        原始训练脚本与 README.md
├── reference_results/         五包随附的六个历史结果文件
├── integration/               入口实现、原始文件清单和整合检查记录
├── tests/                     统一入口的测试；不训练真实模型
└── runs/                      显式运行后才生成的新工作区和结果
```

未提供的三个模块——单因子分析、统一评估／回测、整数股交易模拟——不包含在本工程中。

## 先查看和检查

在工程根目录打开终端。以下命令只需要 Python 标准库，不下载数据、不导入或执行模型脚本，也不拟合模型：

```bash
python3 run.py
python3 run.py status
python3 run.py verify
python3 run.py check
python3 run.py plan --model all --output runs/preview_all
python3 run.py data --step all --output runs/preview_data --dry-run
```

| 命令 | 用途 |
|---|---|
| `status` | 查看工程信息和当前 Python 的依赖安装情况 |
| `verify` | 对照来源清单验证 23 个原始文件的 SHA-256 |
| `check` | 检查原文件哈希、脚本语法，以及数据字段、行数、日期、数值完整性和重复记录 |
| `plan` | 显示将使用的模型、数据、命令和输出位置，不创建运行目录 |
| `data ... --dry-run` | 预览数据处理步骤，不创建运行目录、不访问数据源 |

`check` 是整合层静态检查，不调用原模型的 `--check-only`，也不代表模型运行成功或历史性能已复现。Random Forest 原脚本没有 `--check-only`；直接执行原脚本会启动训练。

## 后续需要运行时：安装依赖

建议为工程建立独立的 Python 3.12 环境。在 macOS／Linux 终端运行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py status
```

如需数据下载或因子构建，再安装数据依赖：

```bash
python -m pip install -r requirements-data.txt
```

`requirements.txt` 是根据脚本依赖整理的安装清单；`xgboost>=2.0` 保留原 Ranker 的兼容要求。它不是原始实验环境的版本锁定文件，不保证不同版本产生完全一致的数值。本次整合没有完整安装训练依赖或执行训练验收，运行前以 `status` 检查当前环境。

## 显式运行模型

先预览，再执行需要的模型：

```bash
python run.py plan --model ridge --output runs/ridge_first
python run.py train --model ridge --output runs/ridge_first
```

`--model` 可选 `random_forest`、`ridge`、`xgboost`、`xgboost_ranker` 或 `all`。需要完整重跑四种模型时：

```bash
python run.py train --model all --output runs/models_first
```

训练入口会将所选原始脚本及共同训练数据复制到新的运行工作区，保存执行日志和新结果。每种模型运行全部四套因子，保持原脚本的 6 个日历年滚动训练窗口及每 26 个日历周重训规则。XGBoost 明确指定 `rolling`，避免原脚本默认 `both` 引入额外模式；Ranker 使用 `--phase all`，在新的运行目录中重新选参、冻结配置和评估，并使用随附的 baseline 文件。

所有新输出必须位于工程的 `runs/` 内。省略 `--output` 时生成带时间戳的新目录；指定的目录已存在时拒绝运行，请换一个新名称。新结果与 `reference_results/` 中的历史结果分开保存。

## 显式运行数据流程

数据入口支持以下步骤：

| `--step` | 执行内容 | 数据输入 |
|---|---|---|
| `download` | `fetch_and_clean.py`，下载并清洗行情 | 原脚本固定的股票池与日期范围 |
| `technical` | `build_technical_factors.py`，构建技术因子 | 本次工作区内复制的确认版数据 |
| `external` | `build_external_factors.py`，调用 SEC 财务采集并合并 FRED 宏观因子 | 本次工作区内复制的确认版数据 |
| `all` | 按 `download → technical → external` 顺序执行 | 同一次工作区内前一步的输出 |

只运行技术因子的例子：

```bash
python run.py data --step technical --output runs/technical_first --dry-run
python run.py data --step technical --output runs/technical_first
```

`external` 和 `all` 实际执行前需要设置 `SEC_USER_AGENT`，填写自己的应用名称和联系邮箱。以下为 macOS／Linux 示例，替换占位内容后再使用：

```bash
export SEC_USER_AGENT='YOUR_APP_NAME YOUR_CONTACT_EMAIL'
python run.py data --step all --output runs/data_first --dry-run
python run.py data --step all --output runs/data_first
```

每次实际运行会复制四个数据脚本和五个确认版数据文件到独立工作区。分别执行的 `download`、`technical`、`external` 是独立运行，不会自动接续上一次目录；需要连续处理时使用 `all`。原下载脚本的日期范围保持为 `2015-09-01` 至 `2026-09-01`（结束日不含），并非自动更新到今天。

下载和外部因子步骤需要网络，受数据源、访问频率与数据修订影响。新数据只保存在该次运行目录，不替换根目录 `data/`，也不会自动触发训练；训练入口继续使用已确认的共同训练表。

## 数据与实验边界

共同训练表是 `data/test_45_factors_weekly.csv`：66 只股票、27,651 行、522 个观测周，日期为 `2016-09-02` 至 `2026-08-28`。55 列中包含 45 个因子，其余为日期、股票、行情及标签字段。五包中该表的 SHA-256 均为：

```text
26e234363e83f2eaefe0ba787b6909be0999f6d4405fbf6ef2e2c7cb8b918d97
```

| 因子集合 | 含义 |
|---|---|
| 5 | 五个财务基本面因子 |
| 7 | 财务因子与技术因子混合的七因子集合 |
| 11（脚本名 `7_macro`） | 上述七因子加四个宏观因子 |
| 45 | 共同训练表中的全部 45 个因子 |

5 因子与 7 因子不是逐项包含关系。具体列名以各模型脚本中的 `FIVE`、`SEVEN` 和 `MACRO` 为准。6 年指每次拟合使用的历史训练窗口，不是回测持续时间。

当前仍保留原模型的选参边界：Random Forest／Ridge 使用 104 个 Development 信号周，XGBoost／XGBoostRanker 使用 105 个；本次整合没有统一或修复此差异。模型候选搜索预算也不同，不能仅凭同一输入数据就认定四者是严格等条件比较。

`reference_results/` 中的六个 CSV 是历史汇总结果，未在本次整合中重新计算或验证性能。五包没有随附原运行的完整冻结配置与逐股逐周预测记录，不能依靠这些汇总表完成原实验的严格复现或统一回测。原模型说明中的结果与运行环境陈述属于原交付记录，请结合上述边界阅读。

## 本次整合检查

已逐字节核对五个 ZIP 的全部 27 个有效文件成员与整合后的 23 个原文件；静态检查通过。统一入口的 11 项测试通过，覆盖目录搬移、中文与空格路径、原文件变动拦截、输出防覆盖、依赖预检、执行顺序和失败记录。执行相关测试只调用临时的简单替身脚本，不执行原模型或数据下载脚本。

可用 Python 标准库重新运行这些测试：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

本次验证记录在 `integration/verification.json`。这些检查证明整合入口及文件保护符合预期；完整训练、数据采集和历史指标复现尚未验证。
