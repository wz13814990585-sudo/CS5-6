# SafeCapital Dashboard 1.4 — English-first delivery

[English](#readme-en) | [中文](#readme-zh)

<a id="readme-en"></a>

## English

Start with the [English installation and handoff guide](../START_HERE.md). It distinguishes the full **Source ZIP** from the prebuilt **Web ZIP**. No API key is needed for the delivered Dashboard or supplied-data replay. The initial interface is English; Chinese remains an optional language. Explicit URL choices and saved preferences take precedence over the default.

### What the module does

The React/TypeScript frontend and FastAPI backend serve an independent, read-only historical stock research module. It supports standalone access, iframe embedding and namespaced APIs. It does not train models, accept arbitrary uploads, run a new backtest, fetch live prices or execute trades.

- Select multiple stocks by ticker or company name from the 40 external evaluation stocks. Inspect five raw factors, model ranks/scores, component percentiles, strategy selection and actual weights together.
- Share a historical date across watchlist, allocation, rankings and output-aligned inputs; browse the complete input source on an independent date.
- Load/reset a reproducible SCL/TJX/CMG example and export the current selection as CSV or JSON. Watchlist preferences do not change the original portfolio or its returns.
- View original full-backtest account value, weekly return and drawdown; inspect all history, the final 52 weeks or final 156 weeks. Headline metrics always describe the full 210-week backtest.
- Browse 366 model signal dates, ranking pagination/search, verified run versions and provenance. Download original predictions, weekly capital, summary and verification files without rewriting their bytes.
- Switch English/Chinese while preserving active filters. Use `?lang=en` or `?lang=zh` to override a saved preference; embed mode accepts the same parameters.
- Handle loading, no-data and API errors, with request timeouts/retry and an iframe failure fallback. Missing values remain unavailable, not zero.

The portfolio module has an independent `cs5_6_equity` namespace. It preserves the 66-stock training / disjoint 40-stock external research scope, weekly signals, verified actual holdings and declared execution assumptions. A verified market benchmark and currency are unavailable. Raw model ranks are before strategy filtering and are not holdings.

### Local access

After installation, start from the extracted project root:

```bash
.venv-dashboard/bin/python dashboard/start.py
```

For the prebuilt Web package, append `--config config.toml`. On Windows use `.\.venv-dashboard\Scripts\python.exe` instead. Keep the terminal open and stop with Ctrl+C. Append `--port 8001` if port 8000 is occupied.

- [Dashboard](http://127.0.0.1:8000/?lang=en#watchlist)
- [Embedded mode](http://127.0.0.1:8000/?embed=1&lang=en)
- [Example host page](http://127.0.0.1:8000/embed-example.html?lang=en)
- [API documentation](http://127.0.0.1:8000/api/docs)
- [OpenAPI JSON](http://127.0.0.1:8000/api/openapi.json)

Localhost is only accessible on the computer running the service; it is not a public customer URL. The API documentation UI uses an external CDN; the local Dashboard and OpenAPI JSON do not need a live data service.

### First installation from source

Requirements: 64-bit Python 3.12 and Node.js/npm compatible with the pinned frontend dependencies (Node.js 22 or later supported version). Use a fresh extraction and run from the project root. The Dashboard environment is independent of the research environment.

macOS / Linux:

```bash
python3.12 tools/check_release.py
python3.12 -m venv .venv-dashboard
.venv-dashboard/bin/python -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python dashboard/start.py
```

Windows PowerShell:

```powershell
py -3.12 tools/check_release.py
py -3.12 -m venv .venv-dashboard
.\.venv-dashboard\Scripts\python.exe -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.\.venv-dashboard\Scripts\python.exe dashboard/start.py
```

For the prebuilt Web ZIP use its root `verify_delivery.py` / `install.py` instead; it needs no Node.js. Those root scripts are not present in the Source ZIP. Full instructions, configuration and troubleshooting are in [START_HERE](../START_HERE.md).

### Results and updates

Startup scans `runs/` and the tracked `FINAL_OUTPUTS/01_saved_model_replay/verified_replay/`. Only completed `frozen_model_inference` runs with passed verification, matching file hashes, row counts and coverage are accepted. Training runs are not served. Corrupt runs are skipped and counted; if no valid result exists, the service reports unavailable rather than generating data.

A development checkout selects its latest valid replay. A fresh source/Web package uses the included `delivered` result. The local run and delivered replay have equal numerical results but different run timestamps and file identities. Always obtain the actual ID through `/api/cs5_6_equity/v1/runs`.

Verified results and downloads are held in the same in-memory snapshot. Restart after changing disk data; browser refresh does not rescan it. To select a specific complete replay, use `result_dir` in TOML or `SAFECAPITAL_RESULT_DIR`. Invalid explicit configuration fails rather than silently substituting another run. Hash verification establishes file consistency, not a third-party digital signature.

### APIs and integration

New clients use **`/api/cs5_6_equity/v1`**. `/api/v1` and `/api` are compatibility aliases. All business endpoints are read-only GET. Start with `runs`, then query `stocks`, `watchlist`, `inputs`, `portfolio`, `overview`, `equity`, `rankings` or downloads for that run. Human-readable API labels/reasons are English; identifiers, numerical values and original downloads remain stable. The optional Chinese UI translates those display labels locally.

See [API contract](docs/API_V1.md), [watchlist API](docs/PRESENTATION_WATCHLIST.md), [OpenAPI](docs/openapi.json) and [integration handoff](docs/PORTFOLIO_NEO_INTEGRATION.md).

For iframe use, host on a dedicated HTTPS origin, configure exact `embed_origins`, and have the client allow the module in its `frame-src` CSP. The module uses `frame-ancestors`; avoid conflicting proxy X-Frame-Options headers. iframe API requests are same-origin. A different-origin client frontend calling JSON directly needs its exact origin in `api_origins`.

No login/SSO is implemented. An embed/CORS allowlist is not authentication. If required, the client gateway must protect pages, APIs and downloads together. Client hosting, domain, authentication, staging regression and production release are separate responsibilities. Docker and public deployment remain deferred; old Docker recipes are reference material and are not a validated route for the current input/portfolio package.

### Development, packaging and evidence

Run the backend, then `npm --prefix dashboard/frontend run dev` for Vite development; it proxies `/api` to port 8000. Rebuild the frontend before serving changed source through Python.

```bash
.venv-dashboard/bin/python -m pip install -r dashboard/requirements-test.txt
.venv-dashboard/bin/python -m unittest discover -s dashboard/tests -v
node --experimental-strip-types --test dashboard/frontend/tests/*.test.ts
npm --prefix dashboard/frontend run build
```

Web packaging requires a Git checkout, Dashboard dependencies and built frontend; it is not a client installation command. The package contains the root English guide, frontend/server source, prebuilt assets, pinned dependencies, matched inputs, module snapshots, verified results and validation tools. It excludes the complete training environment and refuses to overwrite existing archives. See [build instructions](docs/DELIVERY_BUILD.md).

Further reading: [input/output guide](docs/LOCAL_IO.md), [English presentation script](docs/PRESENTATION_SCRIPT_EN.md), [demo guide](docs/CUSTOMER_DEMO_GUIDE.md), [language policy](docs/LANGUAGE_SUPPORT.md), [1.4 feature validation](docs/PRESENTATION_VALIDATION.md), [development plan](docs/DEVELOPMENT_PLAN.md). Earlier validation documents are dated historical records, not claims that all checks were rerun for every revision.

---

<a id="readme-zh"></a>

## 中文

请先阅读[英文安装与交付指南](../START_HERE.md)，区分完整 **Source 源码 ZIP** 与已构建的 **Web 运行 ZIP**。运行所交付的 Dashboard 或基于随附数据进行回放不需要 API Key。界面首次默认英文，中文可选；显式 URL 语言参数和已保存偏好优先于默认值。

### 模块功能

React/TypeScript 前端与 FastAPI 后端共同提供独立、只读的历史股票研究模块，支持独立访问、iframe 嵌入和独立命名空间 API。它不会训练模型、接收任意上传文件、重新运行回测、获取实时行情或执行交易。

- 从 40 只外部评估股票中，按股票代码或公司名称选择多只关注股票，在同一视图查看五个原始因子、模型排名/分数、组件百分位、策略入选状态和实际权重。
- 在关注列表、配置、排名及输出对齐输入间共用历史日期；完整输入源数据可以独立选择日期浏览。
- 加载或重置可复现的 SCL/TJX/CMG 示例，并将当前选择导出为 CSV 或 JSON。关注偏好不改变原始组合和收益。
- 查看原始完整回测的账户价值、每周收益和回撤，支持全部历史、最后 52 周或最后 156 周视图。页面主要指标始终对应完整 210 周回测。
- 浏览 366 个模型信号日期、排名分页/搜索、已验证运行版本和来源；下载预测、每周资金、汇总与验证原文件，不改写其字节。
- 保留当前筛选条件进行中英文切换。使用 `?lang=en` 或 `?lang=zh` 覆盖已保存偏好，嵌入模式使用相同参数。
- 处理加载中、无数据及 API 错误，支持请求超时/重试和 iframe 失败后的备用入口。缺失值显示不可用，不当作零。

组合模块拥有独立的 `cs5_6_equity` 命名空间，保留 66 股训练池、与其不重叠的 40 股外部研究池、周度信号、已验证实际持仓及明确的执行假设。没有已验证的市场基准序列或明确币种。原始模型排名位于策略过滤之前，不等于持仓。

### 本地访问

安装完成后，在解压后的项目根目录启动：

```bash
.venv-dashboard/bin/python dashboard/start.py
```

预构建 Web 包应追加 `--config config.toml`。Windows 使用 `.\.venv-dashboard\Scripts\python.exe`。保持终端运行，用 Ctrl+C 停止；8000 端口被占用时追加 `--port 8001`。

- [英文 Dashboard](http://127.0.0.1:8000/?lang=en#watchlist)
- [中文 Dashboard](http://127.0.0.1:8000/?lang=zh#watchlist)
- [嵌入模式](http://127.0.0.1:8000/?embed=1&lang=en)
- [示例宿主页](http://127.0.0.1:8000/embed-example.html?lang=en)
- [API 文档](http://127.0.0.1:8000/api/docs)
- [OpenAPI JSON](http://127.0.0.1:8000/api/openapi.json)

localhost 仅能在运行服务的电脑上访问，不是可交给客户直接打开的公网地址。API 文档界面使用外部 CDN；本地 Dashboard 和 OpenAPI JSON 不依赖实时数据服务。

### 首次从源码安装

需要 64 位 Python 3.12，以及兼容固定前端依赖的 Node.js/npm（Node.js 22 或更新的受支持版本）。从全新解压目录开始，在项目根目录执行。Dashboard 环境独立于研究环境。

macOS / Linux：

```bash
python3.12 tools/check_release.py
python3.12 -m venv .venv-dashboard
.venv-dashboard/bin/python -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python dashboard/start.py
```

Windows PowerShell：

```powershell
py -3.12 tools/check_release.py
py -3.12 -m venv .venv-dashboard
.\.venv-dashboard\Scripts\python.exe -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.\.venv-dashboard\Scripts\python.exe dashboard/start.py
```

预构建 Web ZIP 应改用其根目录下的 `verify_delivery.py` / `install.py`，不需要 Node.js。Source 源码 ZIP 的根目录没有这两个脚本。完整命令、配置与故障处理见 [START_HERE](../START_HERE.md)。

### 结果与更新

启动时扫描 `runs/` 与已纳入版本控制的 `FINAL_OUTPUTS/01_saved_model_replay/verified_replay/`。仅接收已完成、验证通过，且文件哈希、行数及覆盖范围一致的 `frozen_model_inference` 运行；训练运行不展示。损坏运行会被跳过并计数；若没有有效结果，服务返回不可用，不生成替代数据。

开发目录选择最新的有效回放；全新的 Source/Web 包使用随附的 `delivered` 结果。本地运行与交付回放的数值一致，但运行时间与文件身份不同。始终通过 `/api/cs5_6_equity/v1/runs` 获取实际 ID。

已验证结果和下载内容来自同一份内存快照。磁盘数据改变后需重启服务，浏览器刷新不会重新扫描。可通过 TOML 的 `result_dir` 或 `SAFECAPITAL_RESULT_DIR` 指定某次完整回放。显式配置无效时会报错，不会静默换用其他运行。哈希核验用于检查文件一致性，不是第三方数字签名。

### API 与接入

新客户使用 **`/api/cs5_6_equity/v1`**，`/api/v1` 与 `/api` 仅是兼容别名。所有业务接口均为只读 GET。先查询 `runs`，再查询对应运行的 `stocks`、`watchlist`、`inputs`、`portfolio`、`overview`、`equity`、`rankings` 或下载接口。API 可读标签和原因说明使用英文，标识符、数值与原始下载内容保持稳定；可选中文界面在本地翻译这些展示标签。

参阅 [API 约定](docs/API_V1.md)、[关注列表 API](docs/PRESENTATION_WATCHLIST.md)、[OpenAPI](docs/openapi.json) 和[接入交付说明](docs/PORTFOLIO_NEO_INTEGRATION.md)。

iframe 接入需要将服务部署到独立 HTTPS 来源，配置精确的 `embed_origins`，并让客户在自身 CSP 的 `frame-src` 中允许该模块。模块使用 `frame-ancestors`，应避免代理层配置冲突的 X-Frame-Options。iframe 内的 API 请求同源；若客户前端从不同来源直接调用 JSON，则需在 `api_origins` 中加入精确来源。

当前没有登录/SSO。嵌入和 CORS 来源白名单不是身份认证。若需要权限控制，客户网关必须同时保护页面、API 和下载。客户托管、域名、认证、预发布回归与生产发布属于单独的接入工作。Docker 和公网部署暂缓；旧 Docker 示例仅供参考，尚不是当前输入/组合交付包已验证的安装路径。

### 开发、打包与验证材料

先启动后端，再运行 `npm --prefix dashboard/frontend run dev` 进入 Vite 开发模式，其 `/api` 代理指向 8000 端口。修改前端源码后，需重新构建，Python 服务才会提供新的前端文件。

```bash
.venv-dashboard/bin/python -m pip install -r dashboard/requirements-test.txt
.venv-dashboard/bin/python -m unittest discover -s dashboard/tests -v
node --experimental-strip-types --test dashboard/frontend/tests/*.test.ts
npm --prefix dashboard/frontend run build
```

Web 打包需要 Git 工作副本、Dashboard 依赖和已构建前端，不是客户安装步骤。包内包含根目录英文指南、前后端源码、预构建资源、固定依赖、匹配输入、模块快照、验证结果及校验工具；不包含完整训练环境，也不会覆盖已存在的压缩包。详见[打包说明](docs/DELIVERY_BUILD.md)。

更多资料：[输入输出指南](docs/LOCAL_IO.md)、[英文演示讲稿](docs/PRESENTATION_SCRIPT_EN.md)、[演示指南](docs/CUSTOMER_DEMO_GUIDE.md)、[语言策略](docs/LANGUAGE_SUPPORT.md)、[1.4 功能验证](docs/PRESENTATION_VALIDATION.md)、[开发计划](docs/DEVELOPMENT_PLAN.md)。较早的验证文档是有日期的历史记录，不代表每次修订都重新执行了其中所有检查。
