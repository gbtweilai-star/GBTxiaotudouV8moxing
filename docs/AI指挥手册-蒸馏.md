# AI 指挥手册 · 蒸馏

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
>
> **口径（主人令 2026-10-08 逐字）**：「我们的框架是以GBT小土豆V8指挥触手干活而设计的，也就是说，GBT小土豆V8的以人类角度来指挥AI干活，所以这些知识蒸馏提炼出契合我们的能力来更好的指挥AI干活」
>
> ⇒ 本文只蒸馏**指挥范式**：怎么派活、怎么交接、怎么验收、怎么升级、怎么停手、怎么复盘、怎么记账。
> **不是工具用法。** 每条指挥知识一律四元组：**指挥谁 · 说什么话 · 拿什么验收 · 失败怎么走**——缺一格不算一条。
>
> 外部来源：`msitarzewski/agency-agents`（现查）＋ `Jakenshchicarol/replica-skill`（核不到）＋ 四本书（本机 0 命中、公开面亦未取到，详见 §7）。
> **凡未读到原文的，一律标"核不到/未读到"；本文不含任何按常理推断补写的条目。**

---

## 0. 核实结论（先核真伪，再谈蒸馏）

### 0.1 `agency-agents`（主人截图里挂的那个）

`gh search repos agency-agents` 与 `gh api repos/msitarzewski/agency-agents` 现查原文：

| 字段 | 现查值 |
|---|---|
| `fullName` | **msitarzewski/agency-agents** |
| `stargazersCount` | **158292**（截图里的 116k 与现查不符 ⇒ **按现查记，不照抄截图**） |
| `forks_count` | 25506 |
| `description` | A complete AI agency at your fingertips - From frontend wizards to Reddit community ninjas, from whimsy injectors to reality checkers. Each agent is a specialized expert with personality, processes, and proven deliverables. |
| `license` | MIT |
| `language` | Shell |
| `created_at` / `pushed_at` | 2025-10-13 / 2026-10-07 |
| `size` | 5213（KB） |
| README.md | 86245 B · 1182 行 |

**我读了哪些文件**（全部只读；`gh api .../contents/<path>` 与 raw 直取，**未 clone**）：

| 文件 | 大小 | 用途 |
|---|---|---|
| `README.md` | 86245 B | 部门名册、设计哲学、Stats、多工具集 |
| `divisions.json` | 2514 B | 部门集（**18 个**） |
| `tools.json` | 8839 B | 工具集（**17 个**，含 `zcode` / `dsh`） |
| `strategy/nexus-strategy.md` | 55289 B · **1110 行** | 指挥主干（7 阶段 + 指挥结构 + 质量闸 + 升级 + 风险/度量） |
| `strategy/coordination/handoff-templates.md` | 10073 B · **357 行** | **7 类交接模板**（本文主料） |
| `strategy/coordination/agent-activation-prompts.md` | 13158 B · 401 行 | 派活话术模板 |
| `strategy/playbooks/phase-0…phase-6` (7 个) | 各 4–14 KB | 阶段作业法（精读 `phase-3-build.md` 286 行） |
| `strategy/runbooks/scenario-*.md` (4 个) | 各 4–6 KB | 场景运行册（精读 `scenario-startup-mvp.md` 154 行） |
| `strategy/QUICKSTART.md` | 8388 B · 194 行 | 三档模式（Full/Sprint/Micro） |
| `strategy/EXECUTIVE-BRIEF.md` | 5754 B · 95 行 | 四条关键发现（含"fantasy approvals"） |
| `examples/workflow-*.md` (含 startup-mvp) | 4594 B 起 | 工作流样例 |

### 0.2 `Jakenshchicarol/replica-skill` —— **核不到**

| 查法 | 原文结果 |
|---|---|
| `gh api repos/Jakenshchicarol/replica-skill` | `{"message":"Not Found", ...}` · `gh: Not Found (HTTP 404)` |
| `gh api users/Jakenshchicarol` | `{"message":"Not Found"}` · 404（**该用户名不存在**） |
| `gh search repos replica-skill` | 命中 **`Jakeschincariol/replica-skill`**（886 星，MIT，描述：Eleven free Claude skills that clone any app: reverse-engineer it, rebuild it, test it for bugs, then fix what its users hate.） |

⇒ **按主人给的拼写，核不到**（仓库 404 + 用户名 404）。
⇒ 存在一个**拼写近似**的仓 `Jakeschincariol/replica-skill`（886 星），**仅供主人辨认截图**；
**不并入本次蒸馏**（不能证明是同一个，本仓纪律：**同名≠同物**，何况此处连名都不同）。

### 0.3 四本书 —— **本机 0 命中，公开面亦未取到**

**本机搜索原文（0 命中）**：在 `C:\Users\ADMIN\Downloads`、`Desktop`、`Documents` 下按书名关键词
（`短剧` `分镜` `即梦` `Seedance` `剪映` `豆包` `自媒体` `新媒体` `全流程创作` `一本学通`）
搜 `.pdf/.epub/.txt/.md/.azw3/.mobi`，**排除本仓目录后命中 0 条**；
电子书扩展名（`.epub/.azw3/.mobi`）单独搜也是 **0 条**。

**合法公开面尝试（按主人 2026-10-08 授权的四条通道）**：

| 通道 | 目标 | 原文结果 |
|---|---|---|
| 出版社官方页 | 清华大学出版社 | `book_10265901.html` 返回 HTML 壳（未定位到书页）；试 `tup.com.cn/booksCenter/book_10000000.html` ⇒ **HTTP 404**「没有找到您要访问的页面」（**无书号，无法定位**） |
| 出版社官方页 | 电子工业出版社 | `phei.com.cn` 检索端点 ⇒ **`fetch failed: unable to verify the first certificate`**（TLS 链验不过，未取到） |
| 正规书商 | 豆瓣读书 | `search.douban.com` 搜索页**只有加载态**（"正在搜索..."），无标题/作者/目录 |
| 正规书商 | 当当 | `search.dangdang.com?key=AI短剧全流程创作` ⇒ **302 跳到 `noresult=1`**（无结果） |
| 公开解读/书评 | DuckDuckGo | **机器人挑战页**（"Select all squares containing a duck"，错误码 c21b） |
| 公开解读/书评 | Bing | 返回**完全无关**结果（印尼语摩托车配件），且自报"第 7 页 / 约 3930 条" |

> 本仓既有台账 `docs/书单六本-分层蒸馏台账.md` §未验账 第 4 条早记过同一实情：「本轮检索通道受限：
> DDG 返回机器人挑战页、Bing 只给泛结果」—— **本轮复现，非新问题。**

⇒ **书的内容：0 条。目录级骨架也拿不到（0 条）。**
⇒ 四本书**只有封面截图**（据主人提供）。**书里的流程一个字都没有臆造。**
⇒ 主人要"正文级蒸馏"的合法路径见 §7。

### 0.4 同名≠同物（本仓最贵的那类教训，此处先钉）

**我们的仓里早就有一个"吸收 Agency Agents"的能力位**，但它写的源是**另一个仓**：

```
文件：gbt_allinone/tools/agency_tentacles.py:16
原文：AGENCY_REPO = "https://github.com/paysssk-creator/agency-agents"
```

| 仓 | 星标（现查） | fork | 创建时间 | 说明 |
|---|---|---|---|---|
| `msitarzewski/agency-agents` | **158292** | 25506 | 2025-10-13 | 主人截图挂的那个；**本文蒸馏来源** |
| `paysssk-creator/agency-agents` | **0** | **0** | 2026-07-04 | **我们能力位接的那个**；描述与前者逐字相同 ⇒ 是**同名副本** |

且 `agency_tentacles.py` 的 `_DIVISIONS`（第 24–27 行）里多出 `company` / `hr` / `legal` / `supply-chain`
四个部门，而 `msitarzewski` 的 `divisions.json` 里**没有**这四个。

⇒ **口径：两个仓分开列、不混引。** 本文第 1 节所有指挥范式，**全部来自 `msitarzewski/agency-agents`**
（即主人截图那个），标到文件与行号。我们接的 `paysssk-creator` 那份**星标 0**，
其部门集与前者的差异**如实并排记，不判二者"就是同一个"**。

---

## 1. 七类指挥动作（四元组 · 主交付）

