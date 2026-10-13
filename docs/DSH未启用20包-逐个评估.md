# DSH 未启用 20 包 · 逐个评估（只读）

> 口径：**只读盘**（`~/.dsh/profiles/node_modules/@deepseek-ai/<pkg>/package.json` + `README.zh.md` 现读），
> 台账引用 `state/dsh-census.json`（只读）。**本次没改 `~/.dsh` 一个字节**，也没跑任何 `--profile` 另起面。
> 机器可读版：`state/dsh-20pk-assessment.json`（同样 20 条、同样的建议分类）。
> 结论口径：**接**=建议启用（写清接法与回滚）· **先做最小验证**=有价值但要先在隔离面验证或先定归属（不动默认组合）·
> **不接**=无当期需求 / 与本平台现役路线重复 / 无独立价值。

## 一眼决定（20 行）

| # | 包 | 是什么（半句） | 建议 | 若接要动哪一行（要点） | 爆炸半径一句话 |
|---|---|---|---|---|---|
| 1 | `dsh-mcp-client` | MCP 客户端桥：连 MCP server 把工具注册进 `ctx.tools` | **接** | 默认 preset 末尾 append 一段（见 `docs/MCP桥-甲方案-实施与排练.md` P1） | 多一个 stdio 子进程；工具面由我方桥的只读双闸收口 |
| 2 | `dsh-time-context` | 给模型一只时钟（当前时间/时区/经过时长） | **接** | 同上，末尾 append 两行 + `refreshIntervalMs` 节流 | 每步多一条上下文消息（token），不写盘不出网 |
| 3 | `dsh-schedule` | 持久提醒（同一 live 会话 follow-up；重启不丢） | 先做最小验证 | 官方形式 `dsh web --patch .../schedule/cordis.yml`（不动默认组合） | 会**自己**按时发提醒；只在 live 会话内交付 |
| 4 | `dsh-hooks-codex` | 跑 Codex `hooks.json` 的 5 个钩子点（可拦工具/提示词） | 先做最小验证 | 宿主面孔或独立 profile + `configPath`；先空配置 | **高**：外部配置获得工具拦截权 |
| 5 | `dsh-hooks-claude-code` | 同上，跑 Claude Code hooks 配置 | 先做最小验证 | 同上；与 codex 那条**别同时开** | **高**：同上 |
| 6 | `dsh-hook-protocol` | 上面两个钩子桥的共用线协议（库件） | 不接 | 接钩子桥时自动进依赖闭包，别单独写行 | 不单独挂 ⇒ 无面 |
| 7 | `dsh-webhook` | Host 侧 webhook 规则运行时（唯一动作=建会话） | 不接 | 宿主面 + 自写规则插件；还需 workspace/preset 限定 | **高**：对外事件→以我们的权限起会话 |
| 8 | `dsh-webhook-github` | 签名 GitHub webhook 适配器（HMAC 验签→分发） | 不接 | 需 webserver + webhook runtime + `secretEnv` 密钥 + 规则 | **高**：公网入口；202 只代表已分发 |
| 9 | `dsh-workflow` | 工作流 **seam 本体**（`ctx.workflowEngine`） | 不接 | 只有"换引擎"才写行；默认会话已挂实现+工具 | 重复挂易与 preset 隔离域打架 |
| 10 | `dsh-bash-local` | POSIX 默认 Bash 执行器（无隔离） | 不接 | 换平台才谈 | 本机 Win 走 pwsh ⇒ 收益为零 |
| 11 | `dsh-tool-bash-persistent` | 面型持久 bash（cwd/变量跨调用保留） | 不接 | 会话面 append + 需 PTY 后端 | 常驻终端 ⇒ 审计面变大 |
| 12 | `dsh-tool-str-replace-editor` | Claude Code 风格 `str_replace_editor` 编辑器 | 不接 | 会话面 append | 与 `tool-fs` **重复**：多一条写路=多一份审计面 |
| 13 | `dsh-tmux-context` | 让模型知道自己在 tmux 的哪个 pane | 不接 | 会话面 append | 本机无 tmux ⇒ 什么都不注入 |
| 14 | `dsh-headless` | `dsh --profile headless "<任务>"` 一次性跑完退出 | 不接 | **不动任何文件**（独立命令线；要用直接起） | 不进 web 面；用它就跑真任务 |
| 15 | `dsh-sdk-app` | `--profile sdk`：stdio JSON-RPC 运行时（可编程） | 不接 | 不动任何文件（独立 profile） | 起来后整棵组合暴露在 stdio 上 |
| 16 | `dsh-sdk-minimal` | 最轻的 SDK profile bundle（JSON-RPC+持久 shell） | 不接 | 不动任何文件（独立 profile） | 同上（面更小） |
| 17 | `dsh-sdk-jsonrpc-server` | SDK 的 stdio JSON-RPC **服务端插件**（库件） | 不接 | 随 sdk 面被拉起，别单独写行 | 不单独挂 ⇒ 无面 |
| 18 | `dsh-sdk-protocol` | SDK **线协议**（库件） | 不接 | 不适用 | 不单独挂 ⇒ 无面 |
| 19 | `dsh-acp` | Agent Client Protocol 服务端（给 ACP 编辑器驱动 agent） | 不接 | 不动任何文件（`dsh --profile acp`） | 同 sdk 一族：stdio 控制面 |
| 20 | `dsh-acp-app` | ACP profile 的 bundle | 不接 | 不动任何文件 | 同上 |

