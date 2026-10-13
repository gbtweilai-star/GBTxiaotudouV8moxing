# energy_scheduler · 触手记忆库

> 本库是触手 `energy_scheduler` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
能源调度面（蒸馏自 2026-09-28 主人给的周榜卡 vllm 92.7k★，只取**调度架构**，不引 CUDA 内核——本机零算力造了也是空壳）：批量 prompt → 多能源分配（**每源并发上限** 按池内 status 档 · **失败冷却** 同源连败 3 次 ⇒ 300s 不再派 · **公平** least-load 优先不饿死单源）。`plan` **纯本地不出网**（可单测可审计）· `run` 每一发都过唯一门 `llm_chat`（external_llm 闸管，没票逐发如实记拒绝）· `status` 计划/源/冷却读数。op=plan/run/status/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'energy_scheduler','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
