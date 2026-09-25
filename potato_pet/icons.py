"""单色描边图标（monoline SVG）：替代原先把 emoji 当图标/头像的整套做法。

为什么不用 emoji（P0 第 3 条）：emoji 是彩色字形，跨平台字形差异大，
缺字时直接退化成豆腐块（本项目在无 emoji 字体的环境下实测：导航栏 7 个
按钮、功能栏 8 个按钮、头像、徽章全部渲染成方框）。

本模块提供 1.7px 描边、圆头圆角、24×24 viewBox 的单色 SVG 图标，
按需要着色后交给 QIcon / QPixmap。Qt 的 SVG 渲染器不支持 CSS 的
``currentColor``，因此把「currentColor」等价实现为调用方传入的颜色
（QSS 的 ``color`` 不会自动染到 QIcon 上），默认取 ``ui_theme.ACCENT_SOFT``。

用法::

    import icons
    btn.setIcon(icons.icon("voice", T.ACCENT_SOFT, 18))
    btn.setIconSize(QSize(18, 18))
"""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

import ui_theme as T

# 图标几何：全部为 24×24 网格上的单色描边路径
_PATHS: dict[str, str] = {
    # ---- 导航 ----
    "new": '<path d="M12 5v14M5 12h14"/>',
    "history": ('<path d="M20.5 11.5a8.5 8.5 0 0 1-12.4 7.5L3.5 20.5'
                'l1.5-4.4A8.5 8.5 0 1 1 20.5 11.5Z"/>'),
    "social": ('<path d="M12 10.4a1.6 1.6 0 1 0 0 3.2 1.6 1.6 0 0 0 0-3.2Z"/>'
               '<path d="M8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7"/>'
               '<path d="M5.8 5.8a8.8 8.8 0 0 0 0 12.4M18.2 5.8a8.8 8.8 0 0 1 0 12.4"/>'),
    "persona": ('<path d="M12 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/>'
                '<path d="M5.5 20c0-3.3 2.9-5.6 6.5-5.6s6.5 2.3 6.5 5.6"/>'),
    "settings": ('<path d="M4 7h9M17 7h3M4 12h4M12 12h8M4 17h9M17 17h3"/>'
                 '<path d="M15 5.5v3M10 10.5v3M15 15.5v3"/>'),
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "refresh": ('<path d="M20.4 12a8.4 8.4 0 1 1-2.6-6.1"/>'
                '<path d="M18.2 3v3.2h-3.2"/>'),
    # ---- 功能 ----
    "voice": ('<path d="M12 3.5a2.8 2.8 0 0 1 2.8 2.8v4.4a2.8 2.8 0 0 1-5.6 0V6.3'
              'A2.8 2.8 0 0 1 12 3.5Z"/>'
              '<path d="M6.5 11.2a5.5 5.5 0 0 0 11 0M12 16.7V20M9 20h6"/>'),
    "tools": ('<rect x="3.5" y="5" width="17" height="14" rx="2"/>'
              '<path d="M8 10l2.2 2.2L8 14.4M13 14.4h3.2"/>'),
    "browser": ('<path d="M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Z"/>'
                '<path d="M3.5 12h17M12 3.5c2.3 2.4 3.5 5.3 3.5 8.5S14.3 18.1 12 20.5'
                'c-2.3-2.4-3.5-5.3-3.5-8.5S9.7 5.9 12 3.5Z"/>'),
    "plug": ('<path d="M9 3.5v5M15 3.5v5"/>'
             '<path d="M6 8.5h12v2.2a6 6 0 0 1-12 0Z"/><path d="M12 16.7v3.8"/>'),
    "tentacle": ('<path d="M12 8.4a2.4 2.4 0 1 0 0-4.8 2.4 2.4 0 0 0 0 4.8Z"/>'
                 '<path d="M5.6 20.6a2.4 2.4 0 1 0 0-4.8 2.4 2.4 0 0 0 0 4.8Z"/>'
                 '<path d="M18.4 20.6a2.4 2.4 0 1 0 0-4.8 2.4 2.4 0 0 0 0 4.8Z"/>'
                 '<path d="M10.6 8.6 7 15.4M13.4 8.6 17 15.4"/>'),
    "agent": ('<rect x="4.5" y="7.5" width="15" height="11.5" rx="3"/>'
              '<path d="M12 7.5V4.4M9.2 12.4v1.6M14.8 12.4v1.6"/>'),
    "model": ('<path d="M12 3.8 20 8l-8 4.2L4 8Z"/>'
              '<path d="M4 12.2l8 4.2 8-4.2M4 16.2l8 4.2 8-4.2"/>'),
    # ---- 输入区 ----
    "attach": ('<path d="M16.8 7.5 8.9 15.4a2.4 2.4 0 1 0 3.4 3.4l7.6-7.6a4.6 4.6 0 0 0'
               '-6.5-6.5l-7.6 7.6a6.8 6.8 0 0 0 9.6 9.6l5.4-5.4"/>'),
    "stop": '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/>',
    "send": ('<path d="M21 3 3 10.4l7.1 2.5L12.6 20Z"/><path d="M21 3 10.1 12.9"/>'),
    # ---- 头像 / 菜单 ----
    "user": ('<path d="M12 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/>'
             '<path d="M5.5 20c0-3.3 2.9-5.6 6.5-5.6s6.5 2.3 6.5 5.6"/>'),
    "pet": ('<path d="M12 3.8c4.6 0 8.2 3.5 8.2 7.9 0 4.5-3.6 8.5-8.2 8.5'
            's-8.2-4-8.2-8.5c0-4.4 3.6-7.9 8.2-7.9Z"/>'
            '<path d="M9.3 10.4v1.4M14.7 10.4v1.4"/>'
            '<path d="M9.4 14.4a3.2 3.2 0 0 0 5.2 0"/>'),
    "copy": ('<rect x="9" y="8.5" width="10.5" height="12" rx="2"/>'
             '<path d="M15.5 5.5H6.5a2 2 0 0 0-2 2V18"/>'),
    "heart": ('<path d="M12 20.2 4.6 13a4.6 4.6 0 0 1 6.5-6.5l.9.9.9-.9A4.6 4.6 0 0 1 '
              '19.4 13Z"/>'),
}

