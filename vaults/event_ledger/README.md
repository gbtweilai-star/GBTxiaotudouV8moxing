# event_ledger · 触手记忆库

> 本库是触手 `event_ledger` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
签名事件账（蒸馏自 2026-09-28 主人给的周榜卡 buzz block/buzz 34,934★，只取**账本纪律**「每条消息都是签名记录」，不引 Nostr 中继/网络面——出网归门与它自己的闸；人机同室协作已有 collab_gateway）：哈希链 + HMAC 签名，`hash=sha256(prev+规范化body)`、`sig=HMAC(key,hash)` ⇒ **改任意一条，它之后每一条都对不上，定位到第一条被改的**；钥匙随机生成 **DPAPI 落盘无明文**（复用仓内 deepseek_key 帮手），DPAPI 不可用 ⇒ fail-closed；**只增不删**（作废走 append retract）。op=append/verify/tail/status/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'event_ledger','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
