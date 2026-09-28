# freebuff_term · 触手记忆库

> 本库是触手 `freebuff_term` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
freebuff 终端集成（主人令 2026-09-28「把 freebuff 这个终端集成进我们的对话面板，编程就走这个」）：**正常 HOME 下 EPERM 起不来**（只认 $HOME/.config/manicode），隔离 HOME（%LOCALAPPDATA%\gbt-freebuff\home）下装成并验活（0.1.2）。`status` 真身/版本/登录态 · `flags` 现跑 --help（**钉住"TUI-only、无一次性 prompt"**）· `launch` 用隔离 HOME 起真终端（过 process_execute 门）· `login_hint` 给主人登录命令。op=status/flags/launch/login_hint/verify/where

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'freebuff_term','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
