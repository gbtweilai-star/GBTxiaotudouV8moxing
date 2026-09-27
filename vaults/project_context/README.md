# project_context · 触手记忆库

> 本库是触手 `project_context` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
项目上下文：**文档面**（blueprint 蓝图 / brief 简报 / search 只读检索 / status）＋ **代码结构四面**（2026-09-23 接，补上「专业级编程AI」缺的那半身）：`symbols` 符号（顶层 def/class，可按名问「在哪定义」）· `deps` 依赖（内部 import 边 + 外部三方名）· `calls` 调用图（**复用现成 `tools/call_graph.py`**：find/callers/callees/trace/dead_code，4.2s / 351 文件）· `tests` 测试面（模块被哪些测试**提到**过）· `structure` 三面速览（4.4s，**刻意不含调用图**）。全部只读。⚠️ 四处诚实边界随结果一起带出：符号只收**顶层**；依赖只看 **import 语句**；调用图带**未解析率**

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'project_context','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
