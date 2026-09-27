# memory_bank · 触手记忆库

> 本库是触手 `memory_bank` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
记忆银行：**来源追踪 + 别名 + 零停机迁移**（蒸馏自 GitHub 周榜 #01 hindsight，只取架构）：`stamp` 给每条记忆打来源印章（ref/sha256/origin/session/why/evidence）；`trace` 同时报**印章在不在**与**内容有没有被改过**（当前 sha vs 印章 sha）；`alias`/`resolve` 记忆库别名（多级链 + **环检测**）；`migrate`/`migrate_apply` 搬家**先双写→逐文件校 sha→原子切别名→失败回滚**，旧目标只读保留（无删除路径）。op=stamp/trace/alias/resolve/aliases/migrate/migrate_apply/verify/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'memory_bank','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
