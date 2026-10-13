# 蒸馏 · CyberStrike（CyberStrikeus/CyberStrike）

> 出处：**现读** `github.com/CyberStrikeus/CyberStrike`（README 27,691 字符，2026-10-13 抓取 · **3129★** · TypeScript）
> 官网 `cyberstrike.io` · npm `@cyberstrike-io/cyberstrike` · 许可 **AGPL-3.0**
> 胶囊：`gbt_allinone/store/devoured/devoured_cyberstrikeus_cyberstrike/`

## 一、它是什么（一句话）

「**The first open-source AI agent built for offensive security**」—— 终端里的自动化渗透 agent：
接你已有的 LLM 订阅，做成 13+ 专职 agent / 7,600+ 安全技能 / 120+ OWASP 用例 /
56+ 内置工具 / 176+ MCP 工具的自主红队。

## 二、它的 Intelligence Layer（**我们真正要蒸的那一层**）

原文：「It's an **intelligence layer** that transforms any AI model into an offensive security specialist.
… injects domain-specific context — OWASP testing methodology, vulnerability patterns, attack chain
reasoning, and **tool orchestration logic** — into every interaction. The model doesn't need to know
security; CyberStrike teaches it.」

它自报四条件：

1. **Schema normalization** — 任何 provider 都归一成结构化输出
2. **Context guard** — 防提示泄漏，把 agent 钉在**当前测试阶段**
3. **Provider auto-detection** — 认端点、配最优传输
4. **Tool orchestration** — 按**发现**串安全工具，不是固定脚本

## 三、我们蒸出四条（不是复制它的代码）

| 序 | 取法 | 原话 | 我们的落点 |
|---|---|---|---|
| ① | 阶段聚焦 + 上下文护栏 | `Context guard — Prevents prompt leakage and keeps the agent focused on the current test phase` | 一次只推一个阶段（同 gbt-command「一步一位」） |
| ② | 按发现编排，不跑死脚本 | `Tool orchestration — Chains security tools intelligently based on findings, not fixed scripts` | 下一步由**上一步的读数**决定 |
| ③ | 结果结构化归一 | `Schema normalization — Structured output from any provider` | 工具输出一律收成统一信封（**门已在做**） |
| ④ | 授权范围纪律（**我们加严，不是抄的**） | （它讲 offensive security；我们只做已登记授权） | 未登记目标一律拒 · AI 不许自发放行 |

## 四、为什么是「取法」不是「建平行位」（立项理由）

它干的活我们**已经有 26 个安全位**：`sec_surface` / `sec_scan` / `sec_chain` / `sec_defenses` /
`pentest` / `redteam_recon` / `credential_steal` / `llm_redteam` / `code_audit` / …，
编排通道也有 `omni_plug` / `mcp_call` / `mcp_tools` / `mcp_connect` / `desktop_commander`。
照抄建个平行的「cyberstrike 位」= 撞仓规「**新增即清旧**」的「同功能两份」。
⇒ 本位只**蒸取法**；它的**规模**（13+ agents / 7600+ skills）**不取**，它的
**Bolt 远程执行 / 后渗透 / Web UI 不取**（那是攻击性动作）。

## 五、落点（三处齐 · 零作用域）

- 原生位：`pentest_distill`（登记 `caps_registry.py` · 分派 `api.py` · 图鉴 `omni build` ⇒ 291 位）
- 入口：`py -3.14 tools/codex-scripts/five-dim.py cap pentest_distill '{"op":"method"}'`
- 门：`policy.evaluate('pentest_distill').scopes == ()` —— **零作用域**（只读 + 纯算）
- ops：`method` / `tools`（现读 `caps_registry.BENIGN_CAPS` 报安全域可编排位 + 通道）/ `provenance` / `where`

## 六、红线照旧

本位只是**编排取法**；任何"真去打"的动作仍走既有安全位 + 授权门（`pentest` 未登记目标一律拒 ·
`process_execute` / `deploy_publish` 等），**AI 不许自发放行**。
**许可**：AGPL-3.0 ⇒ 只引用不复制；若日后复用其实现，许可需主人亲自确认。

> ⛔ 开发者：自由的风 · 本署名不可删除、不可篡改归属
