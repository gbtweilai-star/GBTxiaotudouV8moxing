# cap_tags · 触手记忆库

> 本库是触手 `cap_tags` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
GBT 技能标签 + 主人调用许可（主人令「将所有的原生能力注册出专属的 GBT 技能标签，只有我允许了才能调用我的能力」）：每个能力位一个稳定标签 `GBT-<域>-<能力位>`，**从注册表现算**；权限类**由框架自己的判据推**（`policy.evaluate` 逐 op 问作用域 + 图鉴 safe/needs_confirmation），**读不出来一律按 owner**（默认严）。`owner` 类=只有主人发许可才能调；许可在 `gbt_allinone/store/owner_permits.jsonl`，**本能力没有任何写它的路径**，终端 `permit` 命令要求 TTY + 手打 YES ⇒ **AI 发不出许可**。op=tags/check/permits/how/audit/verify/where/permit

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'cap_tags','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