**计数**：接 **2** · 先做最小验证 **3** · 不接 **15**。

## 最该先接的 2 个（与理由）

1. **`dsh-mcp-client`** —— 收益最大、攻击面已收口：它把 **240 位能力从"经 pwsh 敲 CLI"升成第一等工具**
   （有参数 schema、进工具目录、可被 `@` 引用）。我方桥的仓内件**已成形 + 排练全绿 + 官方同款 SDK 真连通**，
   接法就是**末尾 append 一段**、回滚就是删那一段；读写边界默认收在"只读白名单 + 框架策略层双闸"。
2. **`dsh-time-context`** —— 成本最低、补的是**真实缺口**：我们的长程会话跨天跑，而**模型不知道"现在几点"**
   （persona 里没时间，只能靠猜）。两行配置 + `refreshIntervalMs` 节流；不写盘、不出网、不碰凭据，随时可撤。
   （`dsh-schedule` 排第三：价值也高，但"机器自己按时发提醒"要先过主人的拍板线。）

## 先做最小验证的 3 个（验证什么 · 判据 · 纪律）

- **`dsh-schedule`**：用官方给的 overlay 起**一个隔离会话**（`dsh web --patch .../schedule/cordis.yml`，不写盘），
  判据：①"5 分钟后提醒我 X"真的作为 follow-up 回来 ②`schedule_list` 按创建顺序列 ③cancel 后未知 id 报
  `schedule_not_found` ④重启后提醒仍在（逾期等 live 会话）。**验证通过也不等于进默认组合**——那要主人拍板。
- **`dsh-hooks-codex`**：先**定归属**（谁的 hooks.json、放哪、谁能改），再用**空配置**验证"能挂、能撤、不拦错"；
  判据：空配置时 agent 行为零变化；放一条"总 deny"的钩子时该工具真被拦；撤钩子后恢复。
- **`dsh-hooks-claude-code`**：同上；**与 codex 那条二选一**（两条钩子桥叠加会让拦截顺序与多钩子合并变复杂）。

## 不接的 15 个（分组给理由，别再逐个拉扯）

- **独立 profile 面 7 个**（`dsh-sdk-app`·`dsh-sdk-minimal`·`dsh-sdk-jsonrpc-server`·`dsh-sdk-protocol`·
  `dsh-acp`·`dsh-acp-app`·`dsh-headless`）：**不是"接入 APP"的料**，是另一条命令线。
  要用就按官方 CLI 表独立起（`dsh --profile sdk|acp|headless`），**不改 web profile 一行**。
  `sdk-minimal`/`headless` 可当将来自动化联调的"第二腿"，但那是**独立决定**，不是现在接进 APP。
- **库件/无独立价值 2 个**（`dsh-hook-protocol`·`dsh-workflow`）：seam/协议本体，被实现件依赖；
  默认会话里机制已通（`workflow-worker-thread` + `tool-workflow` 已挂），单挂只会造成两份服务/两份词汇。
- **平台不符或功能重复 4 个**（`dsh-bash-local`·`dsh-tool-bash-persistent`·`dsh-tool-str-replace-editor`·
  `dsh-tmux-context`）：Win 走 pwsh（bash 那两条收益为零）；编辑器与现役 `tool-fs` 重复；
  本机无 tmux ⇒ 什么都不注入。接了只增加审计面与维护面。
- **对外触发面 2 个**（`dsh-webhook`·`dsh-webhook-github`）：会把外部事件变成**以我们的权限起的会话**，
  需要签名密钥、来源限制、规则限定（workspace/preset/权限档）。**我们当期没有这个需求**
  （GitHub 那一路我们走主动拉取 `devour_github`，不是被动 webhook），且无凭据、未授权 ⇒ 不开口子。

## 复跑（一条命令重算本件引用）

```
py -3.14 tools/codex-scripts/dsh-census.py --out state/dsh-census.json   # 台账（只读复算；注意：本次未重跑，台账是 2026-10-08 的现读）
py -3.14 -c "import json;d=json.load(open('state/dsh-20pk-assessment.json',encoding='utf-8'));print(len(d['packages']),d['summary'])"
```

> 本件与 `docs/DSH隐藏能力普查与接入方案.md` 的分工：普查件讲**包族与挂载/接入面**（240 = 各层怎么分），
> 本件讲**没启用的那 20 个到底接不接、要接动哪一行**（决策用）。两件冲突以现读为准。

---

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
