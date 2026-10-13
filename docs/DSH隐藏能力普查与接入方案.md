# DSH 隐藏能力普查与接入方案

> 主人令（2026-10-08 逐字）：「把 **DeepSeek Harness 的所有隐藏能力全部接入**，**APP 就直接使用
> DeepSeek Harness 官方 APP**，把集成完美做好，**我们自己的能力也一个不能落下全部接入**」
>
> 取证日期 **2026-10-08** · 取证方式：**读盘**（本机装着的官方包 + 本仓现役件），不读二手教程。
> **本次全程只读**：没改 `~/.dsh/**` 一个字节，没改本仓 `gbt_allinone/**`、`holo_pet_w3/shell/**`，
> 没试任何需授权的作用域。§② 的改动点**只给方案，本次未执行**。
>
> 一手件（全是现读）：
> - `~/.dsh/profiles/node_modules/@deepseek-ai/` — **240 个包**（逐 package.json 现读）
> - 三层补丁：`dsh-base/cordis.patch.yml`（84 行）· `dsh-web-app/cordis.patch.yml`（68 行 + 26 条 id 覆盖）
>   · `dsh-llm-qwen-local/cordis.patch.yml`（1 行）· 用户层 `~/.dsh/profiles/web/cordis.patch.yml`
> - 会话面：`dsh-agent-presets/presets/{standard,ptc,cordis,minimal}` + `~/.dsh/.agent-presets/gbt-spine/`
> - 壳：`holo_pet_w3/shell/{main.cjs,dsh-launch.cjs,url-policy.cjs,windows.json,connect.html}` · `holo_pet_w3/panel/index.html`
> - 我方真源：`py -3.14 -m gbt_allinone list`（现跑）· `state/cap-bindings.json`（2026-10-08T06:55:16）
>
> **复跑**（一条命令重算本文件的全部①③读数）：
> ```
> py -3.14 tools/codex-scripts/dsh-census.py            # 人读总表
> py -3.14 tools/codex-scripts/dsh-census.py --json     # 机器可读
> py -3.14 tools/codex-scripts/dsh-census.py --out state/dsh-census.json
> ```
> 姊妹件：`docs/DSH模型部署-官方契约与我们现况对照.md`（2026-09-25 · 讲 LLM 路由契约）——
> 本件讲**包族与挂载/接入面**，两件互补，口径冲突以现读为准。

---

## 〇 三个口径（先钉死，否则"隐藏能力"这个词会被误读）

**口径一：什么是"官方 APP"。** `dsh web` = `dsh --profile web`（`@deepseek-ai/dsh` README 的
Entry modes 表现读），它拉的 Web GUI 由 **`@deepseek-ai/dsh-web-app`** 这个 bundle 提供
（「The dsh browser-surface bundle … frontend dist serving, web-surface prompt, bash runtime
variables, URL line」——包自述现读）。本仓的「APP 直接用官方 APP」指的就是它。

**口径二：组合树有四层，**同一 id 后写覆盖先写**（`cordis.yml` 官方注释现读：「each bundle in
package.json's dsh.profile.bundles, then cordis.patch.yml, then any --patch overlays」）：

```
~/.dsh/profiles/web/cordis.yml           空入口列表（只有 `[]`，官方注释明说别改它）
  ↑ 依次叠：
  ① bundles：dsh-base → dsh-web-app → dsh-llm-qwen-local   （web/package.json:6-10 现读）
  ② 用户补丁：web/cordis.patch.yml                          （我们加的行：gbt-master、llm-pi-ai）
  ③ --patch 覆盖层（临时用，现役没挂）
```

**口径三：宿主面 vs 会话面（本次普查最要紧的一条）。** `dsh-web-app` 补丁把 **agent 平面整块
disable**，改由**每个会话按 agent preset 挂**（补丁原文：「The agent plane moves behind agent
presets … the Web surface disables them here and lets each session mount a preset instead」
「Disabling rather than deleting is deliberate」——`dsh-web-app/cordis.patch.yml:351-360`）。
且 `settings.yaml` 现读 `agent-presets.default: gbt-spine` —— **默认会话就是我们自己的 preset**。
⇒ 只统计"宿主行"会把**现役会话正在用**的包误报成"未启用"；本件把两层面分开算：

