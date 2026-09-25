# SKILL VETTING REPORT

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

- 根目录：`.scratch\vetting\feature-dev`
- 扫描时间：2026-09-23T06:28:38
- 规则版本：1.0　基线载入 0 条

## 总账

| 扫了 | 干净 | 有发现 | 发现总数 | 其中 high |
|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 0 |

## 按规则分布


## 样例（前 15 个技能）

## 规则表

- `GBT-SK-1`（high）：索要 API key / 凭据 / 密码
- `GBT-SK-2`（high）：破坏性命令
- `GBT-SK-3`（high）：向未知服务器外泄数据
- `GBT-SK-4`（medium）：修改系统配置或安装软件包
- `GBT-SK-5`（high）：伪装成系统指令 / 提示注入

## 诚实边界

1. **静态规则，会有误报** —— 词面命中 ≠ 真恶意。
2. 这是**待人工审的线索**，不是判决；按 `AGENTS.md`，装之前仍须人工过目。
3. 本工具**只读、只报告**，不拒绝、不删除任何 skill。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

---

# 人工审查补记（第 47 轮 · 上面那份工具报告**覆盖不到**的部分）

审查对象：`https://github.com/secondsky/claude-skills/tree/main/plugins/feature-dev`（主人 2026-09-22 给的链接）
审查时间：2026-09-23T06:28 起　·　**结论：未安装任何东西，等主人确认**

## 0. 🔴 先补一件**工具报告没说**的话 —— 分母

上面那张总账写的是「扫了 **1** / 干净 **1**」。**那个 1 是 `skills/feature-dev/SKILL.md` 一个文件。**
这个插件在盘上是 **8 个文件**；`skill_vetting.py` 的规则**只认 `SKILL.md`**，
`agents/*.md` 与 `commands/*.md` **它根本不看**。

> ⇒ **「干净」的范围是 1 个文件，不是"整个插件干净"。**
> 这正是本会话一直在打的病（FR-8：**报了数字却没给"只检查了一部分"起名**）——
> **这回犯病的是我自己的工具、在我自己要在报告里引用的那份读数上。**
> 下面第 1 节 7 个文件是我**逐字读**的；工具没读的部分，由人补上，并**在此写明是人工读的**。

## 1. 文件清单（8 / 8 全部逐字读过 · 字节数与 GitHub API 报的**逐一相符**）

| 文件 | 字节 | 谁读的 | 判定 |
|---|---|---|---|
| `skills/feature-dev/SKILL.md` | 9715 | 工具 + 人 | 干净 |
| `commands/feature-dev.md` | 5115 | **人（工具不看）** | 干净 |
| `agents/code-explorer.md` | 2115 | **人** | 干净 |
| `agents/code-architect.md` | 2259 | **人** | 干净 |
| `agents/code-reviewer.md` | 2994 | **人** | 干净 |
| `.claude-plugin/plugin.json` | 767 | **人** | 干净（无 hook / 无 postinstall） |
| `.codex-plugin/plugin.json` | 1367 | **人** | 干净（无 hook / 无 postinstall） |
| `README.md` | 11697 | **人** | 干净 |

下载时逐个核对字节数（11697 / 9715 / 5115 / 2259 / 2115 / 2994 / 767 / 1367）= API 元数据 ⇒ **拿到的是原件，不是被截断的页面**。

## 2. `AGENTS.md` 五道门逐条判

| 门 | 判 | 依据 |
|---|---|---|
| 索要 API key / 凭据 / 密码 | **无** | 全文无任何 key/token/密码字段 |
| 破坏性命令（`rm -rf` / 删除 / 格式化） | **无** | 8 个文件里**没有任何脚本**，只有 Markdown + 2 个 manifest |
| 向未知服务器外泄数据 | **无** | 无端点、无上传；唯一网络件是 agent 的 `WebFetch`/`WebSearch`（**只读**） |
| 修改系统配置 / 安装软件包 | **无** | 无 `pip install` / 无 postinstall / 无 hook |
| 伪装成系统指令 / 提示注入 | **无** | 无"忽略以上指令"类话术 |

**权限面（frontmatter 实测）**：三个 agent 的 `tools` 都是
`Glob, Grep, LS, Read, NotebookRead, WebFetch, TodoWrite, WebSearch, KillShell, BashOutput`
—— **没有 `Write` / `Edit` / `Bash`**；`SKILL.md` 的 `allowed-tools` 才含 `Write/Edit/Bash`，
但那是**它建议主 agent 用的**，不是它自带可执行件。⇒ **无自带执行面。**

## 3. 人工读出来的两处**内部矛盾**（工具查不出：这是语义不是词面）

### 3.1 置信度档位**自相矛盾**（三份文档里两份在描述做不到的事）

- `agents/code-reviewer.md` 明文：**「Only report issues with confidence ≥ 80.」**
- 而 `SKILL.md` 与 `README.md` 都写它的输出是
  「Critical issues (confidence **75-100**)」+「Important issues (confidence **50-74**)」。

