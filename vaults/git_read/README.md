# git_read · 触手记忆库

> 本库是触手 `git_read` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
**版本库只读面**（2026-09-23 接，补 `code_patch` 的另一半：「改完要能看、要能回滚」）：op=status/diff/log/show/branch_list/stash_list。七道机械闸：**绝不过 shell**（一律 shell=False）· **反选项注入**（rev/path 不许以 `-` 开头）· **路径必须在仓内** · **每条命令带 `--`** · **超时 60s + 输出上限 200KB** · status 只报数量与前 40 条（本仓脏行上万，全量灌回来没意义）· **零作用域**（policy 里不挂任何 scope）。⚠️ 不做 rebase/reset --hard/push —— 那些是「改历史/出网」，要单独设计。type=internal

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'git_read','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