_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
        "width='{size}' height='{size}' fill='none' stroke='{color}' "
        "stroke-width='{stroke}' stroke-linecap='round' stroke-linejoin='round'>"
        "{body}</svg>")

DEFAULT_STROKE = 1.7


def names() -> list[str]:
    """已注册的图标名（缺图时便于自检）。"""
    return sorted(_PATHS)


@lru_cache(maxsize=256)
def pixmap(name: str, color: str = T.ACCENT_SOFT, size: int = 20,
           stroke: float = DEFAULT_STROKE) -> QPixmap:
    """渲染指定图标为 QPixmap（未知名返回空 QPixmap，绝不抛异常）。"""
    body = _PATHS.get(str(name))
    if body is None:
        return QPixmap()
    svg = _SVG.format(size=int(size), color=str(color),
                      stroke=float(stroke), body=body)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    canvas = QPixmap(int(size), int(size))
    canvas.fill(Qt.transparent)
    if not renderer.isValid():
        return canvas
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return canvas


@lru_cache(maxsize=256)
def icon(name: str, color: str = T.ACCENT_SOFT, size: int = 20,
         stroke: float = DEFAULT_STROKE) -> QIcon:
    """渲染指定图标为 QIcon（未知名返回空 QIcon）。"""
    return QIcon(pixmap(name, color, size, stroke))


def apply(button, name: str, color: str = T.ACCENT_SOFT, size: int = 18,
          stroke: float = DEFAULT_STROKE) -> bool:
    """给按钮装图标（保留按钮已有文字）。返回是否装上了真实图标。"""
    result = pixmap(name, color, size, stroke)
    if result.isNull():
        return False
    button.setIcon(QIcon(result))
    button.setIconSize(QSize(int(size), int(size)))
    return True
