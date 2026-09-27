# genoffice_bridge · 触手记忆库

> 本库是触手 `genoffice_bridge` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
GenOffice AI 线 → 统一密钥网关的**本地 OpenAI 兼容桥**（127.0.0.1:31716）：GenOffice 侧只需握一把 gbtv8- 统一密钥，换道/冷却/禁用/耗尽全由网关机械闸管 ——**不新增 AI 线，只换接头**（保留其 custom provider）。op=status/probe 为**读类直连**（只读接线状态 + 回环 GET /health 探活）；selftest 会铸一把测试钥 + 起临时端口 + 真出网 ⇒ 过门；**serve 不在能力位上**（serve_forever 常驻会挂住调用方 · 纪律第 35 条"穿透传输不阻塞"），走 CLI；作用域声明挂在 cap 边界（security/policy.py::evaluate）

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'genoffice_bridge','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
