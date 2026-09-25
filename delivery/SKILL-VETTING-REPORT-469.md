# SKILL VETTING REPORT

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

- 根目录：`C:\Users\ADMIN\.openclaw-autoclaw\skills`
- 扫描时间：2026-09-22T17:23:47
- 规则版本：1.0　基线载入 0 条

## 总账

| 扫了 | 干净 | 有发现 | 发现总数 | 其中 high |
|---|---|---|---|---|
| 469 | 457 | 12 | 14 | 0 |

## 按规则分布

- `GBT-SK-4` × 14

## 样例（前 15 个技能）

### `autoclaw-design-capability/审美相关skill/skills/agent-browser/SKILL.md`　（high 0）
- `GBT-SK-4` L53　修改系统配置或安装软件包
  - 证据：`npm i -g agent-browser`

### `autoclaw-design-capability_noqa/审美相关skill/skills/agent-browser/SKILL.md`　（high 0）
- `GBT-SK-4` L53　修改系统配置或安装软件包
  - 证据：`npm i -g agent-browser`

### `charts/SKILL.md`　（high 0）
- `GBT-SK-4` L342　修改系统配置或安装软件包
  - 证据：`- Use `adjustText` library for automatic label repositioning — **this is the most reliable anti-overlap tool f`

### `cursor-agent/SKILL.md`　（high 0）
- `GBT-SK-4` L187　修改系统配置或安装软件包
  - 证据：`sudo apt install tmux  # Ubuntu/Debian`

### `frontend-slides/SKILL.md`　（high 0）
- `GBT-SK-4` L200　修改系统配置或安装软件包
  - 证据：`1. **Extract content** — Run `python scripts/extract-pptx.py <input.pptx> <output_dir>` (install python-pptx i`

### `glmv-pdf-to-ppt/SKILL.md`　（high 0）
- `GBT-SK-4` L26　修改系统配置或安装软件包
  - 证据：`pip install pymupdf pillow`

### `glmv-pdf-to-web/SKILL.md`　（high 0）
- `GBT-SK-4` L27　修改系统配置或安装软件包
  - 证据：`pip install pymupdf pillow`

### `glmv-prd-to-app/SKILL.md`　（high 0）
- `GBT-SK-4` L380　修改系统配置或安装软件包
  - 证据：`npm install  # or pip install -r requirements.txt`

### `pdf/SKILL.md`　（high 0）
- `GBT-SK-4` L800　修改系统配置或安装软件包
  - 证据：`> **Dependency**: Requires `pymupdf` (`pip install pymupdf`). If not installed, skip automated detection and u`

### `pptx/SKILL.md`　（high 0）
- `GBT-SK-4` L618　修改系统配置或安装软件包
  - 证据：`- **markitdown**: `pip install "markitdown[pptx]"` (text extraction)`
- `GBT-SK-4` L164　修改系统配置或安装软件包
  - 证据：`npm install -g pptxgenjs`
- `GBT-SK-4` L622　修改系统配置或安装软件包
  - 证据：`- **LibreOffice**: `sudo apt-get install libreoffice` (PDF conversion)`

### `skill-vetter/SKILL.md`　（high 0）
- `GBT-SK-4` L49　修改系统配置或安装软件包
  - 证据：`• Requests elevated/sudo permissions`

### `youtube-factory/SKILL.md`　（high 0）
- `GBT-SK-4` L106　修改系统配置或安装软件包
  - 证据：`- Edge TTS (`pip install edge-tts`)`

## 规则表

- `GBT-SK-1`（high）：索要 API key / 凭据 / 密码
- `GBT-SK-2`（high）：破坏性命令
- `GBT-SK-3`（high）：向未知服务器外泄数据
- `GBT-SK-4`（medium）：修改系统配置或安装软件包
- `GBT-SK-5`（high）：伪装成系统指令 / 提示注入

## 诚实边界

1. **静态规则，会有误报** —— 词面命中 ≠ 真恶意。
2. 这是**待人工审的线索**，不是判决；按 `AGENTS.md`，装之前仍须人工过目。
3. 本工具**只读、只报告**，不拒绝、不删除任何 skill。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属