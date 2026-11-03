# SafeCapital Dashboard 1.4 — 中文安装与交付说明

交付修订日期：2026-11-03。英文客户入口在包根目录 [START_HERE.md](../../START_HERE.md)，两种包都包含。当前模块可独立演示，并提供 iframe 和只读 API；客户网站的实际部署和认证接入仍需双方联调。

## 1. 先确认收到哪一种包

| 包 | 包含内容 | 启动 Dashboard 的要求 |
|---|---|---|
| `SafeCapital-Source-1.4.0-20261103.zip` | Git 跟踪的完整代码、数据集、冻结模型、报告、Dashboard 和文档 | Python 3.12（64 位）及 Node.js/npm；首次需要构建前端 |
| `SafeCapital-Web-1.4.0-20261103.zip` | Web 源码、已构建前端、匹配输入、已验证结果、模块快照、安装与校验工具 | Python 3.12（64 位）；无需 Node.js 和模型依赖 |

**根目录有 `install.py` 和 `DELIVERY_MANIFEST.json` 的是运行包。源码包没有这两个根目录文件，请按第 3 节安装。** 所有命令从解压后的包根目录执行；不要照搬开发者电脑路径或复制现有虚拟环境。不要直接打开 HTML 文件代替启动服务。

## 2. Web 运行包安装

先完整解压到新目录，打开终端，进入含 `START_HERE.md` 和 `install.py` 的目录。

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

安装器创建新的 `.venv-dashboard`，使用 `dashboard/requirements.txt` 安装锁定依赖，不覆盖已有环境。安装中断时，建议在新的解压目录重试。后续启动只需最后一条命令。

## 3. 完整源码 ZIP / Git checkout 安装

只运行 Dashboard 不需要安装根目录的研究依赖，也不需要重新训练或回放模型。

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

Node.js 使用 22 或满足前端依赖要求的更高版本。若要复现研究计算，另建研究环境，按根目录 `README.md` 安装其 `requirements.txt`，再运行 `python safecapital.py`。研究回放不是查看 Dashboard 的必需步骤。

## 4. 打开页面与演示

保持启动终端运行；Ctrl+C 停止。端口冲突时，在启动命令末尾添加 `--port 8001`，所有网址和验收命令同时改为 8001。

- 中文：<http://127.0.0.1:8000/?lang=zh#watchlist>
- 英文：<http://127.0.0.1:8000/?lang=en#watchlist>
- 嵌入入口示例：<http://127.0.0.1:8000/embed-example.html?lang=en>
- API 文档：<http://127.0.0.1:8000/api/docs>
- API 定义：<http://127.0.0.1:8000/api/openapi.json>

点击「重置演示」，再点击「载入演示示例」。2026-08-28 的 SCL 排名 1 且入选，TJX 排名 2 但未入选，CMG 排名 3 且入选。查看输入因子、排名、实际配置，切换日期并导出 CSV/JSON。选择关注股票不会改变原策略组合或收益。

完整历史策略为 210 周，初始资金 100000、期末约 149330.61，累计收益 49.33%、年化收益 10.44%、最大回撤 −24.88%。这些是已保存的历史模拟，不是实时持仓或未来收益承诺。详细步骤见 [中英文演示讲稿](PRESENTATION_SCRIPT_ZH_EN.md)。

`127.0.0.1` 只在启动服务的电脑上可用，不能作为客户远程访问网址；本地远程演示请共享屏幕。

## 5. API Key、联网和配置

**当前 Dashboard 和随附数据的冻结回放无需 API Key 或账号凭据。** 首次安装依赖需要联网，安装后的历史数据展示和 API 可在本地运行。Swagger 文档界面依赖外部 CDN；离线时查看 `/api/openapi.json` 或包内 `dashboard/docs/openapi.json`。

上游历史数据采集脚本是可选参考，不属于交付的复现起点；运行 SEC 采集脚本需自行设置 `SEC_USER_AGENT` 联系标识，它不是 API Key。交付包和录屏都不要包含实际密钥、密码、令牌或个人 `.env`。

运行包使用根目录 `config.toml`。源码包可将 `dashboard/config.example.toml` 复制成 `dashboard/config.toml`，然后用 `--config dashboard/config.toml` 启动。先校验未修改的包，再编辑配置。

| 配置 | 本地默认 | 用途 |
|---|---|---|
| host / port | 127.0.0.1 / 8000 | 监听地址与端口 |
| public_url | 空 | 后续正式 HTTPS 地址，建议独立域名根路径 |
| result_dir | 空 | 默认使用随包结果；指定时必须是完整有效回放目录 |
| embed_origins | 空 | 允许 iframe 嵌入的精确 origin |
| api_origins | 空 | 允许浏览器跨域查询 API 的精确 origin |

origin 包含协议、域名和必要端口，没有路径、尾部斜线或通配符，多项以逗号分隔。配置优先级为默认值 < TOML < `SAFECAPITAL_*` 环境变量 < CLI host/port。相对结果路径按配置文件目录解析。更新数据或配置后重启服务，刷新浏览器不会重新读取磁盘结果。

## 6. 后续接入客户网站

方式 A：由客户增加 Strategy Lab 入口卡片，使用 `/?embed=1&lang=en` 嵌入独立服务。配置本服务的 `embed_origins`，客户自己的 CSP 也需允许对应 `frame-src`。iframe 内调用 API 是同源请求，无需为此开放 API CORS。

方式 B：客户自己制作页面，调用 `/api/cs5_6_equity/v1`。先获取 `/runs` 的有效 ID，再查询输入、关注股票、持仓、图表与下载。跨域浏览器调用使用 `api_origins`。合同见 [API v1](API_V1.md) 和 [OpenAPI](openapi.json)，示例为 `dashboard/examples/client.mjs`。

模块保持独立，不读取客户页面的单资产选择器，不合并其他团队本体或覆盖全局路由。嵌入白名单不是登录保护；客户如要求登录访问，需由网关或后续认证层同时保护页面、API 和下载。本版没有 SSO、实时行情、任意数据上传、在线训练、个性化重算或交易执行。

Docker 和公网部署暂缓；仓库保留的旧 Docker 配方是参考，不属于本次验证的安装路线。客户需提供部署环境、实际域名、认证要求与 staging 环境，双方再验收真实网站接入及其他模块。

## 7. 验收与交付

服务启动后，另开终端，在运行包根目录执行：

```bash
python3.12 smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

源码包改用：

```bash
python3.12 dashboard/tools/smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

Windows 使用 `py -3.12`。全新包应返回 `status: passed` 和 `run_id: delivered`。如果开发目录中存在其他 runs，需把 `--expected-dir` 指向实际选中的结果或省略它。该检查覆盖真实输入、结果、关注股票、持仓、静态资源、错误与下载字节。

完整源码包使用 `RELEASE_MANIFEST.json` 校验；运行包使用 `DELIVERY_MANIFEST.json`，同时记录来源 Git 提交及文件身份。ZIP 校验值、最终环境验收报告随交付提供。历史功能验收见 [1.4 记录](PRESENTATION_VALIDATION.md)；不能将本地安装验收称为客户线上部署验收。

提交完整源码 ZIP、Web 运行 ZIP、英文说明、最终校验/验收报告，以及团队自行录制的视频。群消息英文模板见 [CLIENT_SUBMISSION_EN.md](CLIENT_SUBMISSION_EN.md)。软件更新请解压到新目录安装验收，保留旧包以便回滚。