> 每类一批条目，条条四元组：**指挥谁 · 说什么话 · 拿什么验收 · 失败怎么走**。
> 「拿什么验收」一律只填**非 LLM 可判**的东西；凡只能靠干活的模型自评的，**不算达标**，一律入 §2 反面教材。

### 1.1 切活（怎么把活切成"一个判据能判完"的大小）

**C-01 · 单一真相源**
- **指挥谁**：全体工人（含谋划层）
- **说什么话**：「One canonical spec, one task list, one architecture doc」——规格、任务表、架构各只留一份正本。
- **拿什么验收**：三份正本文件存在且**指纹唯一**（同一时刻不存在第二份"最新版"）；可机检：对正本路径取 sha256，全仓引用该正本的节点指纹一致。
- **失败怎么走**：出现第二份正本 ⇒ **停手**，不合并、不"挑一个信"，交人裁定。
- **出处**：`msitarzewski/agency-agents` · `strategy/nexus-strategy.md:55`（Core Principles 表）。

**C-02 · 一个任务 = 一个交付物 = 一条可勾选判据**
- **指挥谁**：接活的开发者工人
- **说什么话**：派单里 `Acceptance criteria` 必须是**可勾选项列表**（原模板就是 `- [ ] [Criterion — measurable]`），**每项自身可测**。
- **拿什么验收**：勾选项能被**不长嘴的东西**算出来（文件存在/字段齐/阈值达标）。
- **失败怎么走**：判据写不出机检形式 ⇒ **不派活**，退回重切（判据先行，再拆动作）。
- **出处**：`strategy/coordination/handoff-templates.md:35-38`（Standard Handoff Template · Acceptance criteria）；教义面 `strategy/nexus-strategy.md:50`（「No phase advances without passing its quality gate」）。

**C-03 · 切错的样子：任务大到判据兜不住**
- **指挥谁**：派活人自己（自检）
- **说什么话**：任务**跨阶段**、或验收标准要靠**人重新解释** ⇒ 就是切错了。
- **拿什么验收**：该任务的重试次数与失败原因分布——**同因重复**（同一原因连挂）即判"切错了"，不是"手不行"。
- **失败怎么走**：**分解**（Escalation 的 b 选项）而不是"再试一次"。
- **出处**：`strategy/nexus-strategy.md:723-724`（Gate 失败处理）；`strategy/playbooks/phase-3-build.md:211-215`（Escalation 五选项：`a) Reassign b) Decompose c) Revise approach d) Accept with known limitations e) Defer`）。

### 1.2 派活（派单里必须有什么、绝对不能有什么）

**C-04 · 派单六件套（上下文最小充分）**
- **指挥谁**：任一工人（跨部门）
- **说什么话**：派单必带六件——**From/To · Phase 与任务号 · Context（现状 + 相关文件清单，每个文件注明"里面是什么"）· Dependencies · Constraints · Deliverable Request（要什么，可测描述）**。
- **拿什么验收**：接活方能**只凭派单**复述"要什么产物、什么算合格"；机检面：派单必需字段齐（结构校验）。
- **失败怎么走**：字段缺 ⇒ 拒收（**不许接活方自己去猜**）。
- **出处**：`strategy/coordination/handoff-templates.md:11-45`（含 `Relevant Files: - [file/path/1] — [what it contains]`，第 27–29 行）。

**C-05 · 绝不冷启动**
- **指挥谁**：接活方（下游）
- **说什么话**：「Context Continuity — Every handoff carries full context — **no agent starts cold**」。
- **拿什么验收**：下游节点的输入里**不含"待补"占位**；机检：派单字段非空率 100%。
- **失败怎么走**：上游没给全 ⇒ **上游返工**（责任在上游，不在下游"自己想办法"）。
- **出处**：`strategy/nexus-strategy.md:51`（Core Principles）；`handoff-templates.md:3`（「Consistent handoffs prevent context loss — the #1 cause of multi-agent coordination failure」）。

**C-06 · 派单里绝对不写的东西**
- **指挥谁**：派活人自己（禁令）
- **说什么话**：不写"尽量/大约/看着办"；不写复合动作（一个任务塞两件事）；不写"顺便"。
- **拿什么验收**：派单里**没有模糊量词**；判据可机检（阈值是数字）。
- **失败怎么走**：发现模糊词 ⇒ 打回改写，**不许"边干边澄清"**。
- **出处**：本仓家法 `docs/新人类操作系统-控AI干活的四段法与能源账.md` §2.2（「口令写死」与「一个动作一句话」；血账：一次组合命令里的顺带删除差点删掉真身）＋ §2.2「禁语清单：不许说"应该没问题""大概好了""理论上"」。
  **NEXUS 侧的对应**：`strategy/nexus-strategy.md:53`（Evidence Over Claims）——它证的是**验收**面，**未见到它写"禁语清单"这类派活禁令**（此处**不替它补**，标：它无此条，我仓有）。

**C-07 · 并行只给无依赖的活**
- **指挥谁**：多条工人线
- **说什么话**：无依赖 ⇒ 同批并行，各自独立跑自己的"干↔验"环；有依赖 ⇒ **等上游过验**再派，并把上游上下文带进派单。
- **拿什么验收**：依赖拓扑无环；同批任务之间无共享可变状态（否则并行不安全）。
- **失败怎么走**：合并按依赖序；依赖未过验就派下游 ⇒ **判违规**，下游结果不算数。
- **出处**：`strategy/playbooks/phase-3-build.md:219-233`（Parallel Task Management）。

### 1.3 交接（递什么、留什么、谁负责）

**C-08 · 交接用标准件，不用自由文本**
- **指挥谁**：上游 → 下游
- **说什么话**：7 类模板各管一段场景，照表填：**① 标准派单 ② QA 判过 ③ QA 判不过 ④ 升级报告 ⑤ 阶段闸交接 ⑥ 冲刺交接 ⑦ 事故交接**。
- **拿什么验收**：模板**结构齐**（机检字段）；判过/判不过**必须带证据位**（截图路径、测试输出、文件路径）。
- **失败怎么走**：模板不齐 ⇒ 交接无效，退回补齐。
- **出处**：`strategy/coordination/handoff-templates.md:1-357`，用法索引在 `:349-357`（"Which Template for Which Situation"表）。

**C-09 · 交接必须带"下一棒要什么格式"**
- **指挥谁**：上游
- **说什么话**：交接件里必写 `**Handoff to next**: [Who receives the output and what format they need]`。
- **拿什么验收**：下游**真能消费**该格式（不需要转换/再解释）；机检：下游入口对该产物解析成功。
- **失败怎么走**：格式不符 ⇒ 上游改格式（**不是下游写转换器**）。
- **出处**：`strategy/coordination/handoff-templates.md:44`。

**C-10 · 交接要留"改了什么、还剩什么"**
- **指挥谁**：上游（判不过时）
- **说什么话**：QA 判不过时，逐条写 `**Fix instruction**: [Specific, actionable instruction]` ＋ `**File(s) to modify**: [Exact file paths]`；并明写「**Fix ONLY the issues listed above / Do NOT introduce new features**」。
- **拿什么验收**：修复范围**可机检地没扩大**（改动文件集 ⊆ 指定文件集）。
- **失败怎么走**：超范围改动 ⇒ 判违规返工。
- **出处**：`strategy/coordination/handoff-templates.md:118-119`、`:137-141`。

**C-11 · 交接要带"下一阶段的关键约束与风险"**
- **指挥谁**：闸门看门人 → 下一阶段
- **说什么话**：阶段闸交接件必带 `Documents Carried Forward` ＋ `Key Constraints for Next Phase` ＋ `Risks Carried Forward`（风险带 P0–P3 与 owner）。
- **拿什么验收**：每条风险有**责任人与等级**（机检字段）；无主风险 = 不合格。
- **失败怎么走**：无主风险不许过闸。
- **出处**：`strategy/coordination/handoff-templates.md:230-249`（Phase Gate Handoff）。

**C-12 · 交接的记账面（我们的对应）**
- **指挥谁**：框架自身
- **说什么话**：每一次交接落一行审计（谁→谁、产物指纹、判据、结果）。
- **拿什么验收**：台账**只追加、可自链校验**；行数只增不删。
- **失败怎么走**：台账断链 ⇒ 停手查因。
- **出处（我们的实物）**：`gbt_allinone/store/audit.jsonl`（现读 **74461319 B · 487012 行**）＋ `state/logbook.jsonl`（现读 **98836 B · 77 行**，工具 `tools/codex-scripts/logbook.py` 24245 B）。
  **NEXUS 侧的对应**：它有 Sprint Handoff 的质量度量表（`First-pass QA rate` / `Average retries` / `Tasks completed`，`handoff-templates.md:275-280`），**但没有"只追加+自链哈希"的台账形态**——这条是**我们更强**。

