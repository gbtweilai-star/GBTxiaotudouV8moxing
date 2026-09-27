# agent_rig · 触手记忆库

> 本库是触手 `agent_rig` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
编码智能体编队：**把本机已装的 CLI agent 编成并行流水线**（蒸馏自 GitHub 周榜 #02 orca，只取架构）：`agents` 只读盘点可编排的 agent（fail-closed）· `plan` 把一批任务分成 N 份（每份 worktree + 端口段 + 隔离 HOME + 独立日志，口径抄 tentacle_fleet）**只出计划** · `dispatch` 要 process_execute 门、任务只进文件不进命令行 · `collect` 从各份 worktree 收改动。op=agents/plan/dispatch/status/collect/verify/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'agent_rig','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
