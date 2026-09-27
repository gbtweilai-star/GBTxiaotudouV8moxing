# transformer · 触手记忆库

> 本库是触手 `transformer` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
变压器（**核心已按成熟成品吃透后重做** 2026-09-27）：LLMLingua 的「显式预算 + 段落保护」（`compress=False` 思想 ⇒ **指令/结构段一字不动**，只压参考叙述，支持 rate/target_chars）+ GPTCache 的「近似命中」本地近似（simhash 汉明距离；**假命中禁令**：近似默认只报告不返答案，要答案须 allow_approx）+ autosize（上下文快满自动压 + **原文先落 spill 资料不丢**）；**可旁路 fail-open**（关键信息丢或没省下来 ⇒ 回原样）；**必给前后两个数**并记台账。op=compress/cache_get/cache_put/autosize/stats/selftest

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'transformer','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
