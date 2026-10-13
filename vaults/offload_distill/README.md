# offload_distill · 触手记忆库

> 本库是触手 `offload_distill` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
**内存墙蒸馏件**（Edge0 思路 → 我们的运行纪律 + **触手映射**）。上游 `Edge0-AI/Edge0`（**Apache-2.0** · ★4612 · arXiv 2609.18063）做到「35B 只吃 ~2.5 GB 内存」。四条机制：**权重离芯**（SSD 流式 + mmap 懒读）· **槽位+LRU+双缓冲**（每步零主机同步）· **prerouter 提前一步预判**（IO 与前向重叠 · 吞吐最高 +59%）· **Recover-LoRA**（int4 底座 + 蒸馏小适配器补质量 · **适配器不合并**）。常用说法：内存压缩 / 省内存 / 流式加载 / 权重放盘 / 预取 / 量化 / LoRA / 内存墙 / 跑大模型。op=status/where/mechanism/map/probe：`mechanism` 逐条给「**上游原文** 

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'offload_distill','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
