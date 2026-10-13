# case_mine · 触手记忆库

> 本库是触手 `case_mine` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
案例挖掘（starter story 架构蒸馏）：**公开盈利案例 → 结构化案例卡**——`sources` 登记源与抓取口径 · `fetch` **经唯一门**取公开页正文（`run_task('tentacle', web_read)`，本件自己不发 HTTP）· `ingest` 正文→案例卡（营收/起步/工具/渠道，**读不到落「未读到」不编**）· `save` 追加落盘（去重）· `search` 本地语料检索。每条卡必带 `source_url + fetched_at + text_sha256`；只留短引文（≤240 字）**不搬全文**。op=sources/fetch/ingest/save/search/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'case_mine','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
