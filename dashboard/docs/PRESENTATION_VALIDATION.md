# Dashboard 1.4 验收记录

日期：2026-11-02（Australia/Sydney）。范围：已有结果的关注股票查询与 presentation 交互。本地 macOS、Python 3.12、Node.js 25.2.1；客户网站、生产部署、Docker 和 SSO 不在本次验收范围。

## 自动验证

| 检查 | 结果 |
|---|---|
| 前端 TypeScript + Vite 生产构建 | 通过 |
| 后端接口与文件一致性测试 | 49/49 通过，含 10 项新增关注测试 |
| 前端语言、搜索、保存偏好、超时与取消测试 | 12/12 通过 |
| 实际服务 HTTP smoke check | 通过，原资金期末值 149330.60888418998，210 周，输入各 17353 行 |
| `verify-watchlist.mjs` | 真实示例、JSON 导出、无数据、非法股票、原策略指标一致均通过 |
| 原研究文件 | 相对于功能开发前 main 的清单，207 个非 Dashboard 文件内容保持一致（清单自身除外） |

执行命令：

```bash
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python -m unittest discover -s dashboard/tests -q
node --experimental-strip-types --test dashboard/frontend/tests/*.test.ts
.venv-dashboard/bin/python dashboard/tools/smoke_check.py
node dashboard/examples/verify-watchlist.mjs
```

新增后端检查包括：股票池与真实公司名称、日期/代码精确关联原因子/价格/排名、SCL/TJX/CMG 入选差异、缺失数据保持 null、快照/输入缺失时隔离、当前选择 CSV/JSON、CSV 字符串转义、原策略与原始下载不被改变、结构化非法请求。

原 87 项研究回归及训练/回放记录沿用原版本验收；本次未重新训练或重新执行整套研究计算。测试中存在依赖的弃用提示及原测试文件未关闭的 ResourceWarning，不影响通过结果。

## 浏览器操作检查

使用实际生产构建与本地 FastAPI 服务：

- 中文「载入演示示例」显示 2026-08-28：SCL rank 1 / selected，TJX rank 2 / not_selected，CMG rank 3 / selected；目标/实际权重使用验证快照。
- TJX 详情展示五因子、rank 2、score 0.8083 和三组件百分位 62.50%/87.50%/92.50%；无伪造的排除理由。
- `Chipotle` 公司搜索、`URBN` 键盘 Enter 添加/移除、重复选择去重、`AAPL` 不支持提示、清空/重置均正常。
- 日期切至 2022-08-26：research-date、allocation-date、input-date、date 四处相同；关注排名变为 34/23/35，旧结果和导出链接不会被当成新结果展示。
- 输入表第 2 页切换统一日期后回到第 1 页。
- 切到 2019-08-30：有排名也可显示「该日期无配置」；CMG 没有排名。无配置不是未入选，缺失数值不是 0。
- 源文件独立选择 2015-09-04 不更改研究日期；示例按钮恢复对齐模式、日期和输入筛选。
- 切换中英文保留关注、日期和结果；新增可见文案和辅助提示均翻译。刷新保留关注股票，日期回到最新回测周。
- 点击真实 CSV 下载，核对得到三行 SCL/TJX/CMG，日期 2026-08-28，TJX 未入选权重为空；API 的 JSON 导出与查询响应相同。
- 1280×1000 宽屏三栏详情、默认桌面窗口和 390×844 手机均检查；手机页面 scrollWidth=390，表格在局部容器横向滚动。测试后已恢复默认窗口。
- 正常页面浏览器 console 未发现错误。

## 异常隔离检查

独立临时本地代理模拟故障，正式 8000 服务数据未修改：

1. 模块根页面返回 503、无法运行前端；嵌入外壳先显示加载，12 秒后显示重试和独立 Dashboard 链接，外层入口仍可操作。
2. 恢复代理后点击「重新加载模块」，实际就绪消息到达后显示 iframe，隐藏错误入口。
3. 仅 watchlist API 返回 503，关注区域显示错误与重试，原策略表现仍可查看；恢复接口并点击重试后表格正确。
4. 前端单测分别覆盖等待响应和 JSON body 卡住的超时，以及外部 AbortSignal 取消。

临时代理和测试页已关闭，不属于交付运行服务。

## 可移植包检查

使用 `build_delivery.py` 生成 1.4 预验收 ZIP，解压到项目外新目录，执行文件校验并从包中源码启动 8002 服务；复用本机已安装、版本锁定的 Dashboard Python 环境。未依赖本地研究模型环境或项目 runs 目录。

结果：包内 run_id 为 `delivered`，输入/配置/持仓完整可用；包内 smoke check（对照包内原始结果字节）和 verify-watchlist 均通过。随后生成的正式包记录功能提交和独立 SHA-256。此检查是包解压与运行验收，不宣称在新电脑重新安装过依赖。临时 8002 服务已停止。

## 截图

- [桌面关注结果](watchlist-desktop.jpg)
- [TJX 输入/排名/配置详情](watchlist-detail.jpg)
- [中文手机搜索](watchlist-mobile.jpg)

仍需客户确认最终域名、部署/认证方式及 staging 环境，并验收实际入口与其他 Portfolio 功能。当前完成的是本地可演示、可交付接口的独立研究模块。