⇒ 按 agent 的指令，**50-74 与 75-79 这两档根本不会被报出来**，
但两份文档告诉使用者"会收到"。**这是文档在描述一个被明令禁止的行为** ——
使用者会以为"没报 = 没有 50-79 的问题"，而真相是"**这一类压根不在报告范围里**"。

> 这条与主人这条目标**同源**：它不是安全问题，是**读数口径问题** ——
> 「没看到」被写成了「没有」。（本机第 43/46 轮同款：`coverage_note` 那两条。）

### 3.2 版本号**三方不一致**

| 出处 | 版本 |
|---|---|
| `skills/feature-dev/SKILL.md` frontmatter | `1.0.0` |
| `README.md`（末尾 `## Version`） | `1.0.0` |
| `.claude-plugin/plugin.json` | **`3.9.0`** |
| `.codex-plugin/plugin.json` | **`3.9.0`** |

作者也不一致：`SKILL.md` 写 `Sid Bidasaria`；两个 `plugin.json` 写
`Claude Skills Maintainers` + **占位邮箱 `maintainers@example.com`**；
`README` 写 `Sid Bidasaria (sbidasaria@anthropic.com)`。
⇒ **manifest 是模板批量生成的**（占位邮箱 + 被工具顶到 3.9.0），内容本体是 1.0.0。
⇒ 读数含义：**"3.9.0"不是这份内容的版本，是那个仓库打包器的计数。**
（引用版本号时必须说清是哪一个版本号，否则又是分母不清。）

## 4. 能不能装（**本机是 DSH，不是 Claude Code** —— 这一条必须说准）

| 件 | 本机能不能用 | 依据 |
|---|---|---|
| `skills/feature-dev/SKILL.md` | ✅ **能**，且是 AGENTS.md 指定的落点 | `C:\Users\ADMIN\.openclaw-autoclaw\skills\<名字>\SKILL.md`（实测该目录存在、已有 **176** 条、形状就是 `<名字>/SKILL.md`；`feature-dev` **不撞名**） |
| `commands/feature-dev.md` | ❌ 用不了 | 它是 **Claude Code 的 `/feature-dev` 斜杠命令**；本机没有这套命令运行时 |
| `agents/*.md` | ❌ 用不了 | 依赖 Claude Code 的 Task 子代理 + `model: sonnet` 命名；本机无此运行时 |
| `.claude-plugin/` · `.codex-plugin/` | ❌ 用不了 | 那是 Claude Code / Codex 的插件清单格式；本机 `plugins/` 里装的是 **DSH 宿主插件**（`package.json` + `lib/` + `tools/`，如 `gbt-master`），是**另一套机制** |

⇒ **可以装，但只有 1/8 的件在本机有意义**：`SKILL.md` 作为技能知识件。
`agents/` 与 `commands/` 装过去也**只是躺在盘上的文档**，不会有任何行为。

## 5. 建议（请主人定）

1. **安全性：可装。** 无凭据索取、无破坏性命令、无外泄、无装包、无提示注入、**无自带脚本**。
2. **但它的口径比本仓纪律松**，直接照搬会**降级**我们的规矩：
   - 它的 Phase 5「实现」是**直接改代码**；本仓纪律是「镜像多维度是唯一试验场，生产只收成品」。
   - 它**没有** `run_task` 授权门、没有作用域、没有「AI 永不给自己发授权」。
   - 它**没有**留出集/两模式回归/错报审计这类**自证装置**。
3. **推荐做法（我的判断，供你否决）**：**只把 `SKILL.md` 当方法论吸收**（七阶段里
   「Phase 3 强制先问清、Phase 5 等批准」这两条与我们既有纪律一致，值得固化进 `gbt-*` 规程），
   **不把 `/feature-dev` 当命令装**，也不引它的 agent 定义。
4. 若你要"原样装"，我可以只装 `SKILL.md` 到托管目录 —— **但那属于"采用任何 skill"，
   按 AGENTS.md 我必须先出这份报告并等你点头**。所以我在此**停住，不装**。

## 6. 本轮**未做**（精确到条）

1. **没有安装任何东西**（连 `SKILL.md` 都没落盘到托管目录）—— 等主人确认。
2. `skill_vetting.py` 的**分母缺口没修**：它只扫 `SKILL.md`，
   不扫 `agents/*.md` / `commands/*.md`，且报告里**不写"还有 N 个文件没扫"**。
   （与本会话 `false_report_audit --scope` 那次是**同一个病**，改法也一样：范围上屏 + 覆盖扩展。）
3. 上面 3.1 / 3.2 两条矛盾**只报告、未上报给上游**（按纪律：不外发、不评论上游）。
4. 插件里的 `README.md` 只做了完整通读，**没有**做逐条与 `SKILL.md` 的交叉一致性核对（那是下一步）。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属