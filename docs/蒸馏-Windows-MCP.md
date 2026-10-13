# 蒸馏 · Windows-MCP（CursorTouch/Windows-MCP）

> 出处：**现读** `github.com/CursorTouch/Windows-MCP`（README 35,974 字符，2026-10-13 抓取 · 8871★）
> PyPI `windows-mcp` · MCP Registry 已收录 · 许可 **MIT**
> 胶囊：`gbt_allinone/store/devoured/devoured_cursortouch_windows-mcp/`

## 一、它是什么（一句话）

**一个 MCP**：`MCP Server for Computer Use in Windows` —— 让任何 LLM 都能做
文件导航 / 应用控制 / UI 交互 / QA 测试。**不依赖传统计算机视觉**，也不需要微调模型。

## 二、它怎么工作（原文口径）

1. 通过 UIA（UI Automation）**原生**读/操作 Windows 元素 —— 不靠截图猜坐标。
2. 工具集：键盘、鼠标、**State-Tool**（抓窗口/UI 状态）。
3. 浏览器另有一条 **DOM 模式**（`use_dom=True`）：只留网页内容，滤掉浏览器外框。
4. 标注动作节律：click→click 典型 **0.2–0.5 s**。

## 三、我们蒸出四条（不是复制它的代码）

| 序 | 取法 | win-mcp 原话 | 我们的落点 |
|---|---|---|---|
| ① | 状态先行 | `State-Tool … capturing window/UI state` | 铁律 1「先看再动」写成可复读判据 |
| ② | UIA 优先、视觉可选 | `doesn't rely on any traditional computer vision techniques` | 层级 = UIA 直取 → DOM 降噪 → 视觉兜底 |
| ③ | DOM 降噪 | `use_dom=True … focuses exclusively on web page contents` | 读网页走 DOM（`browser.dom_query`）；**Firefox 无 `RootWebArea` ⇒ IAccessible2 兜底**照记 |
| ④ | 动作节律 | `Typical latency … ranges from 0.2 to 0.5 secs` | `op=rhythm` **现算**「动后等稳定」等待，带上限防死等 |

## 四、为什么是「取法」不是「建平行位」（立项理由）

win-mcp 干的事（Windows 桌面控制）我们**已经有**：`tentacle`（UIA 直操作，无视遮挡）·
`desktop_commander`（终端 + 文件系统全能力）· `browser`（DOM / 原生窗口，走 CDP）。
照抄建一个平行位 = 撞仓规「**新增即清旧**」里「同功能两份」那一条（`supersede-check.py` 会打红）。
⇒ 本位只**蒸取法**；它的「起服务 / 装计划任务」**明确不取**（那是接入端的活，且会写用户目录与系统计划）。

## 五、落点（三处齐 · 零作用域）

- 原生位：`desktop_distill`（登记 `caps_registry.py` · 分派 `api.py` · 图鉴 `omni build` ⇒ 290 位）
- 入口：`py -3.14 tools/codex-scripts/five-dim.py cap desktop_distill '{"op":"method"}'`
- 门：`policy.evaluate('desktop_distill').scopes == ()` —— **零作用域**（只读 + 纯算）
- ops：`method` / `rhythm` / `source` / `provenance` / `where`

## 六、红线照旧

本位只是**取法**（读法与节律），**不动别人的系统**；任何"拿它去动桌面"的动作仍走 `tentacle`
（`desktop_control` 门）+ 六条铁律，**AI 不许自发放行**。

> ⛔ 开发者：自由的风 · 本署名不可删除、不可篡改归属
