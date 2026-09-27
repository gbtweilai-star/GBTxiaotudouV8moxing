# comfyui · 触手记忆库

> 本库是触手 `comfyui` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
ComfyUI（秋叶整合版）全控（主人令 2026-09-27「这个必须也是一个不漏的双向绑定，才能实现无限制审查生产」）：**966 个节点**（每把一把键）+ 11 个 API 端点 + 14 个启动开关 + 模型清单（checkpoints/loras/controlnet）；**节点消失=断连**（要解释或补）。出网硬钉（SSRF 防线）：只许本机 http + 主机白名单(127.0.0.1/localhost/::1) + 端口 8188 + 路径前缀白名单 + **拒重定向**；读类直连、提交/释放过 filesystem_write 门。op=status/nodes/models/submit/queue/history/free/interrupt/surface/verify

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'comfyui','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
