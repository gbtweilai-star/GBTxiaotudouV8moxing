# remote_confinement · 触手记忆库

> 本库是触手 `remote_confinement` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
**执行者隔离**（主人 2026-10-09 点破：「沙盒隔离的是被测试的靶标，没隔离执行的人」）：exec 中继若在宿主以主人账号跑，云端敲的命令就跑在真机上。op=assess/verdict 现读执行身份（whoami+是否提权）与三条隔离路（Docker 守护/WSL 发行版/低权账号）**并真验每条能不能跑**；ttl 读看门狗（中继最长 TTL）；grant **只查**主人发的 remote_device 票（AI 不发）；guard 是启中继前的最后一道闸：**未隔离 + 无票 ⇒ 一律拒启**（fail-closed），拒了说清怎么开。本件已焊进 desktop_commander.remote_start。

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'remote_confinement','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
