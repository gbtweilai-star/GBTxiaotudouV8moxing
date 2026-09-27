# audio_extract · 触手记忆库

> 本库是触手 `audio_extract` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
从视频里取出声音（本机 ffmpeg，**零出网**）：probe/tracks 读流与音轨（只读）；extract 真出音频件（mp3/aac/m4a/wav/flac/ogg/opus/wma 八种，可切段/调音量/响度归一）。**产出即验证**：落盘后 ffprobe 回读产物，把真读数一并返回。写面自收窄到 projects/·outputs/·.scratch/（policy 无该 kind ⇒ 门内零作用域，故自钉）。格式知识来自 online-audio-converter.com/blog/audio-formats（容器≠编解码器 / 有损与无损两族）。

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'audio_extract','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
