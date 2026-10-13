# DSH MCP 桥（甲方案）· 把 `run_task` 唯一门暴露成官方 APP 的第一等 MCP 工具

> 一句话：官方 APP 里装着一个**未启用**的官方包 `@deepseek-ai/dsh-mcp-client`
> （"MCP client bridge: connects to MCP servers and registers their tools on `ctx.tools`"）。
> 本目录是它**我方那一侧**的服务器：一个最小 MCP 服务（stdio），
> 把我们的 `gbt_allinone.run_task` **唯一门**桥成官方 APP 模型能直接调的原生工具
> （`mcp__gbt__*`），不再需要经 `tool-pwsh` 敲 CLI。

---

## 1. 目录里有什么

| 文件 | 是什么 | 会不会进镜像维度 |
|---|---|---|
| `server.py` | 最小 MCP 服务（stdio · 换行分隔 JSON-RPC 2.0；只读白名单 + 框架策略层**双闸**） | 会（镜内件） |
| `selfcheck.py` | 最小自证：真起服务器、真发 MCP 帧、8 条判据（含写类默认不出现的负对照） | 会 |
| `interop-check.mjs` | **官方同款 SDK 互操作自证**：用本机现装的 `@modelcontextprotocol/sdk` 真连一次（5 条判据） | 会 |
| `rehearsal-plan.json` | 镜像排练计划（假设/架构/步骤/环境契约/验收/回滚） | 会 |
| `rehearse.py` | **可复跑**排练驱动器：六步按序真跑、任何一步红就停 | 会 |
| `README.md` | 本文件（配置行以**文本**给出、攻击面与边界） | 会 |

## 2. 起法（真命令，本机已验证）

```bash
py -3.14 plugins/dsh-mcp-bridge/server.py --repo-root "C:/Users/ADMIN/Desktop/GBT小土豆V8"
```

- 传输 = **stdio**（不监听任何端口；没有 HTTP 面）。
- **stdout 只走协议帧**：服务启动第一件事就是把 `sys.stdout` 换成 stderr，
  协议帧走另存的原始句柄 —— 任何库里的 `print` 都污染不了帧流。
- `--repo-root` 可省：默认从本文件向上找 `gbt_allinone/__init__.py`（镜像维度里的同一份件也能找到）。

最小自证（**这条命令的原文读数要贴给主人**，不许只写"应该是通的"）：

```bash
py -3.14 plugins/dsh-mcp-bridge/selfcheck.py
# 全过 => 末行 SELFCHECK OK（退出码 0）；任一不过 => SELFCHECK FAIL（退出码 1）

node plugins/dsh-mcp-bridge/interop-check.mjs
# 用**官方同款 SDK**（本机 ~/.dsh/profiles/node_modules/@modelcontextprotocol/sdk）真连一次
# 全过 => INTEROP OK（退出码 0）。这条是"官方 APP 那侧真能连上"的直接证据。
```

🔴 **实测坑（interop 首跑的红灯，写在这防重踩）**：官方 SDK 用 **cross-spawn** 起服务器，
它按 `;` 拆 `PATH` 找命令；**Git Bash 下的 `PATH` 是 POSIX 形态**（`/c/WINDOWS:...`）
⇒ 它会报 `spawn py ENOENT`。DSH 自己是原生 Windows PATH（桌面壳起的），`py` 能命中；
但若某次是在 Git Bash 里手起原生组合，把配置里的 `command: py` 换成绝对路径
`C:/Windows/py.exe` 即可（`interop-check.mjs` 的候选表就是这么排的）。

## 3. 怎么接进 DSH（**只给文本，不代改**）

放哪儿：`~/.dsh/.agent-presets/gbt-spine/agent.cordis.yml` —— **文件末尾追加**，只加行、不改任何既有行。
为什么是 preset 层而不是宿主层：官方 preset 文件自己写明
「An AGENT PRESET holds what one session contributes to those registries: its tools, its persona,
its prompt sections」——MCP 工具就是"会话贡献的工具"，属 preset 面（宿主面那份 `agent.cordis.yml`
被 `dsh-web-app` 补丁整块 disable，是官方设计）。

把下面这段**原样**追加到 `agent.cordis.yml` 末尾（`~/.dsh/**` 的改动**要主人点头**，且会动守卫 B2 的哈希基线）：

```yaml
# ── GBT小土豆V8 · 甲方案：run_task 唯一门 → 第一等 MCP 工具 ────────────────────
# 只读优先：本桥默认只暴露读类工具；写类要票且默认不出现（见本目录 README §4）。
- id: mcp-gbt-bridge
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: gbt
    transport: stdio
    command: py
    args:
      - '-3.14'
      - 'C:/Users/ADMIN/Desktop/GBT小土豆V8/plugins/dsh-mcp-bridge/server.py'
      - '--repo-root'
      - 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
    cwd: 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
    toolCallTimeoutMs: 120000
    failOnStartupError: false
```

