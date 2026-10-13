# flow_canvas · 触手记忆库

> 本库是触手 `flow_canvas` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
工作流画布（蒸馏自 2026-09-28 主人给的周榜卡 Langflow 155.3k★，只取**可视化架构**，不引拖拽编辑器）：工作流定义 → 图（nodes/edges，数据只走引擎正规出口 `engine.list_workflows()`，R-H99b，不偷读 store/workflows.json）+ dag 运行账 → 运行图（带 done/failed 读数）→ **自包含 SVG 画布页**（零外链零脚本，离线可开可审计）落 outputs/flow-canvas/。**只画不跑**：执行仍走 wf_run/dagrun 的门，产物不掺页面登记面。op=from_wf/from_dag/render/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'flow_canvas','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