### 1.4 验收（判据怎么定、谁判、判不过怎么办）

**C-13 · 判据必须非 LLM 可算**
- **指挥谁**：验收方（与干活方**分离**）
- **说什么话**：验收标准只认**能用不长嘴的东西算出来的**：文件存在/非空/哈希一致/读数一致/谓词返回真。
- **拿什么验收**：**判据自证有牙**——故意造一处缺陷，判据必须报红。
- **失败怎么走**：判据在"老样子"下不报红 ⇒ **判据作废重写**（不算验收）。
- **出处（我们的实物，原文）**：`gbt_allinone/longrun.py:97-98` docstring「**非LLM验收：唯一"完成"判定**」；四种判据 `longrun.py:105-127`：
  `status_ok` · `contains:<kw>` · `file_exists:<path>` · `no_error`，且**未知标准一律判失败**（`else: return False, f"未知验收标准: {c}"` ⇒ **fail-closed**）。
  **NEXUS 侧的对应**：`strategy/nexus-strategy.md:53`（Evidence Over Claims）；`phase-3-build.md:234-244` 闸检查表每项都写 `Evidence Source`——**方向一致，但它的"证据"要人/模型去取，不是判据词表**（它是"要证据"，我们是"判据可执行"）。

**C-14 · 验收默认不通过**
- **指挥谁**：终审方
- **说什么话**：「The Reality Checker **defaults to "NEEDS WORK"** — you must prove production readiness with **overwhelming evidence**」。
- **拿什么验收**：证据不足即判不过（**默认否决**，而非默许）。
- **失败怎么走**：补证据或降级/砍范围，**不许"先上线再说"**。
- **出处**：`strategy/nexus-strategy.md:380`、`:386`；`QUICKSTART.md:149`（「Reality Checker — Final quality authority; defaults to "NEEDS WORK"」）。

**C-15 · 终审权要单独一个人/一个位，且无利益牵连**
- **指挥谁**：终审位
- **说什么话**：「**Gate Keeper: Reality Checker (sole authority)**」——生产闸的终审**只有一个权威**，且它**不是干活的那个**。
- **拿什么验收**：验收结果与干活方**不是同一个执行体**；机检：判过记录里的验收方 ≠ 产出方。
- **失败怎么走**：验收方与产出方相同 ⇒ 该次验收**无效**。
- **出处**：`strategy/nexus-strategy.md:420`、`:713`（`4 → 5 | Production Gate | Reality Checker (sole authority)`）。

**C-16 · 判过要留证据位，判不过要留修复指令**
- **指挥谁**：验收方
- **说什么话**：判过 ⇒ 列证据（截图分档、逐条勾选、品牌/可达性/性能读数）；判不过 ⇒ 逐条**问题 + 期望 + 实际 + 证据 + 修复指令 + 要改哪些文件**。
- **拿什么验收**：判不过条目**可被逐条核销**（每条有独立证据与修法）；机检：条目数与证据数相等。
- **失败怎么走**：无证据的判过 ⇒ 视为未验。
- **出处**：`strategy/coordination/handoff-templates.md:66-88`（QA PASS）与 `:109-144`（QA FAIL）。

**C-17 · 验收点要"能区分这次真做了与上次的还在"**
- **指挥谁**：判据设计者
- **说什么话**：判据必须排除**陈旧产物冒充新产物**。
- **拿什么验收**：判据含**新鲜度**维度（本次时间戳/本次指纹），而非仅"存在且非空"。
- **失败怎么走**：出现假绿 ⇒ 立即停线，判据重写。
- **出处（我们的血账）**：`docs/新人类操作系统-控AI干活的四段法与能源账.md` §2.1 血账——曾用「文件存在且 >1MB」当判据，ffmpeg 失败时把**昨晚的旧片**认证成新片并盖新指纹；原文铁律：「**判据必须能区分"这次真做了"与"上次的还在"**」、**「假绿比错更贵：它把错误变成了"已验收"」**。
  **NEXUS 侧的对应**：`strategy/EXECUTIVE-BRIEF.md:15` Finding 2 独立命名了同一类病：**"fantasy approvals"**（agents rating basic implementations as A+ **without proof**）。两侧**同源**，我方表述更硬（含具体事故）。

### 1.5 升级（失败分类 → 重试/换手/升级给人/停手）

**C-18 · 重试有硬上限：3 次**
- **指挥谁**：编排方
- **说什么话**：「**Maximum 3 retries per task before escalation**」（原则级）；闸面「**Maximum 3 gate re-attempts** before escalation」。
- **拿什么验收**：`attempts` 计数**可机读**，到 3 必停（不许"再试一次看看"）。
- **失败怎么走**：到顶 ⇒ **升级**（不是继续重试）。
- **出处**：`strategy/nexus-strategy.md:54`（Core Principles · Fail Fast, Fix Fast）、`:723`（Gate Failure Handling）；`handoff-templates.md:141`（`This is attempt [N] of 3 maximum`）。

**C-19 · 升级不是"报个错"，是"带一套可选方案 + 要人拍一个"**
- **指挥谁**：升级提交方 → 决策人
- **说什么话**：升级件必带：失败史（逐次：发现什么 / 改了什么 / 为何还挂）· 根因分析 · **五个选项**（换手/分解/改路线/带限制接受/延期）· 影响面 · **决策人与期限**。
- **拿什么验收**：五选项**逐条可勾**；决策人**有名**、期限**有日期**（机检字段）。
- **失败怎么走**：人不拍 ⇒ **停手等**（不许自行"选一个"）。
- **出处**：`strategy/coordination/handoff-templates.md:148-203`（Escalation Report，选项表在 `:188-193`，决策位在 `:200-203`）；`strategy/nexus-strategy.md:723-724`（「Studio Producer decides: **fix, descope, or accept with risk**」）。

**C-20 · 重试要有差异化，不做"同因复读"**
- **指挥谁**：编排方
- **说什么话**：第 1 次给具体反馈、第 2 次**累积反馈并质疑"是不是这个手不对"**、第 3 次升级。
- **拿什么验收**：第 N 次重试的**输入与第 N−1 次不同**（必须多带了信息）；机检：两次派单差异非空。
- **失败怎么走**：连续同因且输入相同 ⇒ **判"假修复"**，直接升级。
- **出处**：`strategy/playbooks/phase-3-build.md:193-217`（attempt 1/2/3 各自动作）；`strategy/nexus-strategy.md:723`。
  **我们侧的反面对照（本仓已自检出的缺陷）**：`docs/架构调研汇总 · GBT小土豆V8 设计稿.md:240` 原文——「**autopilot 的"修复"是空转**：后续轮只把目标文本加一句后缀…**从不把上一轮 selfscan 的 findings 或失败节点名带进下一轮 plan**」；`:289` 的修法「把上轮 selfscan findings 与失败节点名作为**数据**传进下一轮 `_llm_plan`；并按"**同因重复即停**"设终止条件」。⇒ **C-20 在 NEXUS 是既有条，在我们是待补条**（见 §3 表）。

**C-21 · 停滞要单独一态，不许并进"失败"**
- **指挥谁**：长程执行器
- **说什么话**：重试耗尽后分两态：**failed**（判据明确不成立）vs **stalled**（同因空转、无新信息）——停滞走**升级**语义，不混进失败计数。
- **拿什么验收**：两态在台账里**字段可分**；机检：`status` 取值含 `stalled` 且与 `failed` 分开计数。
- **失败怎么走**：停滞 ⇒ 升级给人（不续烧）。
- **出处（我们的实物，原文读数）**：`lr_tick` 本轮实测输出——`{'status': 'failed', 'attempts': 3, 'why': '文件不存在: …'}` **与** `{'status': 'stalled', 'attempts': 3, 'why': '未知验收标准: some_unknown_criterion'}` 两态并出（详见 §6）。
  **NEXUS 侧的对应**：它有 `BLOCKED → Escalate`（`nexus-strategy.md:299-315` 的 Dev↔QA 决策逻辑框），**未见独立的"停滞"计数**（如实标：它无此细分）。

### 1.6 停手（什么情况必须停下来问主人）

