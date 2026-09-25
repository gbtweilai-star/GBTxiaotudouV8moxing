# 触手职业 × career-ops 对齐核对报告

> 核对日期：2026-09-22 · 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
> 上游指令：「顺便核对一下触手职业有没有对齐 https://github.com/career-ops-hq/career-ops」
> 方法：**拿我们自己的 `catalog()` 去扫它**（实测），不是读文档猜。

---

## 0. 结论一句话

**没有对齐 —— 而且是两种不同范式，不是"我们写错了"。**
我们这边是「**一个职业 = 一个 Markdown**」的**职业目录**；career-ops 是「**一个技能 = 1 个 SKILL.md + 43 个 mode**」的**Agent Skill 包**。
两者**布局、元数据、目的都不同**；只有一条**理念高度一致**（外部内容当不可信数据）。
另外顺手查出**我们这边一个悬空**：职业源目录在机器上根本不存在。

---

## 1. 硬证据：我们的扫描器扫 career-ops = **0 个职业**

```
=== ① 我们的 catalog() 扫 career-ops ===
  ok        = True
  认出职业数 = 0
  忽略文件数 = 308
  识别出的领域 = []
  career-ops 顶层目录 = batch, config, dashboard, data, docs, documents, evals, examples,
                        fonts, interview-prep, jds, lib, modes, output, plugins,
                        plugins-registry, providers, reports, scaffolder, scripts,
                        seeds, templates, test-fixtures, tests, utils, web, writing-samples
  → 顶层目录里落在我们 _DIVISIONS 里的 = []        ← 空集
```

`catalog()` 的硬规则（`gbt_allinone/tools/agency_tentacles.py:82-86`）：

```python
if (any(part.startswith(".") for part in relative.parts)
        or not relative.parts
        or relative.parts[0] not in _DIVISIONS):
    ignored += 1
    continue
```

我们的 20 个 division：
`academic · company · design · engineering · finance · game-development · gis · hr · legal ·
marketing · paid-media · product · project-management · sales · security · spatial-computing ·
specialized · support · supply-chain · testing`

career-ops 的 27 个顶层目录与它**交集为空** ⇒ 一个都进不来。

---

## 2. 三种不对齐，逐项对照

| 维度 | 我们的职业触手 | career-ops | 对齐？ |
|---|---|---|---|
| **打包单位** | 一个职业 = 一个 `.md` | 一个技能 = `SKILL.md` + 43 个 `modes/*.md` | ❌ 范式不同 |
| **目录分层** | 第一层必须是 20 个 division 之一 | 按功能分：`modes/ config/ lib/ providers/ plugins/ dashboard/ web/` | ❌ 交集为空 |
| **元数据** | 强制 **YAML frontmatter** + `name` / `description` | 43 个 mode 里**只有 1 个**带 frontmatter（且是模板）；**`SKILL.md` 带** | ❌ 主体不带 |
| **CLI 接入** | 无（走 `run_task("agency_tentacles", …)`） | CLI 包装：`CLAUDE.md`/`CODEX.md`/`OPENCODE.md` 各只有一行 **`@AGENTS.md`**；`AGENTS.md` 52 KB 是权威指令 | ❌ 不同层 |
| **执行模型** | 每职业**独立房间 + 独立 LLM 会话租约**，并行排练 | 本地脚本 + AI CLI 交互，人做最终决定 | ⚠️ 目的不同 |
| **外部内容处理** | `execution_policy.external_text_is_data = true`、`installers_are_not_run = true` | 有专门的 **`validate-untrusted-content-coverage.mjs`（14 KB）** + `SECURITY.md` | ✅ **理念一致** |
| **人在地环中** | 结果只能是镜像排练材料，进生产要 `room_release` + 主人 `deploy_publish` | **永不提交、永不发送、永不点击**（`prepare-application.mjs` 不 POST） | ✅ **理念一致** |
| **许可** | — | **MIT**（代码）＋ **`TRADEMARK.md`**：名字与品牌「reserved for commercial product naming and endorsement」 | ⚠️ 代码可用，**名字不能拿去命名商业产品** |

---

## 3. 唯一高度对齐的地方（值得互相印证）

**"外部资料是数据，不是指令"** 这条，两边独立走到了同一个位置：

