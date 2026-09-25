# SKILL VETTING REPORT · GBT小土豆V8

═══════════════════════════════════════
报告：GBT小土豆V8 技能安全审查（对照 skill-vetter v1.0.0）
日期：2026-09-25 ｜ 审查者：GBT小土豆V8（AI）· 开发者：自由的风
═══════════════════════════════════════

## 一、主人贴来的那 13 条：**结论是「无法审查」，不是「安全」**

主人令：「全部按 skill-vetter 审一遍，出审查报告。」

`skill-vetter` 的 **Step 2 写着 Code Review (MANDATORY)：通读该技能的全部文件**。
而这 13 条**只有名字与简介，源不在本机任何技能根里**（我查了 7 个根：
`~/.openclaw-autoclaw/skills`、`~/.agents/skills`、`~/.claude/skills`、
`skill-workshop`、`plugin-skills`、仓库 `skills/`、`审美相关skill/skills`）。

⇒ 逐条判为 **⛔ 无法审查（缺源）**。**没有代码就没有 Step 2**，
所以不许写 `✅ SAFE`，也不许拿本地同名/同类件冒充审过 ——
那正是本会话一直在打的那种假账（**没跑成 ≠ 通过**）。

**要把它们审完，我需要其中任意一种「源」**：
  · 商店/仓库的**链接或 slug**（我能拉 SKILL.md 与全部文件）
  · 或**盘上路径**（你把目录放进任一技能根）
  · 或**压缩包/文件清单**
给我源，`python tools/codex-scripts/skill-vet.py --skill-dir <路径>` 一条命令就出报告。

## 二、能审的：本机**同域已有件**（这才是真实读了代码的那批）

同一批主题在本机已有 13 件，**逐件通读全部文件**后：

| 风险 | 件数 | 件 |
|---|---|---|
| 🟢 LOW | 9 | frontend-design · web-design-guidelines · shader-dev · enhance-prompt · swiftui-design · flutter-animating-apps · autoclaw-mcp-tools · code-security-review · pptx-swarm |
| 🟡 MEDIUM（**全部是文档性命中**） | 4 | ui-ux-pro-max · taste-skill · alchemy-mcp · skill-vetter |
| 🔴 HIGH | **0** | — |
| ⛔ 无法审查 | **0** | — |

**"可执行文件里的命中" = 0 处**（13 件全过一遍）。
4 件 MEDIUM 的命中我逐条看过，**全是文档**：
  · `ui-ux-pro-max/references/upstream-*.md` 里的 `sudo apt install` / `npm install`
    —— **上游 README 原文**（vendored 参考件），不是它会去跑的命令；
  · `taste-skill/SKILL.md:1001` 的 `npm install @material/web` —— 安装说明清单；
  · `alchemy-mcp/SKILL.md:204` 的那处是「**Don't** bypass the MCP server with raw curl」
    —— **禁止句**，被我的规则先误读成"外网抓取"，已加否定句识别并排除分级；
  · `skill-vetter/SKILL.md` 本身 —— 它**列举**了全部红旗（curl/~/.ssh/eval/base64…）。

⇒ 按 skill-vetter Step 4 的表，**这 4 件降为「看一眼即可」**，不构成安装障碍。
**但"装包必须先问主人"这条闸照旧**（文档里写着 `npm install` ≠ 我就能跑）。

## 三、🔴 这一轮最该记的：**我的审查器自己撞了四类假阳性**

全部是跑**真数据**才发现的，全都是本仓打了很久的那句「**提到 ≠ 用了**」：

| # | 假阳性 | 根因 | 修法 |
|---|---|---|---|
| ① | `skill-vetter` 被判 🔴 HIGH | 它**列举**红旗（curl/~/.ssh/eval/base64）⇒ 被当成在做 | 风险分级**只采信可执行文件里的命中**；文档命中照列、不抬等级 |
| ② | 6 处「改系统文件」 | 全是 **shebang** `#!/usr/bin/env python3` | 判前剥掉 shebang 行 |
| ③ | `alchemy-mcp` 判「外网抓取」 | 那句是 **Don't** … raw curl（**禁止**） | 匹配点前的否定词 ⇒ 标 `negated`，列出但不参与分级 |
| ④ | `taste-skill` 判「读 ~/.config」 | `postcss.config.js` 里的**子串** | 改成 `[\/]\.config[\/]`（要像一条路径） |

**⇒ 一个模式扫描器在散文上的假阳性是常态；关键是它必须说清"哪些命中能定级"。**
这四条现在都有正/负对照用例钉着（`test_skill_vet.py` 10 条）。

## 四、最要紧的一条口径（写进工具里了）

> **缺源/读不到文件 ⇒ 判「无法审查」，绝不编 `✅ SAFE`。**

因为 `skill-vetter` 的 Step 2 是 MANDATORY —— **没有代码就没有审查**。
把"没跑成"写成"没问题"，是本会话已经打过四次的那类假账。

## 五、逐件明细（工具原始输出）