**C-22 · 不可逆动作必须过人的门**
- **指挥谁**：任何工人（无一例外）
- **说什么话**：发布/上线这类**不可逆外部动作**，自动化的终点站是**人的门**——本仓口径「`submit` **永远 blocked**」「零出网、不发任何请求、**绝不返回"已发布"**」。
- **拿什么验收**：该动作的返回**不可能是"已完成"**（机检：回归测试断言其恒为 blocked，除非有一次性授权记录）。
- **失败怎么走**：无授权 ⇒ **停**（不降级、不自造授权）。
- **出处（我们的实物）**：`media_publish` 能力位 desc 原文（`py -3.14 -m gbt_allinone list` 输出）：「`submit` **永远 blocked**（发布=不可逆外部动作，需主人 `deploy_publish` 一次性授权；本机零平台凭据）…**零出网、不发任何请求、绝不返回「已发布」**」。
  **NEXUS 侧的对应**：`strategy/nexus-strategy.md:763-765` 的风险响应矩阵有**决策权威分级**（Critical→Studio Producer 立即 / High→4h / Medium→24h / Low→1w）——**它给的是"多久内谁拍"，我们给的是"谁都不可能自己拍"**（不同层，方向一致）。

**C-23 · 要凭据的一律不由机器人代持**
- **指挥谁**：框架
- **说什么话**：密钥只从环境变量/密钥服务读；源码与文档零明文；输出打码前 4 位。
- **拿什么验收**：仓库里**不存在明文凭据**（可机检扫描）；台账里**看不到明文**（只回掩码/指纹）。
- **失败怎么走**：发现明文 ⇒ 停手 + 轮换（交人）。
- **出处（我们的实物）**：`docs/新人类操作系统-控AI干活的四段法与能源账.md` §六 边界（「凭据：只从环境变量/密钥服务读；源码与文档零明文；输出打码前 4 位」）；`key_gateway` / `multimodal_port` 能力位 desc 原文「返回值**永不含明文**（只 key_id/掩码/指纹）」。
  **NEXUS 侧**：`nexus-strategy.md:738-744` 把安全归口给 `Legal Compliance Checker`；**未读到它关于"凭据不代持"的条文**（如实标：核不到）。

**C-24 · 碰生产面必须先镜像**
- **指挥谁**：全体
- **说什么话**：所有假设在镜像里跑；生产零修改、一次性晋升；改动生产要主人点头。
- **拿什么验收**：晋升动作**一次性、可回滚**，且排练全绿才放行（机检：晋升前置指纹绑定）。
- **失败怎么走**：排练不全绿 ⇒ **阻断**（不是"告警后继续"）。
- **出处（我们的实物）**：`mirror_rehearse` / `mirror_ascend` 能力位 desc 原文「排练全绿后一次性全量晋升生产（树/计划指纹绑定，**失败即阻断**）」「交叉验证全绿才放行；一次性全量写入现实+护照+时间线；**现实零修改**」。
  **NEXUS 侧的对应**：它在阶段闸上强行卡（`nexus-strategy.md:723-724`），但**没有"镜像/排练"这层**——它的门是评审门，我们的门是**排练+指纹门**。

**C-25 · 超预算/超时立即停**
- **指挥谁**：无人值守链路
- **说什么话**：硬限时、到点自动停；每个阶段一个原子单元、不跨阶段批量落刀。
- **拿什么验收**：限时器**独立于**被限时的执行体（机检：超时后进程真停）。
- **失败怎么走**：超时 ⇒ 停在检查点（不"再跑一会儿"）。
- **出处**：`docs/架构调研汇总 · GBT小土豆V8 设计稿.md:295`（门槛纪律：「文档已明确 **2 小时默认限时、到点自动停**（协议:253），且"每个阶段一个原子单元、不跨阶段批量落刀"」）。
  **NEXUS 侧**：`nexus-strategy.md:759-765` 风险响应矩阵含时间窗（4h/24h/1w）——**是人的响应窗，不是机器的自停阀**（不同物）。

### 1.7 复盘（把这次指挥经验写回记忆，让下次少指挥一步）

**C-26 · 每次冲刺收工必做复盘（三问）**
- **指挥谁**：编排方/看门人
- **说什么话**：收工必答：**What went well / What to improve / Action items**（具体改动）。
- **拿什么验收**：每一条 `Action items` 有**承接处**（谁的什么改动）；机检：条目→承接处映射非空。
- **失败怎么走**：无承接处的复盘条目 ⇒ 视为没写。
- **出处**：`strategy/coordination/handoff-templates.md:286-289`（Sprint Handoff · Retrospective Insights）。

**C-27 · 度量要落到"下一轮能比"的数**
- **指挥谁**：复盘方
- **说什么话**：必记：**首次判过率** / **平均重试次数** / **完成比** / **阶段闸首过率**。
- **拿什么验收**：数字**来自台账**（不是回忆）；机检：数值可由台账重算出来。
- **失败怎么走**：数不可复算 ⇒ 该度量作废。
- **出处**：`strategy/nexus-strategy.md:786-794`（Pipeline Metrics：`Phase completion rate 95% on first attempt` · `Task first-pass QA rate 70%+` · `Average retries per task < 1.5` · `Quality gate pass rate 80%+ on first attempt`）；`handoff-templates.md:275-280`。

**C-28 · 经验要固化成"下次不用再指挥"**
- **指挥谁**：框架
- **说什么话**：一次经验 ⇒ 固化成一个**技能**或一条**常设判据**（"一坑不踩两次"）。
- **拿什么验收**：该固化件**下次真被复用**（机检：调用/命中计数 > 0）；且新判据**在该坑重演时必须报红**（有牙）。
- **失败怎么走**：复现同一坑 ⇒ 判"固化无效"，重做判据。
- **出处（我们的实物）**：`docs/新人类操作系统-控AI干活的四段法与能源账.md` §四 路径 B 与「每交付一次，把这次的新判据固化…否则下一单又从零开始」；操作清单第 10 条「**固化新判据**：每踩一坑，坑变判据（一坑不踩两次）」。
  **NEXUS 侧的对应**：`README.md:685`（Agent Design Philosophy 第 5 条「**Learning Memory**: Pattern recognition and continuous improvement」）——**它是设计意图陈述，未读到可执行的固化机制**（如实标：意图有、机制核不到）。

**C-29 · 度量口径必须带印章，跨口径不许直接比**
- **指挥谁**：复盘方/审计方
- **说什么话**：读数带**四元组印章**（解释器版本 · store · 身份 · 命令）；口径不同打 `not_comparable`。
- **拿什么验收**：每条读数**印章齐**；机检：印章字段非空。
- **失败怎么走**：跨口径差异**不得直接判"代码坏了"**（换解释器/换 store/换身份都会变红）。
- **出处（我们的实物）**：`docs/新人类操作系统-控AI干活的四段法与能源账.md` §2.4（四元组印章）；本轮演示读数里 `gbt_stamp` 就是该印章的落地形态（见 §6）。
  **NEXUS 侧**：`nexus-strategy.md:786-806` 三张度量表**未读到印章/口径约束**（如实标：核不到）。

---

## 2. 反面教材：凡"让干活的模型自己说干完了"，一律不合格

**这不是新立的规矩，是两侧独立踩过的同一个坑。**

**NEXUS 侧原句**（`strategy/EXECUTIVE-BRIEF.md:15`）：
> **Finding 2**: Quality assessment without evidence requirements leads to **"fantasy approvals"** — agents rating basic implementations as **A+ without proof**.

**我们侧原句**（`docs/新人类操作系统-控AI干活的四段法与能源账.md` §2.1 血账）：
> 曾用「文件存在且 >1MB」当成功判据 ⇒ ffmpeg 失败时，把**昨晚的旧片**认证成新片并盖上新指纹。**假绿比错更贵**：它把错误变成了"已验收"。

**我们侧另一条血账**：23 个僵死测试全绿（报"通过"而实际未验）。

⇒ **派活/交接/验收三处，凡验收方与产出方是同一个执行体，或判据只能由模型自评（"我干完了"/"应该没问题"/"看起来对"），该次验收一律判不合格**，本条**不可豁免**。

**每次定判据前先反问一句**：**这个判据能不能用不长嘴的东西算出来？**
能（文件存在/非空/哈希一致/读数一致/帧差非零/谓词返回真）⇒ 达标；
不能 ⇒ 回炉，别派活。

---