接上之后：新开一个会话（或 F5 一次），模型工具列表里应出现
`mcp__gbt__run_task` · `mcp__gbt__alerts` · `mcp__gbt__selfscan` · `mcp__gbt__capability_status`。
**复验判据（机器可核）**：任一会话里让模型调 `mcp__gbt__alerts`，返回体里必须有
`gbt_stamp.framework = "GBT小土豆"` —— 有钢印 = 真过门；没有 = 没接上，别信"看着像接上了"。

⚠️ 若这台机器上 `py` 解析不成（见 §2 的 cross-spawn 实测坑），把 `command: py` 与 `args` 头一项
换成绝对路径的成对写法：`command: C:/Windows/py.exe` + `args: ['-3.14', ...]`。

要**开写**（不建议默认开）：在 `config.env` 里加一行
`GBT_MCP_BRIDGE_WRITES: '1'`（开了之后写类仍要**票**，没票即拒）。

## 4. 攻击面与边界（必须写清的四个问题）

**① 谁能调？** 谁能在这个 DSH 会话里发工具调用，谁就能调 —— 也就是**官方 APP 里的模型**（以及
经它转手的任何会话输入）。所以本桥按"**对面是不可信调用方**"设计，**不继承主人的全通标记**：
服务启动时主动摘掉 `GBT_OWNER_SESSION`（除非显式 `--trusted`）⇒ 在框架眼里它是**未受信会话**，
要票的动作走真票闸。

**② 能看到什么？** 默认只看到**读类**：`alerts`（异常摘要）· `selfscan`（五维体检）·
`capability_status`（240 位目录）· `run_task` 的**读类白名单**（19 个 kind：声带/体检/授权状态/
盘点/署名/卫生/镜像状态/路由/密钥链**状态**/多模态端口**状态**/触手**读类 op**…）。
写类（`logbook_append`、以及白名单外的任何 kind）**默认整个不出现在工具列表里**。

**③ 写类怎么办？** 三层，逐层收紧：
1. **不出列表**：不开 `--enable-writes`，写类工具根本不出现在 `tools/list`（模型看不见，也没法调）；
2. **两道闸**：`kind` 必须在**显式白名单**里（第①道）；再过**框架自己的策略层**
   `security/policy.evaluate(kind, payload)`，`scopes` 非空即拒（第②道）——
   payload 一级也拦（例：`selfscan` 带 `autofix=true`、`inventory` 带 `fix=true` 都会被拒，
   因为这两处框架策略层是 fail-open，**本桥不跟着 fail-open**）；
3. **票**：即便开了写，也要消耗真票（`auth_gate`）。没票 ⇒ 拒绝并回明"缺哪张票、
   主人要在终端跑哪一行"。**桥自己不发授权**（发送授权只能人在终端/手写授权文件）。

**④ 凭据呢？** 本桥**一个凭据都不需要**：不读密钥服务、不读环境里的钥匙。
`dsh-mcp-client` 给 stdio 子进程的环境是**清洗过的**
（删 `*KEY|PASSWORD|SECRET|TOKEN*` 与 `DSH_*`），本桥再往上**没有加任何 `env`** ——
子进程手里没有主人的钥匙。要写类时才需要"票"，票是授权不是密钥。

**边界（明确不做）**：不监听端口；不代理 MCP resources/prompts（官方包也只桥工具）；
不替主人拿 token；不改 `~/.dsh` 任何文件；不跑 `mirror_ascend` / `mirror_release` / `pipeline_submit`。

## 5. 已知未验证项（诚实清单）

- **DSH 侧挂载未实测**：本次不许动 `~/.dsh/**`，所以"追加那一段配置后工具真的出现在官方 APP 里"
  这件事**没有在真 DSH 上验证过**；上表 §3 的复验判据就是为这一步准备的（钢印法）。
- **官方 SDK 版本耦合**：本桥按 MCP 规范（stdio/JSON-RPC 2.0）实现 `initialize` / `tools/list` /
  `tools/call` / `ping`；`@modelcontextprotocol/sdk ^1.12.0` 若改协议形状，要跟着改。
- **非 probe 调用的框架副作用**：任何一次 `run_task` 都会跑框架的"产出即绑"钩子（节流 3 秒，
  只在仓内资产根生效）—— 这是框架总闸的既有行为，**不是本桥引入的**，但在排练里也会发生。

---

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
