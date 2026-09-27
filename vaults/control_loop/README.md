# control_loop · 触手记忆库

> 本库是触手 `control_loop` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
快慢双脑控制回路（蒸馏自 Jev/TypeSafe System One + browser-use/jev-ultrafast）：动作是**枚举**（CLICK/TYPE_TEXT/SELECT/SCROLL_*/WAIT/DONE/BLOCKED，枚举外不存在）· 一次观测出「操作+目标」两个头 · 只为 TYPE_TEXT 调生成模型 · **执行前两查（新鲜+遮挡）+ DONE 必须独立验证** · 低置信度才升级慢脑（无慢脑如实 BLOCKED）· 预算闸（单次时延+每分钟次数）· 每次决策写 state/control_loop.jsonl 审计链。**它只决策不动手**：动作仍走 desktop_control 等门。op=decide/observe/act/demo/selftest

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'control_loop','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