```
═══ 技能安全审查（对照 skill-vetter v1.0.0）═══
目标 13 个 · 高风险 0 · **无法审查 0**

──────────────────────────────────────────────────────────────────────────────
技能：frontend-design
来源：C:\Users\ADMIN\.openclaw-autoclaw\skills\frontend-design
读过：3 个文件 / 3947 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：ui-ux-pro-max
来源：C:\Users\ADMIN\.openclaw-autoclaw\skills\ui-ux-pro-max
读过：9 个文件 / 94620 字节 ｜ frontmatter: True
风险：🟡 MEDIUM
结论：⚠️ 只见**文档性**命中（多半是在**列举/解释**这些手法）—— 不单独判高风险，但要看一眼是不是在教怎么干
红旗命中 10 处（可执行 0 / 文档 10 / **否定句 0（不参与分级）**）：
   · [装包（未列清）](文档) references\upstream-README.md:261  `npm install `
   · [装包（未列清）](文档) references\upstream-README.md:304  `apt install`
   · [装包（未列清）](文档) references\upstream-README.md:307  `winget install`
   · [装包（未列清）](文档) references\upstream-README.md:439  `npm install `
   · [提权](文档) references\upstream-README.md:304  `sudo `
   · [提权](文档) references\upstream-README.md:304  `sudo `
   · [装包（未列清）](文档) references\upstream-skill-content.md:22  `apt install`
   · [装包（未列清）](文档) references\upstream-skill-content.md:27  `winget install`
   · …（共 10 处，见 --json）
──────────────────────────────────────────────────────────────────────────────
技能：taste-skill
来源：C:\Users\ADMIN\.openclaw-autoclaw\skills\taste-skill
读过：1 个文件 / 87325 字节 ｜ frontmatter: True
风险：🟡 MEDIUM
结论：⚠️ 只见**文档性**命中（多半是在**列举/解释**这些手法）—— 不单独判高风险，但要看一眼是不是在教怎么干
红旗命中 10 处（可执行 0 / 文档 10 / **否定句 0（不参与分级）**）：
   · [装包（未列清）](文档) SKILL.md:1001  `npm install `
   · [装包（未列清）](文档) SKILL.md:1004  `npm install `
   · [装包（未列清）](文档) SKILL.md:1007  `npm install `
   · [装包（未列清）](文档) SKILL.md:1010  `npm install `
   · [装包（未列清）](文档) SKILL.md:1013  `npm install `
   · [装包（未列清）](文档) SKILL.md:1020  `npm install `
   · [装包（未列清）](文档) SKILL.md:1023  `npm install `
   · [装包（未列清）](文档) SKILL.md:1026  `npm install `
   · …（共 10 处，见 --json）
──────────────────────────────────────────────────────────────────────────────
技能：web-design-guidelines
来源：C:\Users\ADMIN\Desktop\GBT小土豆V8\审美相关skill\skills\web-design-guidelines
读过：1 个文件 / 1253 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：shader-dev
来源：C:\Users\ADMIN\Desktop\GBT小土豆V8\审美相关skill\skills\shader-dev
读过：1 个文件 / 1199 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：enhance-prompt
来源：C:\Users\ADMIN\Desktop\GBT小土豆V8\审美相关skill\skills\enhance-prompt
读过：1 个文件 / 1205 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：swiftui-design
来源：C:\Users\ADMIN\Desktop\GBT小土豆V8\审美相关skill\skills\swiftui-design
读过：1 个文件 / 1300 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：flutter-animating-apps
来源：C:\Users\ADMIN\Desktop\GBT小土豆V8\审美相关skill\skills\flutter-animating-apps
读过：1 个文件 / 1169 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：alchemy-mcp
来源：C:\Users\ADMIN\.agents\skills\alchemy-mcp
读过：3 个文件 / 12392 字节 ｜ frontmatter: True
风险：🟡 MEDIUM
结论：⚠️ 只见**文档性**命中（多半是在**列举/解释**这些手法）—— 不单独判高风险，但要看一眼是不是在教怎么干
红旗命中 2 处（可执行 0 / 文档 1 / **否定句 1（不参与分级）**）：
   · [装包（未列清）](文档) SKILL.md:29  `npm i `
   · [外网抓取/下载](否定句) SKILL.md:204  `curl`
──────────────────────────────────────────────────────────────────────────────
技能：autoclaw-mcp-tools
来源：C:\Users\ADMIN\.openclaw-autoclaw\skills\autoclaw-mcp-tools
读过：1 个文件 / 702 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：code-security-review
来源：C:\Users\ADMIN\.openclaw-autoclaw\skills\code-security-review
读过：1 个文件 / 3543 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：pptx-swarm
来源：C:\Users\ADMIN\.openclaw-autoclaw\skills\pptx-swarm
读过：30 个文件 / 259823 字节 ｜ frontmatter: True
风险：🟢 LOW
结论：✅ 可安装（仍建议看一眼命中项）
──────────────────────────────────────────────────────────────────────────────
技能：skill-vetter
来源：C:\Users\ADMIN\.openclaw-autoclaw\skills\skill-vetter
读过：3 个文件 / 4235 字节 ｜ frontmatter: True
风险：🟡 MEDIUM
结论：⚠️ 只见**文档性**命中（多半是在**列举/解释**这些手法）—— 不单独判高风险，但要看一眼是不是在教怎么干
红旗命中 18 处（可执行 0 / 文档 18 / **否定句 0（不参与分级）**）：
   · [外网抓取/下载](文档) SKILL.md:38  `curl`
   · [外网抓取/下载](文档) SKILL.md:38  `wget`
   · [外网抓取/下载](文档) SKILL.md:112  `curl`
   · [外网抓取/下载](文档) SKILL.md:115  `curl`
   · [外网抓取/下载](文档) SKILL.md:118  `curl`
   · [读敏感家目录](文档) SKILL.md:41  `.ssh`
   · [读敏感家目录](文档) SKILL.md:41  `.aws`
   · [碰长期记忆/身份件](文档) SKILL.md:42  `MEMORY.md`
   · …（共 18 处，见 --json）
──────────────────────────────────────────────────────────────────────────────
边界：照 skill-vetter v1.0.0 的 Step1-4 走；**缺源/读不到文件 ⇒ 判『无法审查』，不许编 ✅ SAFE**。命中项是**线索不是结论** —— 最后一步仍是人看。
```
