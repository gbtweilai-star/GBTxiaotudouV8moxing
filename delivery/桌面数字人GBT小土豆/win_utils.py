"""Windows window utilities for the desktop pet (topmost / click-through / DWM)."""
from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

logger = logging.getLogger("potato.win_utils")

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

DWMWA_USE_IMMERSIVE_DARK_MODE = 20


def _get_hwnd(widget) -> int:
    """Return the Win32 HWND of a Qt widget (0 if unavailable)."""
    try:
        win_id = int(widget.winId())
        return win_id
    except Exception:  # pragma: no cover - defensive
        logger.exception("winId() failed")
        return 0


def get_window_exstyle(hwnd: int) -> int:
    return user32.GetWindowLongW(hwnd, GWL_EXSTYLE)


def set_window_exstyle(hwnd: int, exstyle: int) -> bool:
    result = user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle)
    if result == 0:
        logger.warning("SetWindowLongW returned 0 (may still be ok)")
    return True


def set_click_through(hwnd: int, enabled: bool) -> bool:
    """Toggle WS_EX_TRANSPARENT so mouse events fall through to the desktop."""
    if not hwnd:
        return False
    style = get_window_exstyle(hwnd)
    if enabled:
        style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
    else:
        style &= ~WS_EX_TRANSPARENT
    ok = set_window_exstyle(hwnd, style)
    logger.info("click_through(%s) -> %s", enabled, ok)
    return ok


def set_topmost(hwnd: int, enabled: bool = True) -> bool:
    """Keep the window above all others (or release it)."""
    insert_after = HWND_TOPMOST if enabled else HWND_NOTOPMOST
    ok = user32.SetWindowPos(hwnd, insert_after, 0, 0, 0, 0,
                             SWP_NOMOVE | SWP_NOSIZE)
    logger.info("topmost(%s) -> %s", enabled, bool(ok))
    return bool(ok)


def set_no_activate(hwnd: int) -> bool:
    """Prevent the pet window from stealing focus when clicked."""
    style = get_window_exstyle(hwnd)
    return set_window_exstyle(hwnd, style | WS_EX_NOACTIVATE)


def enable_dark_mode(hwnd: int, enabled: bool = True) -> None:
    """Best-effort immersive dark mode (Win10 1809+); silently ignore failures."""
    try:
        value = wintypes.BOOL(enabled)
        dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:  # pragma: no cover - cosmetic only
        logger.debug("DwmSetWindowAttribute dark mode not available")


def apply_pet_window_flags(widget, topmost: bool = True,
                           click_through: bool = False) -> None:
    """Convenience: apply the standard pet-window flags to a Qt widget."""
    hwnd = _get_hwnd(widget)
    if not hwnd:
        logger.warning("apply_pet_window_flags: no hwnd yet")
        return
    if topmost:
        set_topmost(hwnd, True)
    set_click_through(hwnd, click_through)
    set_no_activate(hwnd)
    logger.info("pet window flags applied to hwnd=%s", hwnd)
