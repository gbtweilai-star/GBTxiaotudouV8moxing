---
name: gbt-selfgrowth
description: 自生长知识库 4.0（Codex + Google WikiSkill）蒸馏进本仓：Raw/Trace/Pattern/Skill 四段生命周期 + 三条复利循环 + 四判据 + 适用边界。回答"做事的经验如何不在轨迹里消失"，并与本仓既有的台账/坑册/判据/镜像门控一一对位。
---

# gbt-selfgrowth · 自生长知识库（我们自己的落位）

> **来源与口径（先说清，本仓规矩：凡抓取必写口径）**
> · 来源：主人 2026-09-27 现场拍摄的演示稿 8 张（26–32 页 + 封面），标题
>   「基于 Codex + Google WikiSkill 搭建个人自生长知识库 4.0 · CODEX 管理 · AGENT EXPERIENCE COMPILATION」。
> · 口径：**二手资料（演示稿图片）**，不是一手论文/产品文档。演示稿自己也写了这句：
>   「WikiSkill 架构与论文数据来自本地二手资料整理；**公开发布前，论文细节和产品现状仍应回到一手来源复核**」。
>   ⇒ 本技能**只承接方法论骨架**，不复述具体论文结论、不引用未亲验的数字。
> · 该稿的实验边界也一并承接下来（见 §5）：**它证明"门控能发现退化"，不证明"所有 Skill 都会变好"**。

## 1. 一句话内核

**不是让 Agent 自动记住一切，而是让知识与能力都拥有「来源 · 验证 · 版本 · 回滚」。**

三条复利循环（缺一条就退化成"自动记一堆没出处的东西"）：

| 循环 | 路径 | 复利什么 |
|---|---|---|
| 知识复利 | `Raw → Wiki` | 外部真实来源 → 可链接、可修订、可追溯的概念知识 |
| 能力复利 | `Trace → Pattern → Skill` | 执行迹 → 成功要素/失败模式 → 约束下一次行动的 Skill |
| 可信进化 | `Validate → Accept / Rollback` | 候选能力经**门控**才准入；退化可**回滚** |

一句话记住：**让成功经验可以复用，让失败经验不会白费，也让错误经验没有资格被永久记住。**

## 2. 三个必须分清的边界（这是整套方法的地基）

| 判据 | 含义 | 反例（混淆了就全塌） |
|---|---|---|
| **Raw ≠ Trace** | Raw 是**外部真实来源**（不改写）；Trace 是 **agent 的执行迹** | 把"我做过"当成"世界上是这样" |
| **Wiki ≠ Skill** | Wiki **解释世界**；Skill **约束下一次行动** | 把百科条目当操作手册用 |
| **PURPOSE 必须存在** | 每条 Skill 的说明都要能**密封回它自己的 Pattern** | 没有出处的能力 = 无法验证、无法回滚 |

## 3. 最小可用目录（生命周期先分开，再谈自动化编排）

```
raw/                 # 外部来源，不改写
sources/wiki/        # 概念知识（可链接可修订）+ index.md
trace/logs/          # 完整任务轨迹 + trace.md
patterns/            # success.md（成功要素）· failure.md（失败模式）
skills/              # 候选 Skill：提案 → 门控 → 候选（SKILL.md, skill-1.md…）
knowledge-index/     # index.md（结论都能回到来源）
governance/          # purpose.md + protocol.md（Accept / Reject）
outputs/  runtime/   # 产物 与 运行时
```

> 目的不是好看：**让任何结论都能回到来源，让任何能力变更都能找到提案、分数与回滚记录。**

## 4. 本仓没有的机器吗？没有 —— 一一对位（这是本技能真正的价值）