## 3. 对照表：七类指挥动作 × 我们已有的 6 个指挥侧能力位

**我们已有的 6 个指挥侧能力位**（全部现查）：

| # | 能力位 | 域 | 现状证据 |
|---|---|---|---|
| ① | `wf_define` / `wf_run` / `wf_status` / `wf_resume` | `engine` | `caps_registry.py:132` 起；DAG 定义/分层并行执行/查记录/断点续跑 |
| ② | `lr_submit` / `lr_tick` / `lr_status` | `longrun` | `longrun.py:49` 起；**非LLM验收 + 重试 + 停滞升级**，跨进程可续 |
| ③ | `control_loop` | `desktop` | `caps_registry.py:1233`；「**它只决策不动手**：动作仍走 desktop_control 等门」· 每次决策写 `state/control_loop.jsonl` 审计链 |
| ④ | `autopilot` | `llm` | 目标→LLM 拆解→本地校验→执行→自检→修复循环（轮数上限防失控） |
| ⑤ | `gbt_allinone/store/audit.jsonl` | 记账 | 现读 **74461319 B · 487012 行** |
| ⑥ | `state/logbook.jsonl` | 记账 | 现读 **98836 B · 77 行**；工具 `tools/codex-scripts/logbook.py`（24245 B）· 只追加 + 自链哈希 |

**逐格对照**（每格含**验收方式**列：只填 `非LLM判据` 或 `只能模型自评（＝不合格）`）：

| 指挥动作 | ①`wf_*` | ②`lr_*` | ③`control_loop` | ④`autopilot` | ⑤`audit.jsonl` | ⑥`logbook.jsonl` | 验收方式（现状） |
|---|---|---|---|---|---|---|---|
| **C-01 切活·单一真相源** | 部分：`wf_define` 同一 name 覆盖式幂等（`store/workflows.json`） | 部分：任务表 `store/tasks.json` 单一 | 缺 | 缺：目标与验收标准一律调用方传参（`autopilot.py:114-115`） | 部分：审计是"事后账" | 部分：台账是"事后账" | **非LLM判据**（文件指纹） |
| **C-02 切活·一任务一判据** | **已有**：节点 = `{id,kind,params,depends_on}`，一步一产物 | **已有**：`acceptance` 列表即判据 | 缺 | 缺（同上） | 已有（落账） | 已有（落行） | **非LLM判据** |
| **C-03 切活·切错判据** | 部分：`fail_fast` 即停 | **已有**：`attempts` 与 `why` 逐次可读 | 缺 | 部分：轮数上限 | 已有 | 已有 | **非LLM判据**（计数+原因串） |
| **C-04 派活·派单六件套** | **已有**：`params` + 模板注入 | **已有**：`description/kind/params/priority/acceptance` | 缺 | 部分（goal 单参） | 部分 | 部分 | **非LLM判据**（结构校验） |
| **C-05 派活·绝不冷启动** | **已有**：`{{node.field}}` 模板注入 + `{{*}}` 扇入聚合 | 部分：`depends_on` 串依赖 | 缺 | **缺**：`_llm_plan` 签名只有 goal（`autopilot.py:126`） | 部分 | 部分 | **非LLM判据** |
| **C-06 派活·命令写死/禁语** | 已有（参数字典） | 已有（`acceptance` 词表封闭） | 缺 | **缺**：修复靠"加后缀"，未带回 findings（`autopilot.py:126` vs `:62-91`） | 部分 | 部分 | **非LLM判据**（词表封闭性） |
| **C-07 派活·只并行无依赖** | **已有**：分层并行 + 拓扑环检测（`_topo_levels` 有环即抛） | 部分：`depends_on` 有，但**无并行** | 缺 | 缺 | 部分 | 部分 | **非LLM判据**（拓扑） |
| **C-08 交接·标准件** | **已有**：DAG 节点即标准件（结构固定） | **已有**：任务 dict 结构固定 | 缺 | 缺 | 部分 | 部分 | **非LLM判据** |
| **C-09 交接·带下一棒格式** | **已有**：节点返回值即下一棒输入，不需转换 | **已有**：result 原样喂判据 | 缺 | 缺 | 部分 | 部分 | **非LLM判据** |
| **C-10 交接·改了什么/只剩什么** | 部分：`wf_resume` 复用已完成节点 | **已有**：`why` + `attempts` + `fingerprints` | 缺 | **缺**：假修复（见 C-20） | 已有 | 已有 | **非LLM判据** |
| **C-11 交接·带约束与风险** | 缺（无风险带传字段） | 缺（风险无 owner 字段） | 缺 | 缺 | 部分 | 部分 | **只能模型自评（＝不合格）** ⇒ **缺** |
| **C-12 交接·记账** | **已有**（`store/wf_runs/<id>.json` 留全量） | **已有** | **已有**（`state/control_loop.jsonl`） | 已有（audit） | **已有**：只追加（487012 行） | **已有**：只追加 + **自链哈希** | **非LLM判据**（哈希链） |
| **C-13 验收·非LLM可算** | 部分：节点 status/ok | **已有**：四种判据 + **未知判据 fail-closed** | 缺（它只决策） | 缺 | —— | —— | **非LLM判据** |
| **C-14 验收·默认不通过** | 缺（默认 `fail_fast` 但不"默认否决"） | **已有**：`acceptance` 缺省 `["status_ok"]`，未识别判据**直接判失败** | 缺 | 缺 | —— | —— | **非LLM判据** |
| **C-15 验收·终审独立** | 缺（无独立终审位） | **部分**：验收与执行在**同一能力位**内（`lr_tick` 跑完自己判） | 缺 | 缺 | —— | —— | **只能模型自评（＝不合格）** ⇒ **缺** |
| **C-16 验收·证据位/修复指令** | 部分：节点结果如实落盘 | **已有**：判不过给 `why` | 缺 | 缺 | 部分 | 部分 | **非LLM判据** |
| **C-17 验收·排除陈旧产物** | 部分：`cache` 可 ttl | 部分：`fingerprints` 字段存在 | 缺 | 缺 | 部分 | 部分 | **非LLM判据**（指纹） |
| **C-18 升级·重试硬上限3** | 部分：`max_node_retries`（**缺省 0**） | **已有**：`max_attempts` 缺省 **3** | 缺 | 部分：轮数上限 | 已有 | 已有 | **非LLM判据** |
| **C-19 升级·带选项+要人拍** | **缺**：无人可拍，无决策位字段 | **缺**：无"五选项"结构 | 缺 | 缺 | 部分 | 部分 | **只能模型自评（＝不合格）** ⇒ **缺** |
| **C-20 升级·差异化重试** | 缺 | **部分**：重试输入相同（本轮实测：同因两次 why 完全相同） | 缺 | **缺**（假修复已自检在案） | —— | —— | **只能模型自评（＝不合格）** ⇒ **缺** |
| **C-21 升级·停滞单列** | 缺 | **已有**：`stalled` 与 `failed` **分列**（本轮实测两态并出） | 缺 | 缺 | 已有 | 已有 | **非LLM判据** |
| **C-22 停手·不可逆过人门** | 部分：写动作过 `filesystem_write` 门 | 部分：同门 | **已有**：只决策不动手，动作另走门 | 部分 | 已有 | 已有 | **非LLM判据**（门返回 denied） |
| **C-23 停手·凭据不代持** | —— | —— | —— | 部分（走密钥链） | —— | —— | **非LLM判据**（明文扫描） |
| **C-24 停手·碰生产先镜像** | 缺 | 缺 | 缺 | 缺 | 部分 | 部分 | **非LLM判据**（**另有专位** `mirror_*`，见表下注） |
| **C-25 停手·超预算即停** | 部分：节点 `timeout` | 缺（无总预算阀） | 缺 | 部分：轮数上限 | —— | —— | **非LLM判据** |
| **C-26 复盘·三问** | 缺 | 缺 | 缺 | 缺 | 部分 | **部分**：logbook 逐条 | **只能模型自评（＝不合格）** ⇒ **缺** |
| **C-27 复盘·可复算度量** | **已有**：`wf_status` 给 run 记录（耗时/节点状态） | **已有**：`lr_status` 给 `progress`（total/done/failed/stalled/pending） | 缺 | 缺 | 已有 | 已有 | **非LLM判据**（台账可重算） |
| **C-28 复盘·固化成判据** | 部分：工作流可复用（同 name 幂等覆盖） | 部分：任务模板无 | 缺 | 缺 | 部分 | **已有**：append-only 记忆 | **非LLM判据**（复用计数） |
| **C-29 复盘·读数带印章** | **已有**：每次返回带 `gbt_stamp` | **已有**（同上） | 部分 | 已有 | 部分 | 部分 | **非LLM判据** |

