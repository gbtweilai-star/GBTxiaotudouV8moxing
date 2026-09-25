"""全息面板配色 token（单一真源）。

规则（为什么存在这个文件）：
- 面板原来的 QSS 里散着 60+ 个裸 hex，同一个青色有 #22d3ee/#3ddcff/#4fd8f0/
  #67e8f9/#7fe6ff/#8fe8ff/#9ff0ff 七个近似值混用，改主题必须逐行改 QSS；
- 现在所有 QSS / 文档样式只引用本模块的 token，需要透明度时用
  ``rgba(TOKEN, alpha)``，不再另写一份 rgb 三元组；
- ``config.panel.theme`` 的 bg / border / accent / text 由 :func:`apply_theme`
  真正写进 token，使「改主题只改 config」成立。

消费方请用 ``import ui_theme as T`` 后访问 ``T.ACCENT``，不要 ``from ui_theme
import ACCENT``——后者会把当前值拷贝进模块命名空间，config 主题就覆盖不到了。
"""
from __future__ import annotations

# ---- 主色（青）：全项目唯一 accent，禁止再出现第二个色系 ----
ACCENT = "#22d3ee"           # 主色
ACCENT_BRIGHT = "#67e8f9"    # 主色高亮（hover / 链接）
ACCENT_EDGE = "#3ddcff"      # 主色描边高亮
ACCENT_DEEP = "#0891b2"      # 主色深端（渐变收口）
ACCENT_SOFT = "#7fe6ff"      # 主色前景（图标 / 按钮文字）
ACCENT_TITLE = "#9ff0ff"     # 标题
ACCENT_CODE = "#a5f3fc"      # 代码块文字
ON_ACCENT = "#03212e"        # 主色底上的文字

# ---- 文本层级 ----
TEXT = "#e2e8f0"             # 正文（config.panel.theme.text）
TEXT_DIM = "#a8e8f8"         # 次级正文
TEXT_BRIGHT = "#e6fbff"      # 高亮正文（hover）
TEXT_MUTED = "#5fa8c4"       # 弱化文本（时间戳 / 空态）

# ---- 面板底色（config.panel.theme.bg 落在渐变底端）----
SURFACE_TOP = "rgba(6,20,38,0.94)"
SURFACE = "rgba(4,12,26,0.96)"
CODE_BG = "rgba(15,18,30,0.92)"      # 代码块底

# ---- 警示 / 审批（琥珀，唯一第二个色相，只用于「需要人裁决」）----
WARN = "#fbbf24"
WARN_TITLE = "#fde68a"
WARN_TEXT = "#fef3c7"
WARN_BTN = "#fee8b0"
WARN_BTN_HOVER = "#fff7dd"

# ---- 其它 ----
AFFECTION = "#ff7ab8"        # 好感度（角色语义色，非 UI 主色）
MENU_BG = "#121629"
MENU_BORDER = "#2b3350"


def rgba(color: str, alpha: float) -> str:
    """把 ``#rrggbb`` token 转成 ``rgba(r,g,b,a)``（token 只有一个真源）。"""
    value = str(color).lstrip("#")
    if len(value) != 6:
        return str(color)
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def apply_theme(theme: dict | None) -> None:
    """把 config.panel.theme 写进 token（缺项保留默认值）。"""
    global ACCENT, ACCENT_BRIGHT, ACCENT_EDGE, ACCENT_SOFT, ACCENT_TITLE
    global ACCENT_CODE, ON_ACCENT, TEXT, SURFACE
    theme = theme or {}
    accent = str(theme.get("accent") or "").strip()
    if accent.startswith("#") and len(accent) == 7:
        ACCENT = accent
    border = str(theme.get("border") or "").strip()
    if border.startswith("#") and len(border) == 7:
        ACCENT_EDGE = border
    text = str(theme.get("text") or "").strip()
    if text.startswith("#") and len(text) == 7:
        TEXT = text
    bg = str(theme.get("bg") or "").strip()
    if bg.startswith(("rgba(", "rgb(", "#")):
        SURFACE = bg
