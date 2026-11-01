# SafeCapital Web 1.4 — 从这里开始

本包为可独立运行的历史股票研究模块：网页、后端接口、已构建的前端、真实验证结果、与结果匹配的现有输入和文档。支持独立访问或嵌入客户网站；不需要整个训练工程。初始资金 100000，历史期末资金约 149330.61；请以包中真实 CSV 为准。

当前优先使用本地原生启动，Docker 和公网部署暂缓。输入/输出操作见 `dashboard/docs/LOCAL_IO.md`，可交付接口定义为 `dashboard/docs/openapi.json`。

本版客户需求、组合权重合同、范围/假设/缺失值与实际接入步骤见 [Portfolio Neo 交接](PORTFOLIO_NEO_INTEGRATION.md)（ZIP 根目录版本请打开 `dashboard/docs/PORTFOLIO_NEO_INTEGRATION.md`）。

演示入口：启动后打开 `/?lang=zh#watchlist`，点击「载入演示示例」。新增关注股票、统一日期、详情、CSV/JSON 导出及接口见 `dashboard/docs/PRESENTATION_WATCHLIST.md`（文档目录内可打开 [关注股票演示](PRESENTATION_WATCHLIST.md)）。选择关注股票不会重新计算策略收益。

## 1. 安装与启动

解压 ZIP，进入含本文件的目录。运行环境：Python 3.12，64 位。首次安装需要联网下载锁定的依赖；服务运行本身无需联网，在线 Swagger 文档除外。

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

已包含前端构建产物，运行不用 Node.js。首次启动成功后打开 `http://127.0.0.1:8000/`。保持终端运行；Ctrl+C 停止。安装脚本不覆盖已有虚拟环境；升级时解压新目录并安装，再切换服务。

## 2. 配置

编辑包根目录 `config.toml`，不需要修改源码。请先完成原始包校验与安装，再修改配置；修改后的配置文件与交付清单不一致属于预期，应核对为自己作出的变更。

| 配置 | 默认 | 说明 |
|---|---|---|
| host | 127.0.0.1 | 本机/反向代理监听地址；容器内用 0.0.0.0 |
| port | 8000 | 服务端口 |
| public_url | 空 | 客户正式访问地址，例如 https://research.example.com/；使用独立域名根路径 |
| result_dir | 空 | 默认使用随包交付的结果；可指定完整新回放目录 |
| embed_origins | 空 | 允许 iframe 嵌入的客户 origin，逗号分隔 |
| api_origins | 空 | 允许浏览器直接调用 API 的客户 origin，逗号分隔 |

origin 为协议+域名+可选端口，无路径和尾部斜线，不接受通配符。相对 result_dir 基于配置文件目录解析。配置优先级：默认值 < TOML < `SAFECAPITAL_字段名大写` 环境变量 < host/port CLI 参数。也可通过 `SAFECAPITAL_CONFIG` 选择配置文件。浏览器只能读取 public_url 等公开配置，不能读服务器路径。

例：

```toml
host = "127.0.0.1"
port = 8000
public_url = "https://research.example.com/"
result_dir = ""
embed_origins = "https://client.example"
api_origins = "https://client.example"
```

上述域名为示例，需替换为客户实际地址。

## 3. 接入方式

方式 A：客户网站新增页面放入 iframe：

```html
<iframe src="https://research.example.com/?embed=1"
  title="SafeCapital 历史策略研究" width="100%" height="1400"
  style="border:0;border-radius:16px" loading="lazy"></iframe>
```

页面内带滚动，不需要父页面读取框内 DOM。双方站点的 CSP 要允许对应嵌入：本服务设置 frame-ancestors，客户设置 frame-src。示例 `embed-example.html` 可在运行的网站里查看。

方式 B：客户自建页面调用 `/api/cs5_6_equity/v1/`；字段定义和 JavaScript 示例见 `dashboard/docs/API_V1.md` 及 `dashboard/examples/client.mjs`。集成时先请求 runs 获取 ID。

## 4. 部署

建议部署在独立 HTTPS 域名根路径。将客户现有网关代理到服务端口；配置参考 `dashboard/docs/nginx.conf.example`。本包不包含域名、TLS 证书或客户账号系统。

以下为以前准备的可选 Docker Compose；配方尚未包含 V1.2 输入文件，暂不作为本版输入/输出验收路径：

```bash
docker compose config
docker compose up --build -d
docker compose ps
docker compose logs --tail=100
```

容器中端口固定 8000，配置文件只读挂载；宿主端口用 `SAFECAPITAL_PORT` 环境变量调整。可通过 `docker compose down` 停止。Docker 是否实测，以 `dashboard/docs/DELIVERY_VALIDATION.md` 为准。

V1 没有用户账号和私有数据隔离。若客户要求登录后可见，应由其网关同时保护页面、API 和下载，再验收嵌入登录行为；仅配置允许嵌入域名不等于登录保护。

## 5. 验收

启动服务后另开终端：

```bash
python3.12 smoke_check.py --url http://127.0.0.1:8000/ --expected-dir FINAL_OUTPUTS/01_saved_model_replay/verified_replay
```

Windows 用 `py -3.12`。该命令核对健康状态、真实指标、排名、输入因子/价格、网页资源和所有主要下载字节。再在浏览器检查日期切换、搜索、下载和客户站点内的嵌入。

`DELIVERY_MANIFEST.json` 记录文件 SHA-256、构建来源和真实回放身份；ZIP 旁的 `.sha256` 记录压缩包校验值。文件哈希检查不等于第三方数字签名。

## 6. 更新与回滚

1. 在独立的模型工程中生成新的回放，并确认 manifest 为 passed。
2. 完整复制该回放目录，使用新的目录名；不要逐个覆盖正在使用的结果。
3. 同时提供匹配输入及模型配置/清单（固定位置见 LOCAL_IO.md）；输入身份不匹配时只显示输出。将 result_dir 指向新目录，重启服务并执行 smoke_check。
4. 验收失败时，将配置指回上一目录并重启。保留旧软件包和旧结果。

服务启动时验证数据，运行中使用内存快照，刷新网页不会加载磁盘上的新文件。软件升级请安装到新目录，验收后由网关切换目标服务；有问题可切回旧服务。

## 7. 交付责任

开发方提供模块、接口、真实结果与安装文档；客户提供最终域名、部署环境、嵌入站点、登录要求及维护联系人。后续新数据推理、在线训练、定时更新、实际交易不属于本版功能。
