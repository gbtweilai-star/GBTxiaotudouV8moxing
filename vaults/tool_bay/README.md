# tool_bay · 触手记忆库

> 本库是触手 `tool_bay` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
装备坞：触手「自配装备」走的那道门。白名单 15 件（本仓自定口径），每件状态靠**现跑探针**得出（没探针的如实报「无探针」，不得报已装）。install 三态：① 已在位（不耗票）② 需授权接上（screen/ui_tree/comfyui，**真过 auth_gate 的 check_and_consume**，没票如实报 needs_grant）③ 第三方件需主人装（**不代下、也不为此耗票**）。每装一次落账 state/tool_bay.jsonl。op=state 读类，install 写类。

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'tool_bay','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
