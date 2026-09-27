# audio_mix · 触手记忆库

> 本库是触手 `audio_mix` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
混音与母带（本机 ffmpeg，**零出网**）：`mix` 多轨合成（amix，逐路音量，显式 normalize=0）；`master` 响度归一（**两遍法 loudnorm**：先量后施加，第一遍的四个测量值随结果返回）。响度标准表 streaming -14 / podcast -16 / broadcast -23 / cinema -27 LUFS + 曲风动态预算（**与托管技能 music-production 的 -14 LUFS 口径对齐**，不另立第二套）。填的是 media_flow 的 music/04-mix、music/05-master、film/04-assets 三格。写面自收窄到 projects/·outputs/·.scratch/（policy 无该 kind ⇒ 门内零作用域，故自钉）；复用 audio_extract 的写面守卫与验证器（*

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'audio_mix','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