**注（表外能力位，不计入这 6 格，但同一指挥面已有）**：
`mirror_rehearse` / `mirror_ascend` / `mirror_release` / `pipeline_submit` / `pipeline_rollback` 构成**镜像-排练-一次性晋升-可回滚**链
（desc 原文：「排练全绿后才放行」「**失败即阻断**」「**现实零修改**」），C-24 的实体在这条链上，**不在上面 6 格里**。

### 3.1 计数结论（两级口径，都可复核）

**A 级 · 条目级**（与 `state/command-playbook.json` 的 32 条**逐条一致**，可直接对账）：

| 判定 | 条数 |
|---|---|
| **已有** | **20** |
| **部分** | **6** |
| **缺** | **5** |
| **潜在（未执行）** | **1**（H-01 宿主入口） |
| 合计 | **32** |

**B 级 · 格级**（本轮对照表实算：**29 个指挥动作 × 6 个能力位 = 174 格**，脚本逐格点数）：

| 判定 | 格数 |
|---|---|
| **已有** | **46** |
| **部分** | **54** |
| **缺** | **59** |
| 不适用（`——`，该位与该项无干系） | **15** |
| 合计 | **174** |

**「缺」逐条（条目级 5 条 · 写清缺什么）**：

1. **C-11 · 交接带"下一阶段关键约束与风险"** —— **全线缺**"风险带**等级 + 责任人**"字段（①②③④都没有）。这是**只能模型自评 ⇒ 不合格**的典型格。
2. **C-15 · 终审权独立** —— **缺独立终审位**：我们现在**没有**一个"验收方 ≠ 产出方"的常设位——`lr_tick` 在**同一能力位内**跑完自己判（`longrun.tick` 内 `run_task` 后直接 `_judge`）。**这是最要紧的一格。**
3. **C-19 · 升级件结构** —— 缺"**五选项 + 决策人 + 期限**"的升级件（现在只会报 `why`：`{task_id,status,attempts,why}`）。
4. **C-20 · 差异化重试** —— 缺**失败数据回流**：本轮实测 T0060/T0061 三次 `why` **逐字相同**；`autopilot.py:126` 的"修复"只给 goal 加后缀（本仓已自检在案，`docs/架构调研汇总 · GBT小土豆V8 设计稿.md:240`）。
5. **C-26 · 冲刺级复盘三问** —— 缺"冲刺收工 → 三问 → Action items → **承接处**"的结构（`logbook.jsonl` 77 行只是**逐条追加**，未读到该结构）。

**「部分」逐条（条目级 6 条 · 缺哪半）**：

1. **C-01 单一真相源**（部分）—— 有"同名幂等覆盖"，缺"**唯一正本 + 唯一性校验**"。
2. **C-03 切错判据**（部分）—— 有"同因可读"（`attempts` + `why`），缺"**同因自动判切错**"。
3. **C-14 验收默认不通过**（部分）—— ②已有（`acceptance` 缺省 `["status_ok"]`，未识别判据直接判失败）；①`wf_run` 无"默认否决"语义。
4. **C-17 排除陈旧产物**（部分）—— 有写后读回逐字节自证（本轮实测 `verify_new_sha=True`），缺**判据层的通用新鲜度维度**。
5. **C-25 超时/超预算即停**（部分）—— 有单节点 `timeout` 与单任务次数上限，缺**总预算/总时限阀**。
6. **C-28 经验固化成判据**（部分）—— 工作流可复用，缺"**新判据必须在该坑重演时报红**"的强校验。

**另注（②里的两小格）**：`lr_submit` 的 `depends_on` 只串依赖、**无并行**；`C-05·②` 与 `C-07·②` 因此计"部分"。

### 3.2 借"宿主入口"一格（单列，主人点名）

`tools.json` 里两条**把我们的宿主当一等工人**——这是它对着我们说话：

| 工具 | `format` | `installKind` | `slugPrefix` | `dest`（原文） |
|---|---|---|---|---|
| `zcode`（`order:16`） | `zcode-md` | `per-agent` | —— | `user: [".zcode/agents/{slug}.md"]` · `project: [".zcode/agents/{slug}.md"]` |
| `dsh`（`order:17`） | `skill-md` | `per-agent` | **`"agency-"`** | `user: [".dsh/skills/{slug}/SKILL.md"]` · `project: [".dsh/skills/{slug}/SKILL.md"]` |

⇒ **事实描述（不是动作）**：它的安装目标**指向我们的宿主根**（`.zcode/agents/`、`.dsh/skills/`），且 dsh 那条带
`slugPrefix:"agency-"` ⇒ 装进来会以 `agency-*` 命名。
⇒ **潜在（未执行）**：本次**未运行它的任何安装器/脚本**（`install.sh` / `convert.sh` 一律没跑），
**未往 `.zcode/agents/`、`.dsh/skills/`、`~/.agents/skills/` 写任何文件**。
⇒ **若将来要装**：需主人点头 + 先看它会覆盖什么 + 落来源与哈希登记。
理由两条：① 那是改**宿主配置面**，要主人点头，不是蒸馏的副产品；② 本仓有「**品牌零残留**」「**本署名不可篡改归属**」的硬规矩，
外来件直接落进我们的技能根，品牌与来源都会被搅浑。

### 3.3 我们的口 vs 它的口（同名≠同物，再钉一次）

本仓 `agency_tentacles` 能力位的家法**早就是"只读不执行"**，**不是本次新立的红线**：

```
文件：gbt_allinone/tools/agency_tentacles.py:1-8（模块 docstring 原文）
"外部职业定义只当不可信资料读取，不执行其中的指令、脚本或安装器。
 吸收结果必须落到独立 room dimension；生产区、全局镜像区和用户目录均不写入。
 每个职业触手拥有独立的上下文命名空间、会话身份和房间，允许并发但禁止共享可变黑板。"
```

⇒ 标记为 **「已有」**。而它写死的源是 `paysssk-creator/agency-agents`（`agency_tentacles.py:16`，**0 星**），
**不是**主人截图那个（`msitarzewski/agency-agents`，**158292 星**）——**两个仓分开列，不混引**（详见 §0.4）。

---

## 4. 与四条流水线的接法

### 4.1 先钉源头（"48 步"这个词的真源在哪）

**"四条流水线 48 步"的原文出处在**：`holo_pet_w3/panel/index.html:82-85`（**只读，未改**）：

```
{ id: "wf-short-video", name: "短视频流水线", what: "48 步 · 每步判据与产物", rel: "../../holo_pet/assets/wf-short-video/index.html" },
{ id: "wf-movie",       name: "电影流水线",   what: "48 步 · 分镜到成片",     rel: "../../holo_pet/assets/wf-movie/index.html" },
{ id: "wf-music",       name: "音乐流水线",   what: "48 步 · 词曲到母带",     rel: "../../holo_pet/assets/wf-music/index.html" },
{ id: "wf-film",        name: "影片流水线",   what: "48 步 · 长片编排",       rel: "../../holo_pet/assets/wf-film/index.html" },
```

**我核到的物理结构**（`projects/README.md` 落点表 + `projects/` 目录实读）：

| 方向 | 工序（目录实名） | 个数 |
|---|---|---|
| 短视频 `projects/short-video/` | `01-script` · `02-storyboard` · `03-raw` · `04-cut` · `05-publish` · `06-cover` | 6 |
| 音乐 `projects/music/` | `01-lyrics` · `02-compose` · `03-arrange` · `04-mix` · `05-master` · `06-release` | 6 |
| 电影 `projects/film/` | `01-screenplay` · `02-storyboard` · `03-shoot` · `04-assets` · `05-edit` · `06-final` | 6 |
| 电影（成片线）`projects/movie/` | `产线/` `审计标准/` `成片/` `生成/` `编剧室/` `音乐线/` | 6 |

且 `projects/README.md` 明写：「**「彩排」不占第 19 个工序位** … 所以上面 **18 格**不变」。
`projects/movie` 侧的页面自述：「阶段（按真实目录**现读** · 数字是该阶段真文件数）… 来自 `projects/movie` 子目录现读」。

