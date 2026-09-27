# agent_console · 触手记忆库

> 本库是触手 `agent_console` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
代理驾驶舱：**任务监督循环 + 连接请求审批桥**（蒸馏自 GitHub 周榜 #05 paperclip，只取架构）：`add` 登记被监督任务（判活看**读数有没有如期更新**，不是 exit code）· `tick` 定时检查出 ok/stale/failed 并列出该做什么（**不擅自执行**）· `retry`/`wake` 要 process_execute 门 · `request`/`pending`/`approve` 连接请求审批桥：**approve 要求 TTY + 手打 YES ⇒ AI 批不了**。op=add/tick/board/retry/wake/request/pending/approve/verify/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'agent_console','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
