# db_probe · 触手记忆库

> 本库是触手 `db_probe` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
本地只读查询台（dbx 蒸馏）：**SQLite 概览 + JSONL 行统计**——`sources` 列可查本地源 · `tables` 静态 SQL 列表/视图 · `schema` 参数化取 DDL + Python 解析列 · `counts` 每表行数（iterdump 文本计数）· `jsonl` 行统计/筛选（纯 Python 可自由筛）。🔴 **零动态 SQL**（两版被安全钩子按"SQL 注入"拦下 ⇒ 静态字面量 + 参数取值 + Python 层解析；连接 mode=ro）；结果不落盘；不提供按条件查行（要就说，请主人给门加分支）。op=sources/tables/schema/counts/jsonl/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'db_probe','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