- **宿主面**：补丁行直接挂载且未被覆盖禁用（`挂载启用 124`）；
- **会话面**：preset 文件里的行（默认 preset 挂 24 个包，5 个 preset 总计 28 个包）；
- **未启用** = 两面都没有、也不在宿主现役依赖闭包里的（**20 个**，§① 末列）。

---

## ① 逐族清单：装了什么 → 干什么 → 现役启用否 → 怎么接 → 代价与风险

**总读数（探针现算，2026-10-08）**：装 **240** = 宿主面挂载 **124** + 宿主行被禁 **24** +
库件（宿主闭包）**62** + bundle 自身 **1**（dsh-base）+ 入口 CLI **1**（dsh）+
仅预设挂载 **8** + **未启用 20**。行 **154**（启用 127）；预设 **5** 个（默认 `gbt-spine`）。

读表法：`装/宿主挂载/宿主行被禁/库件/被预设挂载/未启用`。**宿主行被禁 ≠ 不可用**：web 面的
agent 平面被禁是官方设计，会话面（preset）会再挂（见口径三）。

| 族 | 装/宿主/被禁/库/预设/未启用 | 这一族是干什么的 | 接入面 | 代价与风险（要接就付这个） |
|---|---|---|---|---|
| 浏览器 UI 插件 `dsh-client-ui-*` | 41/38/1/2/0/**0** | 官方 APP 的每个界面件（会话、聊天、侧栏、设置、轨迹、模型选择…） | 已由 web-app bundle 全挂；`ui-schedule` 官方**故意默认关**（补丁原文：需要 Schedule overlay 一起开） | 已接满；改任何一件都=改官方行，**不动** |
| 会话与投影 `dsh-session-*` | 23/14/0/9/0/**0** | 事件溯源会话库、JSONL 持久化、投影/缓存、FTS 搜索、标题、统计 | 已全挂（宿主面） | 已接满；新增投影类型需官方契约，不做 |
| 模型工具 `dsh-tool-*` | 21/3/12/0/**16**/**2** | 给模型用的工具面（bash/pwsh/fs/子代理/工作流/ralph/skill/todo/web…） | 宿主面**故意全禁**，**会话面由 preset 挂**（gbt-spine 挂 16 个） | 新增工具=往 preset 加行（**动 .agent-presets，受守卫 B2 哈希盯着**，改前问主人） |
| 进程与终端 | 13/3/1/6/2/**1** | 壳执行器与 PTY：bash/pwsh 执行器（沙箱截流版）、子进程、终端 | 已挂（Win 上走 pwsh 一路；`bash-sandbox` 平台判据禁用）；`dsh-terminal` 由 minimal preset 挂 | 接 PTY 终端工具=往 preset 加 `dsh-tool-pwsh-persistent`（代价：常驻终端保持状态，审计面变大） |
| 框架底座·cordis | 10/1/1/7/0/**0** | cordis 微内核、loader、include、timer、hmr、schemastery、dsh-base 本体 | 已挂（hmr 官方默认禁；我们走 `patchReload: live`） | 不动 |
| 零依赖底座件 | 10/2/0/8/0/**0** | uuid/时间/超时/scope/invariants/品牌类型/匿名ID 等零依赖件 | 库件随树加载 | 不动 |
| 存储与溢出 | 10/5/0/5/0/**0** | storage hub + JSON KV + domain、超大工具结果 spill | 已挂 | 不动 |
| 设置与权限 | 8/5/0/3/0/**0** | settings.yaml 提供者、凭据 seam、权限预设、审批、授权对话 | 已挂（`danger-full-access` 现读在 settings.yaml） | 改默认权限档=改被守卫盯的文件，改前问主人 |
| Host 服务 | 8/4/0/4/0/**0** | webserver / 前端静态 / 目录选择器 / open-in-app / 插件清单 | 已挂 | 不动 |
| 独立 profile 面（sdk/acp/headless） | 7/0/0/0/0/**7** | **另一条命令线**：`dsh --profile headless "job"`（跑一个任务出结果就退）· `--profile sdk`（JSON-RPC stdio）· `--profile acp`（ACP stdio） | **不经 web profile**；按官方 CLI 表独立起（首次自动初始化模板） | 中：可当我们自动化/联调的"第二条腿"；不进 APP 面，无 UI 冲突 |
| 人设/提示/上下文/时间 | 7/3/1/0/2/**2** | 人设段（persona）、系统提示装配、计划模式、token 计量、时间/计时上下文 | `persona`/`plan-mode` 会话面已挂（gbt-spine 带我方三主线道人设）；`time-context`/`tmux-context` 未启 | 低：往 preset 加两行即可（代价：每步上下文多两段，token 涨） |
| Web 面 | 7/4/0/1/0/**2** | `dsh-web` 能力 seam + fetch/search provider + webhook 运行时 | web/fetch/search 已挂；**webhook（github 签名入口）未启** | webhook=对外开口子（本地端口+签名校验），要单独设计，暂不接 |
| CLI/引导 | 6/0/0/5/0/**0** | `dsh` CLI 本体、boot glue、cmdline 快照、home 路径、启动环境 | `dsh` 是入口（现役），其余库件随树 | 不动 |
| agent 平面 | 6/4/1/0/2/**0** | agent 注册表/循环/默认模型/AGENTS.md 装载/preset 机制 | 宿主挂 4；`agent-instructions` 宿主禁、preset 挂；preset 机制=**我们接入的主缝** | 已有（gbt-spine）；新增能力走这里 |
| Host RPC 控制器 | 6/6/0/0/0/**0** | 浏览器↔宿主的 RPC 控制器（会话/设置/工作区/文件） | 已挂满 | 不动 |
| 浏览器内核/传输 | 6/6/0/0/0/**0** | 模块系统、RPC 传输、上传、资源模型、HMR | 已挂满 | 不动 |
| 目标与命令 | 6/4/2/0/2/**0** | 会话目标（goal）+ 人类斜杠命令（/goal /compact /feedback） | 宿主行被禁是设计；preset 挂 goal/compact/feedback | 已接 |
| 文件系统 | 4/2/0/2/0/**0** | fs seam、沙箱版 fs、观察策略、发现（glob/grep，含 ripgrep） | 已挂 | 不动 |
| 作业/调度/消息/Webhook | 4/2/0/1/0/**1** | 后台作业注册表、**durable 定时提醒（schedule）**、消息点赞反馈 | jobs 已挂；**`dsh-schedule` 未启**（UI 面 `ui-schedule` 也默认关） | 中：开 schedule = 宿主加行 + 开 ui-schedule + 设置 overlay；会自己发提醒，需主人拍板 |
| LLM 适配器 | 4/4/0/0/0/**0** | `dsh-llm` 服务 + 官方 deepseek 适配器 + pi-ai 通用适配器 + 重试策略 | 已挂满；我方三家 provider 走 **pi-ai**（见 §③） | 已接满 |
| 沙箱 | 4/2/0/2/0/**0** | 进程沙箱 seam（Win 走 ACL 后端）、策略、local 后端 | 已挂（Win：`pwsh-sandbox` 现役；`bash-sandbox` 平台判据禁用） | 不动 |
| 子代理 | 4/3/0/1/0/**0** | ctx.subagents seam + spawn/fork 两个后端（进程内） | 宿主挂 3；委派工具由 preset 挂 | 已接 |
| 上下文压缩 | 3/0/2/1/2/**0** | 压缩 seam、token-meter 驱动的压缩策略、工具结果裁剪 | 宿主行被禁是设计；preset 挂 `compaction-basic` + pruner | 已接 |
| **外部钩子桥** `dsh-hook*` | 3/0/0/0/0/**3** | **跑 Claude Code / Codex 的 hooks 配置**（hooks.json）在我们的拦截缝上（协议、匹配器、多钩子合并） | **隐藏能力**：宿主加行（`dsh-hooks-codex` 或 `-claude-code` 或两者）+ 指 hooks 文件 | **高**：钩子能拦/改工具调用 —— 是"给外部配置生效权"，接之前要主人拍板 + 定 hooks 文件归属 |
| 技能 | 3/1/2/0/1/**0** | 技能注册表 + 文件系统装载 + 自带徽章技能 | `skill` 已挂；`skill-filesystem`/`tool-skill` 会话面挂（gbt-spine 带 `skills/` 目录）；`skill-badge` 官方默认禁 | 已接；加技能=往 preset 的 skills 目录放 SKILL.md |
| Typert 反射 | 3/2/0/1/0/**0** | 生成式类型反射（RPC 元数据/schema） | 已挂 | 不动 |
| 附件 | 2/1/0/1/0/**0** | 附件 seam + 本地内容寻址存储 | 已挂 | 不动 |
| 代码运行时 | 2/1/0/1/0/**0** | 代码执行 seam + worker-thread 后端 | 已挂 | 不动 |
| 动态插件（cordis 双半） | 2/2/0/0/0/**0** | 让**模型自己挂/卸插件**的双半运行器（宿主半 + 浏览器半） | 已挂（`tool-cordis` 由 preset 挂 ⇒ 默认会话里模型能自己挂临时插件） | 已接；安全面=信任边界，官方原文如此 |
| 引用（@文件/@会话） | 2/1/0/1/0/**0** | `@file` 模糊索引、跨会话引用 | 已挂 | 不动 |
| 工作区 | 2/1/0/1/0/**0** | 工作区注册表（会话挂接到哪个目录） | 已挂 | 不动 |
| 工作流 | 2/0/1/0/1/**1** | `ctx.workflowEngine` seam + **模型写 JS 编排脚本**的 worker-thread 引擎 | 宿主行被禁是设计；`workflow-worker-thread` + `tool-workflow` 由 preset 挂 | 已接（我们自己的"万能插"另有 `wf_*` 能力位，两层别混） |
| MCP 桥 | 1/0/0/0/0/**1** | **MCP 客户端桥**：连 MCP server 并把它们的工具注册进 `ctx.tools` | **隐藏能力**：宿主加行 + 配 server 清单 | 低-中：接我方能力进 APP 的**最优候选**（见 §③ 缺口）；代价=多一个子进程与信任面 |

### 未启用清单（20 个，逐族给数；= 两面都没挂、也不在宿主闭包）

| 族 | 未启用清单 | 一句话代价/风险 |
|---|---|---|
| 独立 profile 面（7） | `dsh-sdk-app`·`dsh-sdk-minimal`·`dsh-sdk-jsonrpc-server`·`dsh-sdk-protocol`·`dsh-acp`·`dsh-acp-app`·`dsh-headless` | 不算缺陷：它们是**另外三个 profile**（sdk / sdk-minimal / acp / headless 的 bundle）。要用就按 `dsh --profile …` 独立起，**不改 web profile 一行** |
| 外部钩子桥（3） | `dsh-hook-protocol`·`dsh-hooks-claude-code`·`dsh-hooks-codex` | 见上表：给外部 hooks 拦截权，需主人拍板 |
| Web 面（2） | `dsh-webhook`·`dsh-webhook-github` | 对外开口（GitHub 签名 webhook→建会话），要独立设计与签名密钥 |
| 人设/提示（2） | `dsh-time-context`·`dsh-tmux-context` | 往 preset 加两行即可；代价是每步上下文变长 |
| 模型工具（2） | `dsh-tool-bash-persistent`·`dsh-tool-str-replace-editor` | 持久 bash 在 Win 上本就不用（走 pwsh）；str-replace-editor 是另一套编辑工具，与 `tool-fs` 重复，可不接 |
| 进程与终端（1） | `dsh-bash-local` | Win 平台不走 bash 一路（现役是 pwsh-sandbox）；装上也只是躺着 |
| 作业/调度（1） | `dsh-schedule` | durable 定时提醒：会自己发提醒，开前拍板 |
| 工作流（1） | `dsh-workflow` | **seam 本体**（`ctx.workflowEngine` 服务）。preset 挂的是 worker-thread **实现** + 工具行；单挂 seam 无意义 |
| MCP 桥（1） | `dsh-mcp-client` | 见 §③：接我方能力进 APP 的候选缝 |

### "启用了但没用上"与"未启用"分开报（主人点名的两回事）

- **未启用** = 上表 20 个（两面都没挂）。
- **启用了但没用上**（在现役树里、但**没有证据**说明我们真用过；**不编**）：
  - `ui-*` 里一批官方 UI 功能（trajectory 轨迹、deliverables 产物尾、message-feedback 点赞、
    session-log-export 导出、open-in-app「在系统中打开」）——**挂载启用**，我方**没有使用记录**
    （账本没有这类事件的口径；要断言"用过"需具体操作读数，本次不给不实断言）。
  - `dsh-session-telemetry-otel`：现役挂载（`mode: FEEDBACK_ONLY`，上报地址
    `https://harness-telemetry.deepseeksvc.com/v1/logs` ← 补丁原文现读）。**要不要关**另说（env 可关），
    本次只报现状。
  - `dsh-deepseek-llm-api-extensions` / `dsh-plugin-package-inventory-deepseek` /
    `dsh-session-log-deepseek`：为**官方 DeepSeek API 路由**服务；现读 `settings.yaml` 的
    默认模型就是 `deepseek-official` ⇒ 在役，非"没用上"。
- 反例（防误伤）：`tool-pwsh` 宿主行被禁，但**默认会话（gbt-spine）挂着它** ⇒ 它是"现役"，
  不是"没用上"。判断必须看两层（探针输出里 `row_disabled` 与 `preset_enabled` 分开给）。

---

## ② 官方 APP 面接入方案：壳的窗 A「直接用官方 APP」，与我方面板并存

### 2.1 现状（现读，未改一个字节）

窗 A = 注册表 `dsh-chat`（`holo_pet_w3/shell/windows.json:62-86`），**自接入已经打通**：

| 环节 | 现读锚点 | 行为 |
|---|---|---|
| 窗定义 | `windows.json:65` `"file": "../shell/connect.html"`；`default.visible:false` | 默认隐藏（宿主不打扰律）；现在**载本地引导页** |
| 自接入开关 | `windows.json:72-80` `auto_dsh{enabled:true, port:3080, since:2026-10-07}` | 声明"开窗即自拉 dsh web" |
| 接线 | `shell/main.cjs:1305-1324` | 条件命中（窗是 dsh-chat 且源是 connect.html 且 auto_dsh.enabled）→ `dshLaunch.startDsh(...)` |
| 拉起 | `shell/dsh-launch.cjs:88-190` | 探 3080：**没人听**→ `dsh web --no-open`；**有人在听**→ `dsh web --no-open --port 0`（另起一个，绝不动孤儿）；解析就绪行 `dsh web: http://127.0.0.1:3080/?token=…`（`dsh-launch.cjs:28,39-50`，**缺 token 判失败**） |
| 交 URL | `shell/main.cjs:1430-1469`（`w3ConnectDsh`） | 过**回环白名单** → `win.loadURL(tokenURL)`（1439）⇒ **本窗导航到官方 GUI**；只回 `host`；落**不含 token** 的回执两处（仓内 + userData） |
| 收尾 | `main.cjs:1320-1323` | 窗关 → `stop()`（Win 上 `taskkill /T` 连子孙，`dsh-launch.cjs:172-187`）——不留孤儿 |

**结论**：「APP 直接用官方 APP」的**主路已经在跑**——主人点顶栏「对话」芯片/托盘 → 窗 A 起 →
壳自己拉 `dsh web` → 窗 A 载官方 Web GUI（本地 127.0.0.1，token 只在内存）。**本次不动它**。

**与 2026-10-04 改道的边界（别混）**：那次风控拦的是 **Electron 直连 `chat.deepseek.com`**
（`windows.json:71,81-84` 记载：双组对照均弹「使用环境异常」）⇒ DeepSeek 网页移去主人自己的
Chrome。**本地 `127.0.0.1:3080` 的官方 DSH 面不受那条影响**（本机回环，无 CF 边缘）。两条路互不相干。

### 2.2 还剩三处"不完美"——改动点清单（**本次未执行**；执行前要主人点头 + 走镜像多维度）

> 口径：下面每条都写"文件:行 → 改什么 → 回滚怎么做"。**推荐先做 A（可选做 B），C 是纪律不是改动。**

**改动点 A（推荐）：面板左栏加一条"对话（官方 APP）"入口 —— 走开窗，不塞 webview**

- 为什么现在没有：`holo_pet_w3/panel/index.html:95-105` 的注释**故意不挂** `dsh-chat`，
  理由是"面板 webview 没有 `connectDsh` 口，硬挂只会显示没接上"——**这条理由成立**（webview 里
  载裸 URL 只会回 401）。本条改动**不违反它**：不做 webview 内嵌，只做**开窗**。
- 改什么（两处，改的是**我们自己的**面板页，不碰 DSH、不碰壳逻辑）：
  1. `holo_pet_w3/panel/index.html:61-106`（`PAGES` 数组）：加一条
     `{ id:"dsh-chat", name:"对话（官方 APP）", what:"壳自拉 dsh web 后载入官方界面（token 只在内存）", external:true }`；
  2. `holo_pet_w3/panel/index.html:130`（`pick(rel)`）：加一个分支——`external` 项不 `load()`，
     改调 `window.gbtW3.showWindow({id:"dsh-chat"})`（该口已存在：`shell/preload.cjs:51` → IPC
     `shell/main.cjs:1745` → 只认注册表 id，白名单安全）。
- 回滚：删上面两处的新增行（各一行/一个分支），面板回到现状；无任何数据或状态残留。
- 风险：低。不动 webview 安全面（`panel/index.html:114-129` 的 load() 原样），不动壳源码
  （守卫 B1/B4/B5 不受影响）；唯一行为变化=点一下开一扇**本来就存在**的窗。

**改动点 B（可选，纯文案）：connect.html 的"高级 · DSH"引导文与现况不符**

- 现况：`holo_pet_w3/shell/connect.html:74-94` 还写着"去看启动 `dsh web` 的终端、手贴带 token 的
  URL"；而 `auto_dsh`（2026-10-07 起）已自动接上——兜底文案该先说"**自动接上中…**；起不来才手贴"。
- 改什么：`connect.html:74-94` 与 `:80-91` 的说明/占位文案（**纯文案**：不改任何脚本、不动
  `connectDsh` 调用链、不增删 preload 口）。
- 回滚：`git checkout -- holo_pet_w3/shell/connect.html`（或恢复原三段文字）。
- 风险：极低；但**属于外壳源码**，仍要主人点头后走镜像多维度。另：`holo_pet_w3/window.js:657`
  工作台磁贴上的旧标注`"DeepSeek 原生对话（决策模块 · 免费网页）"`同理可顺手回正（一行文案）。

**改动点 C（纪律，不是改动）：并存三条硬约束（现状已满足，写死防漂移）**

1. **两扇窗各载各的**：窗 0（面板）内容区只载**本树 file://**（`panel/index.html:9` 口径 +
   `load()` 只接 rel 路径）；窗 A 载官方 GUI。互不加载对方内容 ⇒ **不存在相互顶掉**。
2. **我方面板进官方 APP 的路是"只加行"**：`profiles/web/cordis.patch.yml:63-68` 的 `gbt-master`
   insert 行（宿主半边挂 `/gbt-master` 路由；浏览器半边 `plugins/gbt-master` 以
   `dsh.client.inject:[dsh-client-ui-renderer, dsh-client-ui-sidebar]` 注入左栏「总面板」）。
   **它不 disable 官方行、不改官方行 config**（补丁语义：只覆盖自己点的 id）⇒ 官方契约零破坏。
   ⚠️ 唯一需要留意的现役覆盖：`cordis.patch.yml:83-172` 对 `llm-pi-ai` 是**整行 config 替换**
   （补丁语义，非深合并）——这是官方语义、见 §③；动它时要**重述所有保留键**。
3. **壳源码不许出现 DSH 内部标识**：守卫 `tools/codex-scripts/desktop-shell-guard.py:81-82`
   （`DSH_INTERNAL = ("@deepseek-ai/", "dsh-compaction", "dsh-command-", …)`）——改动点 A 只在面板页写
   `"dsh-chat"` 这个**我们自己的注册表 id**（不在禁止名单里），合规；改动点 B 只写文案，合规。

**为什么不做第四种更"深"的方案（列出理由，防将来有人重走）**：让面板 webview 内嵌官方 GUI ——
需要 (a) 面板拿到带 token 的 URL（须改 preload 动作面 + 改壳逻辑），(b) 官方 APP 允许被 webview
内嵌（同源/框架策略未知，未验证），(c) 一份 token 进两处渲染上下文。**收益（少一扇窗）不值这个代价**，
且会把"URL 只在内存、只回 host"的既有纪律拆口子。故不推荐。

---

## ③ 我方能力"一个不能落下"的核对：240 位挂到官方 APP 的哪一层

### 3.1 真源读数（引用，不重算口径）

| 真源 | 现读 | 机器判据 |
|---|---|---|
| `py -3.14 -m gbt_allinone list` | **240 位**（现跑计数） | 243 行输出里 `  - ` 条目 = 240 |
| `state/cap-bindings.json`（2026-10-08T06:55:16） | 能力 **240** · 触手承载 **9** · 直连 **231** · **未绑 0** · 触手域 **10**（121 项）· 无域缺能力 · 能量通道 **13**（活 **9**）· 资产标签 **270** | `orphans`：`caps_unbound=0`·`caps_bad_domain=0`·`caps_bad_channel=0`·`tentacle_domains_without_caps=0`·`dead_channel_carrying=0`·`mismatch_cap_vs_domain=0`·`mismatch_cap_vs_channel=0`；唯一非零=4 条通道不可用（承载数记 0，口径已写死） |

⇒ **三边（能力×触手×能量）零未绑**成立；本件负责回答的是**它们从哪一层进官方 APP**。

### 3.2 四层挂法（现状，逐层给证据）

1. **UI 层（官方 APP 里看我方面板）**：`gbt-master` 行（`cordis.patch.yml:63-68`）→ 官方 APP
   左栏「总面板」图标 + 会话头「上帝视角」入口（v1.2.0 全内嵌 iframe，零 window.open；
   自愈走 `plugins/gbt-master/lib/heal.js`，宿主路由每次现读）。**现役已接**。
2. **会话/agent 层（官方 APP 的模型真能调我方能力）**：默认 preset = **`gbt-spine`**
   （`~/.dsh/.agent-presets/gbt-spine/`，`settings.yaml` `agent-presets.default: gbt-spine` 现读）。
   它挂 24 个包（探针现算），其中关键两件：
   - `dsh-tool-pwsh`（本平台现役；`tool-bash` 按平台判据关）——**240 位的现役通路**：
     三主线道 persona 里写死"一切能力位走 `gbt_allinone.run_task` 唯一门"，模型经 pwsh 敲
     `py -3.14 tools/codex-scripts/five-dim.py cap <能力位> '<json>'` 或 `cap brain_execute`；
   - 委派/工作流/技能/计划/目标整套（`tool-subagent*`、`workflow-worker-thread`、`tool-workflow`、
     `tool-ralph`、`tool-skill`、`plan-mode`、`tool-goal`、`tool-todo`、`tool-web`、`tool-cordis`）。
   **现役已接**（这是"我们自己的能力进官方 APP"的**主缝**：preset 只加行、每会话合成、不动官方契约）。
3. **模型层**：`llm-pi-ai` 行（`cordis.patch.yml:83-172`）→ `gbt-potato`（云上拼接网 · 身份注入）
   / `gbt-free`（本机免费路由 8 个真调通模型）/ `gbt-local`（本机端点，GPU 到位换一行 baseURL）
   三家 provider 出现在官方 APP 的模型选择器里（`ui-model-selection` 已挂）。**现役已接**。
   另：`dsh-llm-qwen-local` bundle（`web/package.json:9`）提供本机 Qwen 端点 + 它的前端设置页。
4. **壳层（我方各窗与官方 APP 并存）**：触手视觉回传/数字人/记录本/能力统计等**11 扇我方窗**走壳
   IPC 动作口（`preload.cjs:19-23` 登记的动作面：`capFrame`/`message`/`summon`/`openExternal`…），
   页面在面板窗的 webview 里；官方 APP 在窗 A。**两套并存、互不顶掉**（§② 改动点 C）。

### 3.3 缺口（诚实）：240 位还缺"第一等工具面"

现状里模型调 240 位要**经 pwsh 敲 CLI**（可用、已验证，但不是第一等工具：无参数 schema、无
工具级审批渲染、无 `@` 引用）。补法候选（**均未执行**，动的是 `~/.dsh` 与 profile patch，须主人点头）：

- **候选甲（推荐先做的）**：`dsh-mcp-client`（**现装未用**）+ 我方一个 MCP server 包住
  `run_task` 唯一门 ⇒ 240 位以 MCP 工具形态出现在**每个会话**（preset 加一行 `mcp-client` +
  server 清单）；代价=多一个子进程与信任面，收益=第一等工具面、别人家客户端也能用。
- **候选乙**：仿 `gbt-master` 写一个宿主插件，注册 N 个工具行（`ctx.tools`）——更贴官方契约，
  但要把 240 位做成工具目录（工作量大；可先只暴露 `gbt_cap` 一个总工具）。
- **候选丙（零改动）**：维持现状（pwsh + 三主线道指引）——**已可用，不阻塞任何事**。

### 3.4 零遗漏判据（机器可核）

- 能力侧：`cap-bindings.json.counts.caps=240` 且 `orphans` 全 0（4 条死通道按"承载数 0"另计）；
- 接入侧：本件探针复跑应稳定给出 `未启用 20` 清单；20 个里**没有一个是"我方能力"**
  （全为官方另面/可选件）⇒ **我方能力在 DSH 侧的零遗漏 = 断言成立**；
- 会话侧：`state/dsh-census.json` 的 `packages[*].default_preset` 可逐个复查谁在默认会话里。

---

## ④ 不接入的与理由（明确列出，防"为什么不做"反复拉扯）

| 不接入项 | 理由 |
|---|---|
| `~/.dsh/settings.yaml`、`~/.dsh/.agent-presets/**`（含 gbt-spine）的**任何改动** | **守卫 B2 哈希基线盯着**（`desktop-shell-guard.py:76-78` `DSH_WATCH` 含 `settings.yaml`、`.agent-presets`；`:104-110` 还记结构指纹与 `defaultPreset` 等安全键）⇒ **改它要先问主人**，本次一个字节没动 |
| 改 `dsh-base` / `dsh-web-app` bundle 包内任何文件 | **会破坏官方契约**（升级即被覆盖；且 §口径二：用户层才是我们的层）。要改行为走 `cordis.patch.yml` 覆盖同 id |
| disable / 覆写官方行（除既有 `llm-pi-ai` 覆盖外） | 保持"只加行"——这是 gbt-master 与官方共存不打架的根因（§② C.2） |
| token 落盘 / 回显 / 替主人找 token | 纪律三条（`main.cjs:1425-1429` 写死）：不落盘、不回显、只回环；`connect.html:93` 明写"故意不提供自动找 token" |
| `dsh-web-search-deepseek` 的密钥 | 缺凭据：`apiKeyEnv` 走**凭据 seam**（settings/env 引用），且**不代持**；没配则 web_search 报 `MISSING_CREDENTIAL`（fetch 匿名可用）。要开由主人配 |
| `dsh-hooks-codex` / `dsh-hooks-claude-code` | 钩子=给外部配置**拦截权**（能改工具调用），属安全面扩张 ⇒ 要主人拍板 + 先定 hooks 文件归属（§① 表） |
| `dsh-schedule` + `ui-schedule` | 会**自己**按时间发提醒（宿主行 + UI 行 + overlay 三件一起开）；未经拍板不擅自让机器自己动 |
| `dsh-webhook` / `dsh-webhook-github` | 对外开口（HTTP 入口→建会话），需签名密钥与暴露面设计；无凭据、未授权 |
| GitHub/其它外部凭据类（octokit 等库件） | 库件被树引用，但**没有我们的凭据**；不试授权作用域（我方授权台账多数为 0，纪律） |
| `dsh-sdk-*` / `dsh-acp*` / `dsh-headless` | 不是"接入 APP"的料，是**另起 profile**（独立命令线）；要用按官方 CLI 表单独起，不动 web profile |
| 官方遥测行 `dsh-session-telemetry-otel` 的**关闭** | 现役 `FEEDBACK_ONLY`；关它=改行为，**要主人拍板**（env `DSH_TELEMETRY_MODE` 可关，但本次不动） |
| `dsh-tool-bash-persistent` / `dsh-tool-str-replace-editor` / `dsh-bash-local` / `dsh-workflow`(seam 本体) | 与本平台现役路线重复或无独立价值（Win 走 pwsh；编辑器走 tool-fs；seam 本体由 worker-thread 实现+preset 行覆盖）⇒ 接了只增加审计面 |
| 面板 webview 内嵌官方 GUI 的"深方案" | 要拆"URL 只在内存/只回 host"的口子（§② 末）⇒ 收益不值，不做 |

---

## 附：证据与复跑

```
# ①③ 的读数（全部现读现算，只读盘）
py -3.14 tools/codex-scripts/dsh-census.py --out state/dsh-census.json
# 我方能力位
py -3.14 -m gbt_allinone list | grep -c "^  - "          # → 240
py -3.14 -c "import json;print(json.load(open('state/cap-bindings.json',encoding='utf-8'))['counts'])"
# 官方契约自查（壳不改 DSH 的机器证据）
py -3.14 tools/codex-scripts/desktop-shell-guard.py
```

台账 `state/dsh-census.json` 内含：`packages[*]`（每个包的族/状态/挂载行 id/层/被哪些 preset 挂/
sha 证据）· `rows[*]`（154 行逐行 id→name→层→disabled）· `presets[*]`（5 个 preset 的挂载集）·
`app_surface.anchors`（§② 的全部 文件:行 锚点）· `ours`（240 位与三边绑定读数）。

**本次未执行的改动（重申）**：§② 改动点 A/B 全部**未执行**；`~/.dsh/**`、`gbt_allinone/**`、
`holo_pet_w3/shell/**`、`holo_pet_w3/panel/**` **本次零改动**。执行任何一条前：主人点头 + 走镜像多维度。

---

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