| 4.0 组件 | 本仓已有的对应物（可直接用，不必新建） |
|---|---|
| `Raw`（外部来源，不改写） | `_upstream/`（第三方参考，永不入史）· 探针工作区 `04-调研/` + 抓取台账（源/时间/口径） |
| `sources/wiki` | `docs/` · `memory/*.md` · `store/devoured/`（知识胶囊）· 大脑 vault |
| `trace`（执行迹） | **`state/*.jsonl` 全是执行迹**：`asset_bindings` · `cross_scan_trace` · `dag_runs` · `fleet` · `work_log` · `store/audit.jsonl` |
| `patterns/success.md` | 判据库（23 条常设判据）· `state/full_scan.json` 的分诊表（哪些类命中是预期的） |
| `patterns/failure.md` | **`store/pit_log.json` 坑册**（root_cause + lesson + 防复发锁）· `memory/2026-09-22-假绿与自伤清单.md` |
| `skills/`（提案→门控→候选） | `skills/gbt-*`（79 个）· **源↔装唯一真相 + 哈希锁**（`tools/skills_sync.py`，覆盖前先备份） |
| `governance/purpose.md` | `AGENTS.md` 红线 · `gbt_allinone/LAYOUT.md` 家规（铁律 1–13） |
| `governance/protocol.md` | 授权门 `run_task` + `security/policy.py` 作用域 · 镜像三区（mirror/gate/production） |
| `知识索引` | `state/skill_atlas.json` + `caps_registry.BENIGN_CAPS`（185 位 × 30 域） |
| **验证门控 Validate** | 三板块总监令 · 交付前主检查清单 · `test_*` 常设判据 · **反向自检**（故意造缺陷看它红不红） |
| **回滚 Rollback** | `.backups/`（skills-hub 覆盖前留档）· `.trash/`（只移不删）· DAG 检查点 · `git worktree reap` |
| **生产/实验隔离** | **镜像多维度是唯一试验场**（生产零修改、一次性晋升）· 舰队 `git worktree` 每根一份隔离工作区 |

**结论**：4.0 的方法论我们**七成已经在跑**，缺的是把它**显式成一条闭环判据**（见 §6 的三步落地）。

## 5. 适用边界（照抄它的诚实，也照抄我们自己的）

**适合先做**：高频重复、**结果可检查**的知识工作；已有可鉴定的基线（baseline）与历史轨迹；
错误成本可由隔离环境承受；能明确划分"训练/测试"。

**不要直接自动化**：样本极小、目标持续变化的任务；评价标准是**价值判断**或需偏好；涉及
**账务 · 资金 · 客户 · 不可逆操作**；**没有沙箱、没有回滚能力**的系统。
（最后两条本仓是硬红线：动生产面要授权、破坏性操作要主人点头。）

**它不能证明什么（原样承接）**：它证明"门控能发现退化"，**不证明**"所有 Skill 都会变好"；
一个模型、两项验证任务、小样本 ⇒ 结论**不许外推**到所有工作流/模型/数据规模。

## 6. 我们怎么落地（三步，每步都有可机检产物）

1. **先立基线**：给要进化的那条线定"做完的样子"+ 评分表（我们的说法：**判据先行**）。
   · 产物：一条常设判据（`gbt_allinone/tests/test_*.py`）——**能红才算数**。
2. **再开轨迹**：让每次执行都往 `state/*.jsonl` 留执行迹（**无痕即未发生**已在跑），
   并把"成功要素/失败模式"提炼进坑册与判据。
3. **后开门控**：候选 Skill 只能走 **提案 → 门控 → 候选 → 人工实施**；
   门控 = 判据全绿 + 反向自检过 + 覆盖矩阵无死角；回滚 = `.backups/` + `git`。
   · 命令：`python tools/skills_sync.py check`（源↔装不许分叉）·
     `python tools/coverage_matrix.py sweep`（无死角）·
     `python tools/selfgrowth.py check <候选技能目录>`（四判据机检，见 §7）。

## 7. 四判据的机检（`tools/selfgrowth.py`）

```
python tools/selfgrowth.py init <目录>          # 建最小可用目录 + 四判据模板（只建不删）
python tools/selfgrowth.py check <候选技能目录>   # 机检：Raw≠Trace · Wiki≠Skill · PURPOSE 在 · 隔离在
python tools/selfgrowth.py promote <候选> <目标>  # 门控通过才准入；准入前**先备份**（=可回滚）
```

**四判据怎么机检（不靠感觉）**：
1. **Raw≠Trace**：`raw/` 里不许出现带执行迹特征的文件（时间戳流水、exit code、"本次"字样）；
   执行迹只许在 `trace/`。
2. **Wiki≠Skill**：`sources/wiki/**` 不许被 `skills/` 直接引用为操作步骤（反向也要查）——
   两类文件的引用关系必须显式（`PURPOSE.md` 里写清"我这套动作来自哪条 Pattern"）。
3. **PURPOSE 密封**：每个候选 `SKILL.md` 必须含 `PURPOSE:` 段，且段内指到 **同名 Pattern 文件**。
4. **隔离**：候选不许直接落在生产目录（`skills/` 真身）；必须从 `skills/_candidates/` 走门控。
