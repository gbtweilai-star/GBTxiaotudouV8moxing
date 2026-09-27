# key_gateway · 触手记忆库

> 本库是触手 `key_gateway` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
统一密钥网关：**唯一密钥真源**（链序/冷却/禁用/耗尽/换道）+ 触手统一密钥（`gbtv8-<32hex>`，库内只存 blake2b 摘要）的铸造与校验 —— 也是触手密钥 Y 字端口的取钥处（R-H201：不另开第二条取密钥的路）。op=status/whoami/energy/plan/keys/compat/mask/classify/verify/selftest 为**读类直连**（只读账本与配置，不落盘、不外发、不铸钥）；mint/revoke/note/reset 改**密钥账本与运行态** ⇒ 过 filesystem_write 门；materialize 是**唯一返回明文密钥**的路 ⇒ 按 external_llm 收口；作用域声明挂在 **cap 边界**（security/policy.py::evaluate），与本域同口径

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'key_gateway','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
