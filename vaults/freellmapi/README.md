# freellmapi · 触手记忆库

> 本库是触手 `freellmapi` 的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据（有的话写 `能力.md`）
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
FreeLLMAPI（本机免费大模型池 127.0.0.1:31415，34 家供应商 / 635 免费端点汇成一个 OpenAI 兼容 /v1）**接入层的**能力位：`status` 总表（探活 + 文档 + 可选供应商读数）· `probe` 探活（`/api/ping`，**明确无鉴权**的口，不拿需要登录的端点探活以免把「没登录」误判成「服务没起」）· `docs` 文档可用性（`/v1/openapi.json`）· `models` 列免费池可用模型（`GET /v1/models`，**只要统一 key、不用登录**）· `framework_env` 算给框架网关用的环境变量（`GBT_LLM_BASE_URL/API_KEY/PROVIDER`，**只算不写盘**）· `where` 给设置页看接线契约；写面：`login`/`providers`/`list_keys

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'freellmapi','text':'…'})`

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
