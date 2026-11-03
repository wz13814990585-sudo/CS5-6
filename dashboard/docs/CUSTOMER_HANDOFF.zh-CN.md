# 客户交付 — 安装与接入速查

[English](CUSTOMER_HANDOFF.md) | **中文**

Dashboard 1.4.0，语言切换交付修订 2026-11-03-language-switch。完整中文指南位于两种包根目录的 [START_HERE.zh-CN.md](../../START_HERE.zh-CN.md)。本页为安装速查，顶部链接可切换到对应英文页。

## 选择正确的安装流程

| 包类型 | 用途 | 要求 |
|---|---|---|
| Source 源码 ZIP | 完整代码、数据、模型、报告和 Dashboard 源码 | Python 3.12，加 Node.js/npm 构建前端 |
| Web 运行 ZIP | Dashboard 源码、预构建前端、匹配输入和已验证结果 | 仅 Python 3.12 |

Web 根目录有 `install.py`、`verify_delivery.py`、`config.toml` 和 `DELIVERY_MANIFEST.json`，Source 没有这些根目录安装文件。请解压到新目录并在根目录打开终端，不要复制其他电脑的虚拟环境。

## Web 运行包

macOS / Linux：

```bash
python3.12 verify_delivery.py
python3.12 install.py
.venv-dashboard/bin/python dashboard/start.py --config config.toml
```

Windows PowerShell：

```powershell
py -3.12 verify_delivery.py
py -3.12 install.py
.\.venv-dashboard\Scripts\python.exe dashboard/start.py --config config.toml
```

安装器检查文件、创建新环境并下载固定依赖，不覆盖已存在环境。后续仅需启动命令。保持终端打开，Ctrl+C 停止；端口被占用时加 `--port 8001`，同时修改所有访问地址。

## Source 源码包

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

研究复现使用根目录单独的 `requirements.txt` 和 README 流程。查看随附 Dashboard 结果不需要运行研究计算。

## 演示与验证

打开 <http://127.0.0.1:8000/?lang=en#watchlist>。首次默认英文，显式 URL 或已保存语言会覆盖默认。点击 **Reset demo** 再点 **Load demo example**：2026-08-28 时 SCL 排名 1 且入选，TJX 排名 2 但未入选，CMG 排名 3 且入选。更改关注列表不重新计算组合收益。逐步操作与讲解见[英文演示讲稿](PRESENTATION_SCRIPT_EN.md)。

示例宿主页为 <http://127.0.0.1:8000/embed-example.html?lang=en>。API 文档位于 `/api/docs`；`/api/openapi.json` 和随包 OpenAPI 不依赖 Swagger UI CDN。localhost 不是客户可直接访问的公网地址。

服务运行后，在另一终端执行 Web 验收：

```bash
python3.12 smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

Source 改用 `dashboard/tools/smoke_check.py`；Windows 使用 `py -3.12`。全新包应显示 `status: passed` 和 `run_id: delivered`。开发目录若有其他运行，应指定实际被选择的结果目录，或省略 `--expected-dir`。

## 密钥与配置

所交付 Dashboard 和随附数据回放不需要 API Key 或凭据。安装需要网络，安装后的本地数据浏览不需要实时数据源。可选 SEC 上游采集需要用户自己的 `SEC_USER_AGENT` 联系标识，不是 API Key，也不属于必需流程。不要提交真实凭据或个人 `.env`。

Web 编辑根目录 `config.toml`；Source 将 `dashboard/config.example.toml` 复制为 `dashboard/config.toml` 并加 `--config dashboard/config.toml` 启动。先核验未经修改的包，再改配置。

- `host` / `port`：本地默认 127.0.0.1 / 8000。
- `public_url`：未来的独立 HTTPS 来源，本地留空。
- `result_dir`：完整已验证回放，留空选择随附或发现的结果。
- `embed_origins`：允许嵌入模块的精确来源。
- `api_origins`：允许浏览器发起 API 请求的精确来源。

来源包括协议、主机及可选端口，不包含路径、通配符或结尾斜杠；多个来源以逗号分隔。优先级为默认值 < TOML < `SAFECAPITAL_*` 环境变量 < CLI host/port。相对结果路径以配置文件为基准。修改磁盘结果或配置后重启。

## 客户接入与限制

使用 iframe 或只读 `/api/cs5_6_equity/v1` API。先从 `/runs` 获取 `default_run_id`，不要写死开发者运行 ID。详见 [API 约定（英文）](API_V1.md)、[OpenAPI](openapi.json) 和[接入说明（英文）](PORTFOLIO_NEO_INTEGRATION.md)。

模块的股票池、标识符、本体及引擎应独立于客户全局资产选择器和其他团队。iframe 需要双方兼容的 CSP；不同来源的前端调用 API 需要配置 `api_origins`。来源白名单不是登录保护；如需限制访问，网关或后续认证层必须共同保护页面、API 和下载。

当前没有实时行情、上传、在线训练/推断、个性化组合重算、交易或 SSO。Docker/公网部署暂缓，保留的 Docker 示例不是已验证安装路径。客户托管、精确域名、认证和预发布回归需与客户核心团队确认。

交付两个 ZIP、安装指南、验证报告/校验文件及单独录制的视频。[英文提交消息](CLIENT_SUBMISSION_EN.md) 是草稿，并未发送。哈希用于完整性检查，不是数字签名。升级时使用新目录并核验，保留旧包用于回退。
