# SafeCapital Dashboard V1.2

当前重点是本地查看真实输入和输出，以及交付查询接口。Docker 和公网部署暂缓。先看 [本地输入输出使用指南](docs/LOCAL_IO.md) 与 [本次验收](docs/LOCAL_IO_VALIDATION.md)。

**客户交付入口：**[客户演示操作与讲解稿](docs/CUSTOMER_DEMO_GUIDE.md) · [完整计划](docs/DEVELOPMENT_PLAN.md) · [客户安装与接入手册](docs/CUSTOMER_HANDOFF.md) · [API v1 合同](docs/API_V1.md) · [本次交付验收](docs/DELIVERY_VALIDATION.md)。

支持 `--config dashboard/config.toml`，模板为 `dashboard/config.example.toml`。新集成使用 `/api/v1`，旧 `/api` 继续兼容。前端通过运行配置生成公开域名下的嵌入代码。

构建客户 ZIP（需要先构建前端）：

```bash
.venv-dashboard/bin/python dashboard/tools/build_delivery.py
```

默认输出到 `deliveries/`，包含预构建页面、服务端源码、完整依赖锁、最新验证通过的真实结果、与结果匹配的两份输入 CSV 及配置/清单、配置、校验工具和安装说明。默认拒绝覆盖已有 ZIP；再次构建用 `--output` 指定新文件名。客户运行无需 Node.js 或模型环境。

中文、只读的历史策略 Dashboard。React + TypeScript 前端，FastAPI 后端，同一个服务提供页面与 API。支持独立访问和 iframe 嵌入，无需客户网站使用相同的前端框架。

## 已实现

- 模型五个原始因子、历史回测价格浏览，日期/股票过滤与分页，完整输入下载。
- 完整源文件与当前输出覆盖范围分开显示；点击“查看输出”按日期和股票关联排名。
- 输入查询地址复制、JSON 查看、字段说明和文件 SHA-256。

- 真实回测总览、账户资金 / 每周收益 / 历史回撤曲线；切换全部、末 52 周、末 156 周。
- 366 个信号日期可选；股票代码搜索、排名分页、三组件百分位与集成得分。
- 历史结果版本选择、来源说明、运行时间和验证状态。
- 原始排名、资金、汇总 CSV 和 manifest JSON 下载。
- `/?embed=1` 隐藏外层导航与接入说明；`/embed-example.html` 提供可交互的 iframe 示例。
- 窄屏布局、移动导航、加载 / 空搜索 / 请求失败状态。

这是历史结果展示服务，不是实时选股、交易执行、任意数据上传或在线训练服务。排名是策略过滤前的结果，不等同于实际持仓。资金数值使用原始回测计价单位，页面不另行假定币种。

## 在当前 Mac 上启动

在项目根目录运行（已安装独立环境并完成前端构建）：

```bash
.venv-dashboard/bin/python dashboard/start.py
```

保持终端运行，浏览器打开：

- 独立页面：<http://127.0.0.1:8000/>
- 嵌入模式：<http://127.0.0.1:8000/?embed=1>
- 模拟客户页面：<http://127.0.0.1:8000/embed-example.html>
- API 文档：<http://127.0.0.1:8000/api/docs>

按 Ctrl+C 停止。端口冲突时添加 `--port 8001`，然后用新的端口访问。地址 `127.0.0.1` 只在当前电脑可访问，不是客户可访问的公网地址。

## 新电脑首次安装

要求 Python 3.12、Node.js 22 LTS 和 npm。Dashboard 使用独立环境，不需要安装 XGBoost 或重新运行模型。

macOS / Linux，项目根目录：

```bash
python3.12 -m venv .venv-dashboard
.venv-dashboard/bin/python -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python dashboard/start.py
```

Windows PowerShell，项目根目录：

```powershell
py -3.12 -m venv .venv-dashboard
.\.venv-dashboard\Scripts\python.exe -m pip install -r dashboard/requirements.txt
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.\.venv-dashboard\Scripts\python.exe dashboard/start.py
```

模型原有的 `.venv` 和 `requirements.txt` 保持独立。Python 的完整运行依赖锁定在本目录 `requirements.txt`；前端使用 `package-lock.json` 锁定。

## 结果来源与更新

启动时扫描项目 `runs/` 下的冻结回放，以及随仓库交付的 `FINAL_OUTPUTS/01_saved_model_replay/verified_replay/`。仅接受 `mode=frozen_model_inference`、`status=passed`、`stage=complete` 的记录，核对清单中的全部文件 SHA-256、预测/回测校验状态、行数和日期覆盖。训练记录不参与展示。存在损坏的回放时跳过并显示数量；没有有效记录时返回不可用状态，不生成假数据。

本机默认选择最新验证通过的回放（当前为 `saved_ensemble_20261101T062202_638390Z`）。新克隆的仓库没有本地 runs 时，使用随项目交付的真实历史结果。两份结果的数值一致，但运行日期和文件哈希不同，页面会显示实际来源。

服务将已验证结果保存在内存中，下载与图表始终读取同一份快照。新增回放后**重启 Dashboard**才会加载；刷新浏览器不会重新扫描磁盘。

若只想提供指定的一次结果，可配置绝对路径：

```bash
export SAFECAPITAL_RESULT_DIR="/absolute/path/to/verified/replay"
.venv-dashboard/bin/python dashboard/start.py
```

指定目录无效时启动失败，不会替换成其他回放。清单哈希校验检查文件一致性，不是独立的第三方签名；原计算程序负责数值验证。

