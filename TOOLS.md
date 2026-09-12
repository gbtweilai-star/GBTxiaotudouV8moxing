# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that is unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
Do not store passwords, API keys, tokens, or secrets here in plain text.
For sensitive items, use aliases and safe context only.

### Figma API

- Token: 通过用户授权后的 MCP / 安全配置读取，不在 workspace 文件中保存明文 token。
- 基础调用: `curl -H "X-Figma-Token: <token>" "https://api.figma.com/v1/..."`
- 常用接口:
  - 文件结构: `GET /v1/files/:key?depth=N`
  - 节点详情: `GET /v1/files/:key/nodes?ids=xxx&depth=N`
  - 图片导出: `GET /v1/images/:key?ids=xxx&format=png&scale=2`
  - 用户信息: `GET /v1/me`
- 坑点:
  - 网络偶尔超时，重试即可
  - depth 过大时响应慢，建议分步拉取（先 depth=1 再按需深入）
  - 图片导出 API 容易超时，优先用节点数据 + Python 解析样式

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
