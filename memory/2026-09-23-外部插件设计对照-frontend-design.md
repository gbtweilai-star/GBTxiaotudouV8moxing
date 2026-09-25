# 外部插件设计对照 · `secondsky/claude-skills` 的 `frontend-design`（2026-09-23）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
>
> Owner 指令：「https://github.com/secondsky/claude-skills/tree/main/plugins/frontend-design 来看清楚别人是怎么设计的」
> 本件是**读完之后的对照与采纳**，不是转述。来源全部是 2026-09-23 现读（GitHub API 全树 + raw 原文）。

---

## 0. 它的真身（现读，不是我印象里的）

```
plugins/frontend-design/
├── .claude-plugin/plugin.json          594 B    ← 宿主清单一（最小）
├── .codex-plugin/plugin.json         1,364 B    ← 宿主清单二（带 interface 块，是清单一的 2.3 倍）
├── README.md                         6,582 B    ← **发现层**（人看）
└── skills/frontend-design/SKILL.md   9,050 B    ← **执行层**（模型读）
```

零脚本、零依赖（它自己写明 "pure guidance skill with no external dependencies"）。

---

## 1. 它的八条设计（逐条）

| # | 设计 | 具体长什么样 |
|---|---|---|
| 1 | **一个源，多宿主清单** | 正文只在 `SKILL.md` 一份；宿主差异**只落在各自的 `plugin.json`**。codex 那份多一个 `interface` 块：`displayName / shortDescription / longDescription / developerName / category / capabilities:["Read","Write"] / defaultPrompt:[三句]` |
| 2 | **两层文档分工** | `README.md` = 发现层（触发词分组 · 能力清单 · 哲学 · 什么时候用/**什么时候别用** · 用法示例+**预期结果** · 相关技能 · 文件结构）；`SKILL.md` = 执行层（设计思考 → 准则 → 常见问题 → **验收清单** → 测试方法） |
| 3 | **触发词分五组，含 Anti-Pattern** | Primary / Secondary / Design-Approach / Technical / **Anti-Pattern**（`avoid generic design` · `avoid AI aesthetics` —— **要避免的东西也做触发词**） |
| 4 | **"❌ Don't Use When" 是一等公民** | 四条，与 "✅ Use When" 并列，各占一节 |
| 5 | **常见问题写成 Issue/Solution 成对** | "**Issue**: Generic font choices / **Solution**: Use distinctive pairings…"，不是散落的提醒 |
| 6 | **验收清单是可勾选的** | 五组：视觉质量 / 响应式 / 无障碍 / 性能 / 代码质量 / 浏览器兼容，共 30+ 个 `- [ ]` |
| 7 | **测试给具体命令与阈值** | 断点 320/768/1024/1440/1920 · WCAG AA 4.5:1 · 只动 `transform/opacity` · `font-display: swap` · 尊重 `prefers-reduced-motion` |
| 8 | **成熟度与时标头** | `**Status**: Production Ready ✅` · `**Last Updated**: 2025-11-12` |

---

## 2. 对照我这边的**现状**（诚实，不美化）

### ✅ 我比它强的三处（要保住，别在学它的时候丢掉）

| 我这边 | 它那边 |
|---|---|
| **验收是"可跑的门"**：`quick_scan` / `cap_probe_all` / `desktop-shell-guard` / `accept-all-angles`，退出码即结论 | 它的验收是**人拿眼睛勾清单**（`- [ ]`），机器不判 |
| **有授权门与残骸纪律**：`policy` 作用域门 · 唯一门 `run_task` · 回收站纪律 | 它没有权限模型（纯 guidance，无副作用，也不需要） |
| **多根一致性可机检**：同一技能在 4 个根逐文件哈希一致 | 它是单仓单根，无此问题 |

### ❌ 我缺的四条（它就是在这四条上比我清楚）

| # | 我缺什么 | 现读证据 |
|---|---|---|
| a | **没有"发现层 README"** —— 我只有 `SKILL.md`；触发词塞在 frontmatter 里，**没有"什么时候别用"、"预期结果"、"相关技能导航"** | `skills/gbt-omni/` 只有 `SKILL.md`（18 KB），无 README |
| b | **"什么时候别用"普遍缺失** —— 我最近才在 `unimplemented_scan` / `code_structure` 里开始写 boundary，技能层几乎没有 | 只有少数件有「诚实边界」节 |
| c | **Anti-Pattern 不做触发词** —— 我的反模式在 `memory/2026-09-22-假绿与自伤清单.md` 里，**没进任何技能的触发表** | 用户说"别给我假绿"时，**打不中**任何规程 |
| d | **没有成熟度/时标头** —— 有 `version`，但没写"能不能用/最后更新" | 各 `gbt-*` SKILL.md 头部无 Status/Last Updated |

---

## 3. 采纳（三条，按价值排序）

1. **补发现层 README**：含「自动触发词分组（**含反模式**）· 什么时候用/什么时候别用 · 用法示例与**预期结果** · 相关技能 · 文件结构」。
2. **反模式进触发表**：把「假绿 / 假故障 / 报得出名字点下去没反应 / 只读半身 / 门说拒了报表说未知」这类**症状词**做成触发词 —— 让人说"**别给我假绿**"时能命中纪律件。
3. **验收清单成形成人可勾的样子**，与我的可跑工具**并列**：机器判（退出码）+ 人勾（清单）。**两者都要，不互相替代。**

**不采纳**：把验收降级成人勾（我这边有可跑的就不要退回去）；`interface.defaultPrompt` 那三句套话（本仓的 `ask` 路由已经能出真候选，不需要预设问句）。

## 4. 机械化（**记在文档里没人守 = 没做**）

采纳必须落成**可跑的检查**，否则就是"我记住了"。
⇒ `tools/codex-scripts/skill-discovery-lint.py`：逐个 `gbt-*` 技能检查发现层要件
（README 在不在 · 有没有「什么时候别用」· 触发表里有没有反模式词 · 有没有相关技能导航 · SKILL.md 有没有成熟度/时标头），
**带负对照**（喂一个只有 SKILL.md 的假技能，必须红）。

现读读数见该工具输出（**本文不抄数字，避免又一处会过期的手抄**）。
