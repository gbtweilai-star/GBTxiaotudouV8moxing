# 蒸馏 · REA（Reverse Engineer Anything）

> 出处：**现读** `github.com/morluto/rea`（README 18,330 字符 + `docs/installation.md` 53,440 字符，2026-10-12 抓取）
> npm：`rea-agents` · 许可 **MIT** · 官网 rea.tools · 已有 DSH 插件页

## 一、它是什么（一句话）

**一个 MCP**：`One MCP for reverse engineering across binaries, applications, and runtime behavior`。
把"逆向"做成**带证据的问答** —— 你问，它查，**每条结论都带 evidence**。

## 二、它怎么工作（How REA works · 原文口径）

1. Agent 通过 **MCP** 调 REA → 检查目标、**追踪相关代码**
2. REA 返回 **findings + 它们的证据（evidence）**
3. Agent 拿这些去**追问 / 解释行为 / 写并测试自己的实现**
4. **CLI 命令走同一套 workflow**（人机同一条链）

## 三、能分析什么（七类目标 · 各自前置）

| 目标 | 它返回什么 | 前置 |
|---|---|---|
| **本地二进制** | 伪代码 / 汇编 / 字符串 / 符号 / 调用与引用 | Hopper / Ghidra / IDA |
| 离线 ELF 布局 | sections / segments / 原始符号与重定位 / 静态缓解候选 | Linux x64 + pwntools |
| WASM 产物 | 校验 / sections / 精确的 import-export WAT | WABT 1.0.42 |
| EVM 字节码 | dispatch 选择器 / 字节偏移 / 推断参数与可变性 | Linux x64 本地 raw/hex |
| 记录的 Linux 崩溃 | 每线程寄存器/信号 + 可选映射候选 | pwntools（可选 GDB/pwndbg） |
| **JavaScript / Electron** | 模块 / imports / source maps / 路由 / **IPC** / 原生插件关系 | **只要 Node.js + npm** ← 门槛最低 |
| **网站** | 页面结构 / 脚本 / 网络观察 / 截图 | Chrome 系浏览器 |

## 四、怎么装（原文）

```bash
npx rea-agents setup      # 选 agent → 给你看改动计划 → 批准 → 重启 agent
```
- 支持 **Claude Code · Codex · Cursor · Gemini CLI · Grok Build** 等（**含我们刚接好的 Codex** ✓）
- **会改 agent 配置**（先给计划、有备份 ✓）
- Node 要求：22.x(>=22.19) / 24.x(>=24.11) / 26+（**23/25 不支持**）

## 五、对我们（GBT小土豆V8）意味着什么

1. **同一条精神**：它的 `findings + evidence` = 我们的「**拿实质性证据说话**」✓
2. **同族触手**：`omni_web`（看结构/读源码/改文件）· `devour_github`（吞仓 → 知识胶囊）· 它（**逆向看穿实现**）
3. **最划算的入口**：**JS/Electron**（只要 Node ✓）与**网站**（只要 Chrome ✓）—— 不需要 Hopper/IDA/Ghidra（那些是要买/要装的）
4. **接法（按本仓 intake 七步法）**：克隆落位 → 只读体检（供应链 ✓）→ 包成能力位 → 接分派 → 咬触手 → 挂判据
5. ⚠️ **红线照旧**：它只是**看**（分析）✓；任何"拿它去动别人系统"的动作仍过我们的门（`deploy_publish`/隐私 ✓），**AI 不许自发放行**

> ⛔ 开发者：自由的风 · 本署名不可删除、不可篡改归属
