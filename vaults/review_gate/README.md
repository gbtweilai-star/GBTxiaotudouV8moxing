# review_gate · 触手记忆库

> 本库是触手 `review_gate` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
独立终审位（C-15「验收方 ≠ 产出方」的最小实现 · 2026-10-08 在册）：接线件 `tools/codex-scripts/terminal-review.py`。`review` **只读盘**现算 sha256/字节/空否/BOM/关键词，判据只用非 LLM 四族（file_exists:/contains:/no_error/status_ok，与 longrun._judge 同口径），可选 producer_run 取产出方**自报**与盘上真值逐项对账（背离逐条列；自报一概不采信）；`escalate` 从任务真读数出「五选项 + 决策人 + 期限」；`retro` 冲刺三问；`reflow` 差异化重试（失败数据回流 _prev_error/_prev_attempts/_prev_fingerprints）。**默认零写盘**（只打印读数与判决）；写面一律走*

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'review_gate','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