⇒ **如实标**：**"四线各 48 步"这个数字我核到了它的出处（panel 页面四个字符串），但没核到"48 行步骤逐条表"**——
仓里能核到的物理结构是**每线 6 工序**（3 方向 18 格 + movie 成片线另 6 格）。
**我不替它把 6 工序展开成 48 步**（那是编）。**待主人确认**：48 步是"工序×子步"的另一种记法，还是另一份未入库的表。

### 4.2 每条流水线里：哪一步 V8 指挥 / 哪一步交给触手 / 验收点在哪

按**三方向 18 格**的物理结构逐段接（**每格四元组：指挥谁 / 说什么话 / 拿什么验收 / 失败怎么走**）：

| 工序 | 指挥者（V8 侧） | 交给触手/AI 的活 | 验收点（非 LLM 判据） | 失败怎么走 |
|---|---|---|---|---|
| `01-script` 选题/口播稿 | V8：**定判据**（字数/钩子位/标题数） | 触手：拟稿 | `file_exists:<稿>` + 字数在阈值内 + 标题数 == N | 判不过 ⇒ 重试（≤3）⇒ 换手 ⇒ 升级 |
| `02-storyboard` 分镜表 | V8：定**字段齐全度**（景别·运镜·时长·情绪） | 触手：`drama` 能力位（剧本→镜头表） | 字段齐全度逐条 == 100% + 时长和一致 | 同上 |
| `03-raw/03-shoot` 原始素材 | V8：定**数量/规格/许可** | 触手：生成/拍摄 | 件数 == N + 每件 sha256 已登记（`media_license register`） | 缺件 ⇒ 重试；**无许可 ⇒ 停手**（家规第 2 条） |
| `04-cut/05-edit` 剪辑 | V8：**不给自由**，只给参数（`edit_pipeline` 时间线语义） | 触手：渲染 | **回读磁盘**：`verify_new_sha == True`（写后逐字节自证） + 交付三必查（`level`/关键帧间隔按秒/音轨 codec） | 回读不符 ⇒ 判不过，重渲 |
| `05-publish` 发布版 | **V8 只做"备发布包"，终点是主人的门** | —— | `media_publish.submit` **恒 blocked**（零出网、绝不返回"已发布"） | 无授权 ⇒ **停手**（不降级、不自造授权） |
| `06-final/06-cover` 终版/封面 | V8：终审判据（SSIM 阶梯定档） | 触手：出图/出片 | SSIM 落到档位区间 + 体积在阶梯内 | 落档外 ⇒ 重渲或降档 |
| 音乐线 `02-compose`→`05-master` | V8：定**整数采样对齐 + 拍内位置直方图**判据 | 触手：合成 | onset 直方图落拍内 + `−1.5 dBFS` 读数 | 同 01 |
| 电影线（长片） | V8：**能量驱动密度**（段落 0–1 能量同时驱动配器与剪辑密度） | 触手：逐拍渲染 | 逐拍视觉验证帧存在 + QC 三项过 | 缺帧 ⇒ 重试；同因重复 ⇒ **判切错了**，分解 |

**交接面的实物接线**（我们已有，直接用）：
- 上一工序的产物路径作为下一工序派单的 `params`，经 `{{node.field}}` 注入 ⇒ **不冷启动**（C-05）；
- 同一工序的多件并行（无依赖）⇒ `wf_run` 分层并行（C-07）；
- 产物在 ⇒ `wf_resume` 复用已完成节点（C-12 记账面 + 幂等）；
- 每次判过/判不过落 `lr_tick` 的 `why` 与 `attempts`（C-16）。

---

## 5. 我们不采用的部分与理由

| 它那套里的东西 | 出处 | 不采用的理由 |
|---|---|---|
| **它的安装器与多工具装配链**（`scripts/convert.sh` → `install.sh`，把 agent 装进 17 种工具的宿主目录） | `README.md:32-119`、`tools.json` | **一次都不跑**。① 安装目标指向我们的宿主根（`.zcode/agents/`、`.dsh/skills/`）⇒ 改宿主配置面要主人点头；② 与「品牌零残留」「本署名不可篡改归属」冲突（`slugPrefix:"agency-"` 会落 `agency-*`）。**只抄文件里的结构知识，不搬它的脚本。** |
| **`integrations/` 那层生成产物** | `divisions.json` 注释（`NON_DIVISION_DIRS`） | 那是它 `convert.sh` 的输出物、**不是源**；对我们零信息量。 |
| **人的排期/预算/业务度量**（`Budget Overrun`、`LTV:CAC`、`NPS > 50`、`Portfolio ROI > 25%`、`User acquisition MoM 20%+`） | `nexus-strategy.md:735-750`、`:812-820` | 那是**一家公司**的运营指标，不是"指挥 AI 干活"的判据；且**这些数我们无从核**（无数据源）。**不引入**（引进来只会变成"看着专业"的空格子）。 |
| **"用 LLM 当验收方"的隐含前提**（把评分交给人/模型去取证据） | `nexus-strategy.md:53`、`phase-3-build.md:234-244` | 与本仓红线冲突：**非 LLM 验收**是硬口径。它的"要证据"我们升级成"**判据本身就是可执行词表**"。 |
| **`zcode` / `dsh` 的安装目标** | `tools.json` | **潜在（未执行）**；若将来要装，见 §3.2 的三道前置（主人点头 + 先看覆盖什么 + 落来源与哈希登记）。 |
| **它作为"托管服务/需凭据"的任何部分** | —— | **核不到它需要凭据**（它全套是本地 md/sh，MIT）。⇒ **不写"它依赖托管服务"这种没核到的话**（如实标：此项**未核到**，故不构成不采用理由）。 |
| **四本书的任何流程条文** | —— | **书的内容 0 条**（本机 0 命中 + 公开面 6 条通道全失败，§0.3）⇒ **一个字都不敢引入**。这不是"不采用"，是**没有可采用的**。 |

---

## 6. 最小可跑演示（原文读数 · 硬证据）

**口径**：只用**我们自己的**能力位，不用它的任何脚本。**只读不装**。

### 6.1 派活口：`wf_define` + `wf_run`

**写根**：`outputs/agency-demo/`（本仓既有产出区）。**文件名带 run-id** 防重复跑互覆。

**DAG 定义**（落 `state/wf-cmd-demo.json`，`wf_define` 只许读仓内 `state/` 下的相对路径）：

```json
{"name": "cmd-demo-dispatch-accept",
 "nodes": [
   {"id": "deliver", "kind": "create",
    "params": {"op": "write", "path": "agency-demo/deliver-20261008-094654.txt",
               "content": "GBT小土豆V8 指挥演示 · 派活产物 · run=20261008-094654"}},
   {"id": "readback", "kind": "create", "depends_on": ["deliver"],
    "params": {"op": "write", "path": "agency-demo/deliver-20261008-094654.txt",
               "content": "GBT小土豆V8 指挥演示 · 派活产物 · run=20261008-094654"}}
 ]}
```

**`wf_define` 原文读数**：

```
{'ok': True, 'name': 'cmd-demo-dispatch-accept', 'nodes': 2, '_source_file': 'state/wf-cmd-demo.json'}
```

**`wf_run` 原文读数（节录关键字段）**：

```
run_id: cmd-demo-dispatch-accept-1791427634706 · status: ok · elapsed_s: 0.404
nodes: {'deliver': 'ok', 'readback': 'ok'}
deliver  → {'action':'write', 'path':'agency-demo/deliver-20261008-094654.txt',
            'bytes':66, 'sha256':'e7d790bf9f083f7f4ed63b28f6a26fd1b093501b0fd567e8eb5ccbf0920be1fc',
            'wrote':True, 'idempotent':False, 'verify_new_sha':True, 'verify_backup_sha':True,
            'auth_consumed':'grant-1791425395752'}
readback → {'wrote':False, 'idempotent':True, 'verify_new_sha':True,
            'sha256':'e7d790bf9f083f7f4ed63b28f6a26fd1b093501b0fd567e8eb5ccbf0920be1fc'}
```

**这两行本身就是非 LLM 判据**：
- `deliver.verify_new_sha == True` = **写后从磁盘读回、逐字节比对**（`file_operation.py:515-525`），不是自称；
- `readback.idempotent == True` = **再读一次盘、字节完全相同**（`file_operation.py:481-488`）⇒ **"这次真做了"被机械证明**（正是 C-17 要的那种判据）。

**独立第二路交叉验证**（不看它的自报，我自己直读盘）：