## 接入客户网站

建议将本服务部署在独立 HTTPS 域名，例如 `https://research.example.com/`。客户增加一个页面，放入：

```html
<iframe
  src="https://research.example.com/?embed=1"
  title="SafeCapital 历史策略研究"
  width="100%"
  height="1400"
  style="border:0; border-radius:16px"
  loading="lazy">
</iframe>
```

框内自带滚动；客户可以按页面空间调整高度。首次接入不依赖跨域消息或自动高度脚本。如果客户额外加 `sandbox` 属性，需要允许脚本、同源与下载，否则相关功能会受限。

本服务默认只允许同源嵌入。部署时指定客户站点的**精确 origin**（协议、域名及必要端口，无路径或尾部斜线），可用逗号分隔多个域名：

```bash
export SAFECAPITAL_EMBED_ORIGINS="https://client.example,https://www.client.example"
.venv-dashboard/bin/python dashboard/start.py --host 0.0.0.0
```

服务通过响应头 `Content-Security-Policy: frame-ancestors 'self' ...` 授权嵌入。客户自己的 CSP 也要在 `frame-src` 中允许 Dashboard 域名。反向代理不要额外设置冲突的 `X-Frame-Options: DENY/SAMEORIGIN`。iframe 内的页面与 API 同源，因此此方式不需要开放 API 的跨域 CORS。

V1 不实现登录或客户 SSO，也不保存客户输入。若客户要求只有登录用户可看，需要在反向代理或后续认证层同时保护页面、API 和下载；嵌入域名白名单不等同于访问认证。

## 部署包（当前暂缓）

以下是之前准备的可选部署资料，不是当前本地使用的必要步骤。现有 Docker 配方只包含输出；如未来启用容器，需要补入并验收 V1.2 的输入文件。

仓库根目录已有 `.dockerignore`，Dockerfile 仅打包 Web 服务、构建后前端及交付的真实验证结果。镜像不包含训练数据、模型依赖或本机 runs。

```bash
docker build -f dashboard/Dockerfile -t safecapital-dashboard .
docker run --rm --name safecapital-dashboard \
  -p 127.0.0.1:8000:8000 \
  -e SAFECAPITAL_EMBED_ORIGINS="https://client.example" \
  safecapital-dashboard
```

在主机上用 Nginx / 客户现有网关为它提供 HTTPS。示例见 `docs/nginx.conf.example`。容器只运行已完成结果的展示服务，使用非 root 用户。若需要特定新结果，可只读挂载其完整目录并设置 `SAFECAPITAL_RESULT_DIR`。

目前已验证原生 macOS 启动；本机 Docker daemon 未启动，尚未实测容器构建和启动，部署前应执行上述两条命令验收。Windows 和客户实际域名/登录系统也需要目标环境验收。

## API

所有接口只读。首先访问 `GET /api/v1/runs` 获取有效 ID，再使用该 ID：

| 路径 | 响应 |
|---|---|
| `/api/v1/health` | 可用状态、有效与拒绝的结果数量；无结果时 503 |
| `/api/v1/runs` | 结果列表及 `default_run_id` |
| `/api/v1/runs/{id}/inputs` | 输入目录、字段、日期覆盖和哈希 |
| `/api/v1/runs/{id}/inputs/{dataset}/rows` | factors/prices，支持 date、scope、q、page、page_size |
| `/api/v1/runs/{id}/inputs/{dataset}/download` | 完整原始输入 CSV |
| `/api/v1/runs/{id}/overview` | 指标、全部可选信号日期、来源与覆盖范围 |
| `/api/v1/runs/{id}/equity` | 完整每周资金、收益与从初始资金起计算的历史回撤 |
| `/api/v1/runs/{id}/rankings?date=2026-08-28&q=ANF&page=1&page_size=10` | 日期排名、股票代码过滤与分页；page_size 上限 100 |
| `/api/v1/runs/{id}/downloads/{kind}` | 原始文件，字节与已验证快照相同 |

`kind` 可为 `predictions`、`equity`、`summary`、`manifest`、`prediction-verification`、`backtest-verification`。不存在的结果或下载返回 404；非法日期/页码返回 422。服务器不暴露仓库文件路径，也不接受文件上传、任意路径下载或执行命令。

所有摘要指标对应完整 210 周回测，切换图表区间不会重新计算顶端指标。预测覆盖 366 周与回测覆盖 210 周在页面中分别标注。回撤按完整资金历史计算，切换区间只裁剪显示，不重新设置峰值。

## 开发与测试

后端启动后，另开终端执行 `npm --prefix dashboard/frontend run dev`。Vite 将 `/api` 代理到 `127.0.0.1:8000`，只供本地开发；修改后重新 build 即可由 Python 服务提供更新后的静态页面。

```bash
.venv-dashboard/bin/python -m pip install -r dashboard/requirements-test.txt
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python -m unittest discover -s dashboard/tests -v
```

30 项接口与完整性测试覆盖真实数值、排名分页/搜索、原始下载、损坏文件、非有限数值、路径和符号链接越界、域名白名单及空结果状态。浏览器验收记录见 `docs/LOCAL_IO_VALIDATION.md`。

参考：[FastAPI 静态文件](https://fastapi.tiangolo.com/tutorial/static-files/)、[Vite 相对部署路径](https://vite.dev/guide/build#relative-base)、[MDN 嵌入域名策略](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors)。
