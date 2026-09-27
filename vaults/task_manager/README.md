# task_manager · 触手记忆库

> 本库是触手 `task_manager` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
任务管理器（主人令 2026-09-27）：一屏看全「任务 / 归属 / 内存占用 / CPU / 端口 / 进程ID」；psutil 读**真进程**（CPU 需两次采样：process_iter 的 info 是首次缓存，第二遍必须直接再调）；归属按**进程名优先**认（血账：只看命令行会把 chrome 误认成框架服务）；**网络列是"占着的端口"不是流量**（本机取不到 per-process 流量，不编）；stop 过 process_execute 门；page 生成我们视觉语言的静态页（SVG 图标·无 emoji·深色+青橙）。op=list/stop/page

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'task_manager','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