```
exists: True · bytes: 66
sha256: e7d790bf9f083f7f4ed63b28f6a26fd1b093501b0fd567e8eb5ccbf0920be1fc
content: GBT小土豆V8 指挥演示 · 派活产物 · run=20261008-094654
MATCH_ENGINE_REPORT: True
```

⇒ **派活口：已跑通**。且**刹车层是活的**：写盘消耗了真实授权
（`auth status` 原文：`filesystem_write` `grants_available: 1` · `used_total: 4`），**不是绕门硬写**。

### 6.2 验收口：`lr_submit` 的 `acceptance` + `lr_tick`

**判据词表就用 `longrun.py:_judge` 那四种**（`status_ok` / `contains:<kw>` / `file_exists:<path>` / `no_error`）。

**三个任务原文读数**：

```
正例    T0059  acceptance=["status_ok","file_exists:<真路径>","contains:python"]
负对照1 T0060  acceptance=["status_ok","file_exists:<故意不存在的文件>"]
负对照2 T0061  acceptance=["status_ok","some_unknown_criterion"]
```

**`lr_tick` 原文读数**：

```
{'task_id': 'T0059', 'status': 'done',   'attempts': 1, 'why': '全部验收标准满足'}
{'task_id': 'T0060', 'status': 'pending','attempts': 1, 'why': '文件不存在: C:/.../NO-SUCH-FILE.txt'}
{'task_id': 'T0060', 'status': 'pending','attempts': 2, 'why': '文件不存在: C:/.../NO-SUCH-FILE.txt'}
{'task_id': 'T0060', 'status': 'failed', 'attempts': 3, 'why': '文件不存在: C:/.../NO-SUCH-FILE.txt'}
{'task_id': 'T0061', 'status': 'pending','attempts': 1, 'why': '未知验收标准: some_unknown_criterion'}
{'task_id': 'T0061', 'status': 'pending','attempts': 2, 'why': '未知验收标准: some_unknown_criterion'}
{'task_id': 'T0061', 'status': 'stalled','attempts': 3, 'why': '未知验收标准: some_unknown_criterion'}
progress: {'total': 61, 'done': 34, 'failed': 26, 'stalled': 1, 'pending': 0}
```

**这一组同时证明了四件事**：
1. **判据真判**：正例 `attempts: 1` 即 `done`，`why: 全部验收标准满足`；
2. **判不过会重试**：`file_exists` 指不存在 ⇒ 连挂 3 次（`attempts` 1→2→3）后 `failed`；
3. **fail-closed**：未知判据 `some_unknown_criterion` **没有"放行"**，而是**逐字报** `未知验收标准: some_unknown_criterion`，三次后进 **`stalled`**；
4. **停滞单列**：`stalled` 与 `failed` **在同一份 progress 里分开计数**（C-21 达标）——且注意 `failed: 26` 里**绝大多数是历史遗留**（`store/tasks.json` 里 2026-09-13 起的测试任务），**不是本次三条**。

### 6.3 演示的口径（哪半跑了、哪半没跑）

> **派活口 `wf_*`：已跑通**（`wf_define` + `wf_run`，2 节点，0.404s，磁盘直读 sha256 逐字节相符）。
> **验收口 `lr_submit` / `lr_tick`：正例已跑通**（T0059 `done`）；**负对照两条已跑通**（T0060 `failed`、T0061 `stalled`）。
> **三条全部拿到原文读数，无一条是"被票挡"**。

**诚实附注（哪些不是本次演示的结果）**：
- `failed: 26` / `done: 34` 是 `store/tasks.json` 的**累计历史**，本次只新增 T0059/T0060/T0061 三条；
- 本次**没有**测"升级给人"的第五选项结构（C-19）——**该格在 §3 表里是"缺"**，不拿演示替它背书；
- 本次**没有**测独立终审位（C-15）——**该格也是"缺"**，同此。

---

## 7. 边界（书的部分 + 主人要"正文级蒸馏"的合法路径）

### 7.1 本次**不做**的（写清、不含糊）

- **不下载、不引用盗版电子书/扫描件**。理由与「不绕反机器人」同类：**能做，但不该做**——那是侵权。
  （本轮公开面尝试里，DuckDuckGo 返回的就是**机器人挑战页**；**未绕过**，就此收手。）
- **不假装读过正文**：本文每条书的说法都**没有**——因为**书的内容 0 条**。
- **凡是只有封面的部分，明写"仅封面可见"**：四本书**全部**处于这个状态。

### 7.2 来源等级（本轮如实标注）

| 书 | 本机搜索 | 出版社官方页 | 书商详情页 | 公开解读 | 结论 |
|---|---|---|---|---|---|
| 《AI短剧 全流程创作：从分镜脚本到特效成片》（清华大学出版社 · 楚晓辉/郭笑莹） | **0 命中** | 清华社页面未定位到书页（试书号 ⇒ 404） | 豆瓣**加载态**；当当 **noresult=1** | DDG **机器人挑战**；Bing **无关** | **仅封面可见 · 目录核不到** |
| 《豆包 × 剪映 × 即梦 Seedance 一本学通 AI 绘画》 | **0 命中** | —— | 同上 | 同上 | **仅封面可见 · 目录核不到** |
| 《AI + 新媒体 全流程操作指南》 | **0 命中** | —— | 同上 | 同上 | **仅封面可见 · 目录核不到** |
| 《Codex AI 自媒体实战（零基础·案例版）》（电子工业出版社 · 黄益贺） | **0 命中** | 电子工业出版社检索端点 **TLS 验签失败**，未取到 | 同上 | 同上 | **仅封面可见 · 目录核不到** |

**拿到几条就写几条：0 条。**

### 7.3 主人要"正文级蒸馏"的两条合法路径（供主人选）

1. **主人手上有电子版/纸书** ⇒ 把文件给我、或指定章节 ⇒ 我**按章蒸馏**（每条标章节页码）。
2. **主人授权某个他本人已购买/已订阅的正规平台作为来源** ⇒ 那涉及**他的账号凭据**：
   **由他决定，我不代持、不代登**（与本仓凭据红线一致，见 C-23）。

---

## 8. 一句话总结

**我们的框架已经有一条完整的"指挥"骨架**：`wf_*` 是**派活口**（DAG + 上下文注入 + 并行 + 断点续跑），
`lr_*` 是**验收口**（非 LLM 判据 + 重试 + 停滞升级，且 fail-closed），
`control_loop` 是**只决策不动手**的手刹，`autopilot` 是拆解环，两条台账是记账面。
**从 NEXUS 蒸馏出来的、我们最该补的三格**：
**① 独立终审位（C-15）** —— 现在验收方与产出方在同一个位里；
**② 升级件的结构（C-19）** —— 现在只会报 `why`，没有"五选项 + 决策人 + 期限"；
**③ 失败数据回流下一轮（C-20 / C-05·④）** —— 现在重试是同因复读，不是差异化重试。

**判据所在，即领土所在。** 这三格补上，才算真把"指挥"从"能跑"抬到"能交给人拍板"。

---

## 9. 附带交付：`skills/gbt-command/SKILL.md`（**要生效还得装，那是另一步**）

本轮已写 `skills/gbt-command/SKILL.md`（仓内 `skills/` 下，格式与既有技能一致：YAML frontmatter + `triggers`）。
它把本文的七类动作压成**可执行**形态：七条真口命令（`wf_define`/`wf_run`/`wf_status`/`wf_resume`/`lr_submit`/`lr_tick`/`lr_status`）、
判据词表、节点级武器表、`status` 四态读法、停手四条、以及本轮实测跑通的派活 DAG 样例。

**必须说清（不许含糊）**：
- **它现在只是仓里一个文件，不会自动生效。** 要让本机 agent 真能用它，还得**装到本机 agent 技能根**
  （把 `skills/gbt-command/` 落到宿主技能目录）——**那是另一步，需主人点头**。
- **本轮没有装、也没有往任何宿主技能根写文件**（`.zcode/agents/`、`.dsh/skills/`、`~/.agents/skills/` 一律未动）。
  理由同 §3.2：宿主配置面要主人点头，且本仓有「品牌零残留」「本署名不可篡改归属」的硬规矩。
- 仓内 `skills/` 现状（只读一数）：**88 项**，命名风格为自有品牌 `gbt-*` / `remotion-*` 等。

---

> 开发者：自由的风 · 守护者：公主土豆 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
