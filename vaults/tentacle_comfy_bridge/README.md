# tentacle_comfy_bridge · 触手记忆库

> 本库是触手 `tentacle_comfy_bridge` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
**第 1530 根触手 · ComfyUI 桥**（主人令 2026-10-11「ComfyUI 不是生图工具，是第 1530 根触手的底座」）：把外部 ComfyUI 当**贴图工厂／概念工厂**用，并**双向绑定** —— ① 工作流 = 契约（`state/comfy_workflows/*.json`，ComfyUI 原生节点连线格式）；② 产物**先过闸才允许落盘**（闸口径与 `comfy_native.gate_image` 同源：最短边/格式/非空/可解码）；③ **溯源自证**：workflow_sha256 + seed + ckpt_hash 全部落 `store/tentacle_comfy/ledger.jsonl`（只追加）。出网硬钉照抄 `comfyui_surface`：只许本机 http + 主机白名单 + 端口 8188 + 路径前缀 + 拒重定向。*

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'tentacle_comfy_bridge','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
