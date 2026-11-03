# SafeCapital — 客户交付与安装指南

[English](START_HERE.md) | **中文**

**团队：**CS5-6 · **Dashboard 版本：**1.4.0 · **交付修订：**2026-11-03-language-switch

本交付提供 Portfolio Neo / Strategy Lab 的独立研究模块 **Model-Based Stock Strategies**，包含默认英文、支持中文切换的 Dashboard、只读输入输出 API，以及已验证的历史结果。Dashboard 可独立运行或嵌入 iframe。实际接入客户网站仍需确认客户的托管与认证安排。

**运行所交付的 Dashboard，或回放随附的冻结研究结果，都不需要 API Key。** 安装时会下载依赖；Dashboard 使用本地随附数据，不调用实时行情或 AI 服务。

界面首次默认英文，显式 URL 参数或已保存的中文偏好优先。演示时可使用 `?lang=en` 强制英文。API 展示标签和错误信息为英文。所有 22 组 README 均拆成独立英文页和中文页，点击页面顶部链接切换，不再将两种语言上下排列。完整目录见[中文 README](README.zh-CN.md#readme-index)。本安装指南也采用相同切换方式。

## 1. 选择交付包

| 交付包 | 内容 | 启动 Dashboard 的要求 |
|---|---|---|
| `SafeCapital-Source-1.4.0-20261103-language-switch.zip` | 完整版本控制项目：研究代码、随附数据、保存模型、报告、Dashboard 源码和文档 | 64 位 Python 3.12、前端依赖支持的 Node.js 22 或更新版本及 npm；首次需构建前端 |
| `SafeCapital-Web-1.4.0-20261103-language-switch.zip` | Dashboard 源码与预构建前端、匹配输入、已验证结果、模块快照、安装工具和文档 | 64 位 Python 3.12；无需 Node.js、模型库或训练 |

最快的体验方式是 **Web 运行包**。完整代码审阅或研究复现应使用 **Source 源码包**。Web 不包含完整训练项目，不能替代源码交付。

将 ZIP 解压到新目录，在包含本文件的最外层目录打开终端，不要在 ZIP 查看器中直接运行。源码 ZIP 不包含 `.git`、虚拟环境、`node_modules` 或预构建前端；不要从其他电脑复制虚拟环境。

**识别包类型：**Web 根目录包含 `install.py`、`verify_delivery.py`、`config.toml` 和 `DELIVERY_MANIFEST.json`；Source 根目录则包含 `safecapital.py`、`tools/check_release.py` 和 `RELEASE_MANIFEST.json`。仅执行对应类型的安装步骤。

## 2. Web 运行包：安装与启动

### macOS / Linux

```bash
python3.12 --version
python3.12 verify_delivery.py
python3.12 install.py
.venv-dashboard/bin/python dashboard/start.py --config config.toml
```

### Windows PowerShell

```powershell
py -3.12 --version
py -3.12 verify_delivery.py
py -3.12 install.py
.\.venv-dashboard\Scripts\python.exe dashboard/start.py --config config.toml
```

安装器核验文件，创建新的 `.venv-dashboard`，并安装 `dashboard/requirements.txt` 中的固定依赖。它不会覆盖现有环境。安装中断时请重新解压一份再试，不要在完整源码项目中运行此安装器。

使用 Dashboard 时保持终端打开。后续启动只需最后一条命令，按 **Ctrl+C** 停止。若 8000 端口被占用，在启动命令后加 `--port 8001`，浏览器和检查命令也改用 8001。

## 3. Source 源码包：安装与启动 Dashboard

本节适用于完整源码 ZIP 或 GitHub 工作副本。源码根目录没有第 2 节的 `install.py`。本流程不安装研究/模型依赖，也不重新训练或回放模型。

### macOS / Linux

```bash
python3.12 --version
node --version
npm --version
python3.12 tools/check_release.py
python3.12 -m venv .venv-dashboard
.venv-dashboard/bin/python -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python dashboard/start.py
```

### Windows PowerShell

```powershell
py -3.12 --version
node --version
npm --version
py -3.12 tools/check_release.py
py -3.12 -m venv .venv-dashboard
.\.venv-dashboard\Scripts\python.exe -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.\.venv-dashboard\Scripts\python.exe dashboard/start.py
```

在全新解压目录执行。首次成功后，仅需最后一条启动命令。修改前端源码后需再次运行 `npm --prefix dashboard/frontend run build`。

如需复现研究计算，请使用**根目录 README 中单独的研究环境和说明**。研究的 `requirements.txt` 与 Dashboard 的依赖不同。研究环境中的完整冻结回放命令为 `python safecapital.py`；仅查看已交付的 Dashboard 结果不需要执行。原始数据采集不属于本交付的复现流程。

## 4. 打开并验证

| 页面 | 本地地址 |
|---|---|
| 英文 Dashboard | <http://127.0.0.1:8000/?lang=en#watchlist> |
| 中文 Dashboard | <http://127.0.0.1:8000/?lang=zh#watchlist> |
| iframe 入口演示 | <http://127.0.0.1:8000/embed-example.html?lang=en> |
| 交互式 API 文档 | <http://127.0.0.1:8000/api/docs> |
| 不依赖文档界面的 OpenAPI JSON | <http://127.0.0.1:8000/api/openapi.json> |
| 模块健康状态 | <http://127.0.0.1:8000/api/cs5_6_equity/v1/health> |

`127.0.0.1` 指运行服务器的电脑，不是其他人可直接访问的公网链接。远程本地演示可共享屏幕。直接打开 `index.html` 不会启动 API 服务。

在 **Watchlist** 中点击 **Reset demo**，再点击 **Load demo example**。历史日期 **2026-08-28** 下，SCL 排名 1 且入选，TJX 排名 2 但未入选，CMG 排名 3 且入选。可以查看因子和实际配置、切换历史日期，并下载当前选择的 CSV/JSON。选择关注股票只改变视图，不改变策略或收益。

完整原始策略覆盖 2022-08-26 至 2026-08-28 的 210 个信号周：初始资金 100000，最终资金约 149330.61，总收益 49.33%，年化收益 10.44%，最大回撤 −24.88%。这些是已保存的历史模拟结果，不是实时持仓或预测。随附结果没有独立确认的基准和币种，因此显示不可用。

服务运行后，在同一包根目录打开另一终端，执行对应检查。

**Web 包：**

```bash
python3.12 smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

**全新 Source 包：**

```bash
python3.12 dashboard/tools/smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

Windows 将 `python3.12` 改为 `py -3.12`。检查仅依赖 Python 标准库，核验页面资源、真实输入、持仓、关注列表、原始指标、错误处理和下载字节。全新未修改包应返回 `"status": "passed"` 与 `"run_id": "delivered"`。开发目录有其他运行时，可省略 `--expected-dir`，或指向实际被选中的运行目录。

如安装了 Node.js，还可执行更详细的 API 示例：

```bash
node dashboard/examples/verify-watchlist.mjs http://127.0.0.1:8000/
```

## 5. API Key、配置与网络

| 项目 | 要求 |
|---|---|
| Dashboard / 随附数据回放 | 不需要 API Key、云账号或实时数据源 |
| 安装依赖 | 需要访问 Python/npm 包仓库 |
| 安装完成后的 Dashboard | 本地历史浏览和 API 不依赖实时数据服务 |
| 交互式 `/api/docs` | Swagger UI 资源使用外部 CDN；不可用时打开 `/api/openapi.json` 或随包的 `dashboard/docs/openapi.json` |
| 可选上游 SEC 采集脚本 | 需要用户自己的 `SEC_USER_AGENT` 联系标识和网络；这不是 API Key，交付 Dashboard/回放不需要它 |
| 应用登录 / SSO | 未实现；当前 API 没有 API Key 身份认证 |

提交资料中不要包含真实密钥、令牌、密码、个人 `.env` 或凭据。示例域名与联系标识只是占位内容。

**Web 包：**先核验和安装，再编辑根目录 `config.toml`。**Source 包：**将 `dashboard/config.example.toml` 复制为 `dashboard/config.toml`，以 `--config dashboard/config.toml` 启动。不提供配置时，源码使用本地默认值。

```toml
host = "127.0.0.1"
port = 8000
public_url = ""
result_dir = ""
embed_origins = ""
api_origins = ""
```

`public_url` 是未来独立 HTTPS 来源，本地留空。`result_dir` 指定完整已验证回放，留空使用随附结果，相对路径以配置文件为基准。`embed_origins` 控制允许嵌入的网站；`api_origins` 单独控制跨来源浏览器 API 读取。二者均接受精确来源列表，以逗号分隔，包含协议及可选端口，不含路径、结尾斜杠或通配符。

优先级：默认值 → TOML → `SAFECAPITAL_*` 环境变量 → CLI 的 host/port。编辑配置后不再匹配原包校验码，应先核验原包，再记录有意修改。磁盘数据或配置改变后重启服务，浏览器刷新不会重新加载磁盘结果。

## 6. 接入 Portfolio Neo / Strategy Lab

客户可在现有 Strategy Lab 选项旁增加 **Model-Based Stock Strategies** 卡片或标签。模块的多股票池应独立于客户页面的单资产选择器；研究引擎、数据、标识符和本体保留在独立 `cs5_6_equity` 命名空间中。

### 方案 A：iframe

在独立 HTTPS 来源托管服务，然后嵌入：

```html
<iframe
  src="https://research.example.com/?embed=1&lang=en"
  title="Model-Based Stock Strategies"
  width="100%"
  height="1400"
  style="border:0;border-radius:16px"
  loading="lazy">
</iframe>
```

替换示例域名，按真实来源配置 `public_url` 与 `embed_origins`。客户 CSP 的 `frame-src` 必须允许 Dashboard；模块提供 `frame-ancestors` 策略。避免代理层冲突的 `X-Frame-Options`。iframe 内 API 同源，不需要 API CORS。本地入口示例包含加载、就绪、重试和独立访问备用入口。

### 方案 B：客户前端调用 API

使用只读命名空间 **`/api/cs5_6_equity/v1`**。先请求 `/runs`，读取 `default_run_id`，再请求对应 ID 的数据；不要写死开发者本地运行 ID。

```text
GET /api/cs5_6_equity/v1/runs
GET /api/cs5_6_equity/v1/runs/{run_id}/stocks
GET /api/cs5_6_equity/v1/runs/{run_id}/inputs
GET /api/cs5_6_equity/v1/runs/{run_id}/watchlist?date=2026-08-28&tickers=SCL,TJX,CMG
GET /api/cs5_6_equity/v1/runs/{run_id}/portfolio?date=2026-08-28
GET /api/cs5_6_equity/v1/runs/{run_id}/overview
GET /api/cs5_6_equity/v1/runs/{run_id}/equity
```

不同来源的浏览器前端调用 API 时需配置 `api_origins`。接口定义和示例见 [OpenAPI](dashboard/docs/openapi.json)、[API 指南（英文）](dashboard/docs/API_V1.md)及 [JavaScript 客户端](dashboard/examples/client.mjs)。`null` 表示不可用，不是零；收益和权重使用小数比例。应读取结果及各字段状态。原始模型排名在策略过滤之前，不等于入选持仓。

来源白名单**不是身份认证**。如果客户需要登录，其网关或后续认证层必须同时保护页面、API 和下载。生产上线前应确认托管、来源、访问控制、责任归属和预发布验收。Docker 与公网部署不是本交付前置要求，也不是其已验证安装路径；旧 Docker 示例仅供参考。

## 7. 范围与证据

研究范围为 66 只训练股票和 40 只独立外部评估股票，无 ETF。策略使用周度信号、三个冻结组件、最多五个持仓、13 周历史收益过滤、整数股交易及每边 10 基点费用。执行采用历史次周开盘/收盘代理价，最后一个持有期结束时清仓。Dashboard 不保证财务信息的时点可得性、真实次开盘成交或历史 S&P 500 成分资格。

当前不提供任意股票池、数据上传、在线推断/训练、个性化组合重算、实时行情、真实交易或客户 SSO。关注列表是浏览器本地偏好，不是服务器端账号数据；不会推断缺失的逐股排除原因。

随包最终验证报告记录两个 ZIP 的实际验证平台和命令。早期功能证据见 [Dashboard 1.4 验证（英文）](dashboard/docs/PRESENTATION_VALIDATION.md)。本地入口只是接入模拟，不证明已部署客户网站。提供 Windows/Linux 命令，但实际平台覆盖以验证报告为准，不声称已验证未经执行的平台或客户生产环境。

## 8. 常见问题

| 现象 | 处理 |
|---|---|
| 找不到 `python3.12` / `py -3.12` | 安装 64 位 Python 3.12 并重新打开终端，不要替换为未经验证的版本 |
| 找不到 `install.py` | 可能是 Source 源码包，请按第 3 节操作 |
| `Frontend build missing` | Source 包执行前述 `npm ci` 和 `npm run build`；Web 包应核验并重新解压原 ZIP |
| 依赖下载失败 | 检查网络/代理，保留固定依赖版本，在新解压目录重试 |
| 地址已被占用 | 加 `--port 8001`，所有浏览器和检查地址也改为该端口 |
| 页面打开但没有已验证结果 | 检查是否完整解压、原始清单及 `result_dir` 覆盖配置，不用虚构数据替代 |
| API 文档空白 | 打开 `/api/openapi.json`；CDN 是否可用不影响本地 API |
| 别人无法打开 localhost | 在对方电脑运行、共享屏幕，或安排获授权的托管地址 |
| iframe 被阻止 | 检查双方 CSP、精确允许来源和代理响应头 |
| 编辑后文件核验失败 | 与全新解压副本比较，区分有意配置变化和文件损坏 |

## 9. 提交清单与补充资料

提供完整源码 ZIP、可选预构建 Web ZIP、本指南、验证报告/校验文件，以及团队单独录制的视频。提交时标明最终 Git 提交；源码 ZIP 从该提交导出，Git 历史仍在仓库中。ZIP 哈希用于完整性检查，不是数字签名。

- [英文提交消息模板](dashboard/docs/CLIENT_SUBMISSION_EN.md)
- [英文演示讲稿](dashboard/docs/PRESENTATION_SCRIPT_EN.md)
- [中文安装速查](dashboard/docs/CUSTOMER_HANDOFF.zh-CN.md)
- [功能与接口演示（英文）](dashboard/docs/PRESENTATION_WATCHLIST.md)
- [接入范围与研究来源（英文）](dashboard/docs/PORTFOLIO_NEO_INTEGRATION.md)

仓库：<https://github.com/wz13814990585-sudo/CS5-6>