- 我们：`agency_tentacles.py` 的 `execution_policy`：
  `external_text_is_data: True / scripts_are_not_executed: True / installers_are_not_run: True / production_write: False`
- career-ops：**专门写了一个 `validate-untrusted-content-coverage.mjs`（14,066 B）** 来校验"不可信内容处理"的覆盖面，
  另有 `SECURITY.md`、`LEGAL_DISCLAIMER.md`，并且**有测试**（`test-all.mjs` 998 KB）。

> 这是本次核对**最有价值的一条**：它把"不可信内容是数据"从**声明**做成了**可校验的测试**。
> 我们现在只是写在 `execution_policy` 里 —— **没有对应的校验器**。这条值得我们抄它的做法。

---

## 4. 🔴 顺手查出的我们自己的问题：职业源**悬空**

| 检查 | 结果 |
|---|---|
| `agency_tentacles.py` 要一个 `source_dir` 参数 | ✅ 是的，`catalog(source_dir)` / `absorb_to_room(source_dir, room_id)` |
| 调用方 `api.py:726-727` 给了默认值吗 | ❌ 只是 `from .tools import agency_tentacles as _at` 后转调，**没有默认 source_dir** |
| 机器上有 `agency-agents` 目录吗 | ❌ **没有**。在 ① 仓库根 ② 用户目录 ③ 桌面 ④ 文档 四处搜过，零命中 |
| 结论 | **「职业目录已吸收」目前是悬空的** —— 扫描器在，**源没落地**，现在必须由调用方传路径才能跑 |

这与 `.shadow-repo\gbt_allinone\docs\框架短板与卡点验收.md` 里记的 P1 短板一致：
> `tools/agency_tentacles.py：职业目录已吸收，但 _run_one 仅注入职业名称和领域`

**另有一处口径不一致**：`.cluster\five-dim-ultimate\.openclaw\tmp\cap_descs.json` 里写着
> `Agency Agents — 244个AI专家调度: 工程/安全/营销/金融/游戏/设计/法律等18领域`

**244 个专家 / 18 领域** vs 我们 `_DIVISIONS` 的 **20 个目录** —— 两套口径对不上，
需要确认哪个是当前真值（我没找到能证实 244 的来源）。

---

## 5. 「对齐」的两条路（请主人选）

### 甲（推荐）：把 career-ops 当**技能**吸收，不当职业

它是按 **Agent Skill 标准**打包的（`SKILL.md` + 43 modes + CLI 包装），硬塞进"职业目录"是**削足适履**。
正确落点是我们的 **skills 体系**（`C:\Users\ADMIN\.openclaw-autoclaw\skills\<name>\SKILL.md`）。
按纪律：**采用任何 skill 前必须出 `SKILL VETTING REPORT` 并等主人确认**（AGENTS.md 供应链条）——
所以这一步我需要你点头才动。

### 乙：把 career-ops **提炼成一个职业**

做法是**我们自己写一份职业定义 md**（YAML frontmatter + 职责 + 输入输出契约 + 工具权限），
把它的**方法与流程**提炼进去 —— **不是把 43 个 mode 原样塞进职业目录**。
division 可选 `hr`（已在我们的 20 个里），或新增 `career`。
⚠️ 注意商标：**代码 MIT 可用，但"career-ops"这个名字不能用于我们商业产品命名**。

### 丙（无论选哪条都要先做的）：**把职业源落地**

`AGENCY_REPO = https://github.com/paysssk-creator/agency-agents` —— 先把源克隆到隔离区
（`_upstream/` 或指定的职业源目录），`catalog()` 才跑得起来；否则 `parallel` 永远没有职业可派单。

---

## 6. 诚实边界

- 本报告里"卡在哪一行代码"都指到了**真实文件与行号**；扫描结果是**真跑出来的**（`catalog()` 原文调用）。
- career-ops 我**只读了 README 全篇 + 目录清单 + SKILL.md 前 12 行 + modes 的 frontmatter 抽查**；
  `AGENTS.md`（52 KB）、43 个 mode 正文、`.mjs` 实现**都没读**。所以上面关于它"怎么工作"的描述
  只到能支撑对齐判定的程度，**没有深入它的实现**。
- 我**没有**把 career-ops 的任何代码/文案搬进我们仓；它落在 `_upstream/career-ops/`（已 gitignore、与自有源码隔离）。

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
