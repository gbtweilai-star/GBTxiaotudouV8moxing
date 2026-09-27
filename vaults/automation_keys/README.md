# automation_keys · 触手记忆库

> 本库是触手 `automation_keys` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
自动化配置密钥口（APP 设置调它）：六个槽位（codex/claude/deepseek/browser/free_pool/sec_llm）每槽只存**引用**（env:<环境变量名> / vault:<DPAPI profile> / local），**不存值**；输出只有掩码（前 4 字符 + ****）；set/unset 过 filesystem_write 门；test 做只读闭环自检（free_pool 只打本地 /v1，不花积分、不出公网）；where 给设置页看接线契约。真密钥一律走 model_key_pool 的 DPAPI 路径（六条红线在那边）。op=status/set/unset/test/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'automation_keys','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
