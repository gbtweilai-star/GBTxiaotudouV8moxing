# gbt-capability: subprocess, dynamic-import, ctypes
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/omni_tentacle.py — 万能触手 · 无护栏 · 直连硬件
======================================================
触手插入显示屏 → 实时画面回传
触手带动鼠标 → 点击任何东西
触手读取一切 → 不受任何限制

零 brain 依赖。纯 pyautogui + win32。直接干。
"""
import sys, json, time, base64, io
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent


# ═══════════════════════════════════════════
#  硬件直连 — 屏幕/鼠标/键盘
# ═══════════════════════════════════════════

_MSS_SCT = None  # 复用mss实例 (新建95ms → 复用30ms)
_DXCAM = None  # DXGI Desktop Duplication (硬件级采集, 1.6-9.9ms)
_DXCAM_FAIL_TS = 0.0  # ⛔ 2026-08-08: 创建失败冷却(60s后重试, 不永久缓存False)
_DXCAM_BASE = None  # 增量基准帧 (numpy)
_DXCAM_BASE_TIME = 0
_NV_LITE = None      # ⛔ 2026-08-09: native_vision轻量眼缓存 (画布/游戏/自绘UI原生视觉定位兜底)
_NV_LITE_TS = 0.0    # 加载失败重试节流(30s)


def _get_sct():
    """获取复用的 mss 采集实例"""
    global _MSS_SCT
    if _MSS_SCT is None:
        try:
            import warnings as _w
            with _w.catch_warnings():
                _w.simplefilter("ignore", DeprecationWarning)
                import mss
                _MSS_SCT = mss.mss()
        except Exception:
            _MSS_SCT = False
    return _MSS_SCT if _MSS_SCT else None


def _get_dxcam():
    """获取 DXGI Desktop Duplication 采集器 (硬件级: 直读显卡帧缓冲)"""
    global _DXCAM, _DXCAM_FAIL_TS
    if _DXCAM is None:
        if time.time() - _DXCAM_FAIL_TS < 60.0:
            return None  # ⛔ 冷却期内不重试(防循环创建)
        try:
            import warnings as _w
            # 防御: 清理 sys.path 中的 cv2 目录条目 (cv2 目录身在 path 会导致 dxcam 内部 import cv2 递归爆炸)
            import sys as _sys_cv
            _clean_cv = [p for p in _sys_cv.path if p.lower().replace(chr(92), "/").rstrip("/").endswith("/cv2")]
            if _clean_cv:
                for _p_cv in _clean_cv:
                    try:
                        _sys_cv.path.remove(_p_cv)
                    except ValueError:
                        pass
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                import dxcam
            _DXCAM = dxcam.create(output_idx=0, output_color='RGB')
            _DXCAM.start(target_fps=144)
        except Exception:
            _DXCAM_FAIL_TS = time.time()  # ⛔ 失败记时间, 60s后自动重试自愈
    return _DXCAM if _DXCAM else None


def _dxcam_frame():
    """DXGI 采集最新帧 (numpy RGB, 1.6-9.9ms)"""
    cam = _get_dxcam()
    if not cam:
        return None
    try:
        return cam.get_latest_frame()
    except Exception:
        return None


def _native_lite_eye():
    """⛔ 2026-08-09 原生视觉眼 — importlib加载native_vision的LiteEyes (零brain依赖, 复用定位缓存)
    画布/游戏/自绘UI UIA读不到的, 视觉模型看图定位; 加载失败缓存False, 30s后重试"""
    global _NV_LITE, _NV_LITE_TS
    if _NV_LITE is False and time.time() - _NV_LITE_TS < 30:
        return None
    try:
        if _NV_LITE is None or _NV_LITE is False:
            import importlib.util as _iu_nv
            _spec_nv = _iu_nv.spec_from_file_location("_nv_eye", str(ROOT / "caps" / "native_vision" / "run.py"))
            _nv_mod = _iu_nv.module_from_spec(_spec_nv)
            _spec_nv.loader.exec_module(_nv_mod)
            _NV_LITE = _nv_mod.LiteEyes()
    except Exception:
        _NV_LITE = False
        _NV_LITE_TS = time.time()
    return _NV_LITE if _NV_LITE else None


def _screen_capture(region: dict = None, fmt: str = "jpeg", quality: int = 80, incremental: bool = True):
    """屏幕采集 — 秒级传输优化 v2
    基线(PNG): 234ms / 1622KB b64
    优化(mss+JPEG): 79ms / 389KB b64  (3x提速, 4x减负)
    fmt: jpeg(默认,快) | png(兼容,慢)
    """
    import io as _io, base64 as _b64
    import numpy as _np
    from PIL import Image as _PILImage
    img = None
    captured_ms = 0.0
    delta = False
    t_start = __import__("time").time()

    # 方案1: DXGI 硬件级采集 (1.6-9.9ms, 直读显卡帧缓冲)
    frame = _dxcam_frame()
    if frame is not None:
        captured_ms = (__import__("time").time() - t_start) * 1000
        # 增量模式: 与基准帧对比, 只编码变化区域
        global _DXCAM_BASE, _DXCAM_BASE_TIME
        if incremental and _DXCAM_BASE is not None and (__import__("time").time() - _DXCAM_BASE_TIME) < 5:
            try:
                # 快速差异检测: 步长采样4x4 (面积1/16), uint8对比免int16
                step = 4
                base_s = _DXCAM_BASE[::step, ::step]
                frame_s = frame[::step, ::step]
                diff_s = _np.abs(base_s.astype(_np.int16) - frame_s.astype(_np.int16)).sum(axis=2)
                changed_s = diff_s > 40
                ratio = float(changed_s.mean())
                if ratio < 0.15:  # 变化<15% → 增量
                    ys_s, xs_s = _np.where(changed_s)
                    if len(xs_s):
                        # 采样坐标 → 原图坐标 (外扩1步长防边缘)
                        y0 = max(0, int(ys_s.min()) * step - 4)
                        y1 = min(frame.shape[0], (int(ys_s.max()) + 1) * step + 4)
                        x0 = max(0, int(xs_s.min()) * step - 4)
                        x1 = min(frame.shape[1], (int(xs_s.max()) + 1) * step + 4)
                        if (y1 - y0) * (x1 - x0) < frame.shape[0] * frame.shape[1] * 0.4 \
                                and (y1 - y0) >= 64 and (x1 - x0) >= 64:
                            img = _PILImage.fromarray(frame[y0:y1, x0:x1])
                            delta = True
                            region_out = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
            except Exception as _e:
                print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
        if img is None:
            img = _PILImage.fromarray(frame)
        _DXCAM_BASE = frame
        _DXCAM_BASE_TIME = __import__("time").time()

    # 方案2: mss 兜底 (BitBlt)
    if img is None:
        try:
            sct = _get_sct()
            if sct is not None:
                mon = sct.monitors[1]
                if region:
                    shot = sct.grab({"left": mon["left"] + region["x"], "top": mon["top"] + region["y"],
                                     "width": region["w"], "height": region["h"]})
                else:
                    shot = sct.grab(mon)
                img = _PILImage.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                captured_ms = (__import__("time").time() - t_start) * 1000
        except Exception as _e:
            print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
    # 方案3: pyautogui 终极兜底
    if img is None:
        import pyautogui
        if region:
            img = pyautogui.screenshot(region=(region["x"], region["y"], region["w"], region["h"]))
        else:
            img = pyautogui.screenshot()
        captured_ms = (__import__("time").time() - t_start) * 1000

    buf = _io.BytesIO()
    if fmt == "jpeg":
        img.save(buf, "JPEG", quality=quality)
        fmt_out = "jpeg"
    else:
        img.save(buf, "PNG")
        fmt_out = "png"
    data = buf.getvalue()
    result = {"ok": True, "size": list(img.size), "fmt": fmt_out,
              "image_base64": _b64.b64encode(data).decode(),
              "image_kb": len(data) // 1024,
              "capture_ms": round(captured_ms, 1),
              "engine": "dxcam" if _DXCAM is not None else ("mss" if _MSS_SCT is not None else "pyautogui"),
              "delta": delta}
    if delta:
        result["delta_region"] = region_out
    return result

def _mouse_move(x, y):
    import pyautogui; pyautogui.moveTo(x, y)

def _mouse_click(x=None, y=None, button="left"):
    import pyautogui
    if x is not None: pyautogui.click(x, y, button=button)
    else: pyautogui.click(button=button)

def _mouse_double_click(x=None, y=None):
    import pyautogui
    if x is not None: pyautogui.doubleClick(x, y)
    else: pyautogui.doubleClick()

def _mouse_scroll(amount=-3):
    import pyautogui; pyautogui.scroll(amount)

def _keyboard_type(text):
    import pyautogui; pyautogui.write(text, interval=0.03)

def _keyboard_press(key):
    import pyautogui; pyautogui.press(key)

def _keyboard_hotkey(*keys):
    import pyautogui; pyautogui.hotkey(*keys)

def _mouse_position():
    import pyautogui; pos = pyautogui.position(); return {"x": pos.x, "y": pos.y}

def _screen_size():
    import pyautogui; size = pyautogui.size(); return {"width": size.width, "height": size.height}

def _enum_windows(max_count=50):
    try:
        import win32gui, win32process
    except ImportError:
        return []
    windows = []
    def _cb(hwnd, _):
        if len(windows) >= max_count: return
        if not win32gui.IsWindowVisible(hwnd): return
        title = win32gui.GetWindowText(hwnd)
        if not title or len(title.strip()) < 1: return
        rect = win32gui.GetWindowRect(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        windows.append({"title": title[:100], "pid": pid, "hwnd": hwnd, "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]}, "size": f"{rect[2]-rect[0]}x{rect[3]-rect[1]}", "pos": f"({rect[0]},{rect[1]})"})
    win32gui.EnumWindows(_cb, None)
    return windows

# 中文应用名 → 窗口标题关键词映射 (中文匹配不到时用英文)
_WINDOW_TITLE_MAP = {
    "记事本": "notepad",
    "浏览器": "chrome",
    "资源管理器": "explorer",
    "文件管理器": "explorer",
    "计算器": "calculator",
    "画图": "mspaint",
    "终端": "terminal",
    "命令提示符": "cmd",
    "控制台": "console",
}


def window_title_matches(target, title):
    """窗口标题模糊匹配 — 双向子串 OR token级AND
    例: target="Chrome - doubao.com" 匹配真实Chrome标题 "豆包 - doubao.com - Google Chrome"
    (模型常按"浏览器 - 域名"旧格式猜测窗口名, 实际标题为"页面名 - 域名 - 浏览器名")
    """
    t = str(target or "").lower().strip()
    n = str(title or "").lower().strip()
    if not t or not n:
        return False
    if t in n or n in t:
        return True
    try:
        import re as _wm_re
    except Exception:
        return False
    _sep = r"[\s\-_.:：,，/\\()\[\]{}]+"
    t_toks = [x for x in _wm_re.split(_sep, t) if len(x) >= 2]
    if not t_toks:
        return False
    n_toks = {x for x in _wm_re.split(_sep, n) if len(x) >= 2}
    if not n_toks:
        return False
    _noise = {"google", "microsoft", "windows", "www", "浏览器"}
    t_toks = [x for x in t_toks if x not in _noise]
    if not t_toks:
        return False
    return all(any(tok in nt or nt in tok for nt in n_toks) for tok in t_toks)

def _find_window(target):
    try:
        import win32gui, win32process
    except ImportError:
        return None
    # 中文→英文映射: 同时尝试原始关键词和映射关键词
    candidates = [target.lower()]
    for cn, en in _WINDOW_TITLE_MAP.items():
        if cn in target:
            candidates.append(en)
            candidates.append(f"{cn} - {en.capitalize()}")
    found = None
    def _cb(hwnd, _):
        nonlocal found
        if found: return
        try:
            title = win32gui.GetWindowText(hwnd)
            tl = title.lower()
            if win32gui.IsWindowVisible(hwnd) and (window_title_matches(target, title) or any(c in tl for c in candidates if c)):
                rect = win32gui.GetWindowRect(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                found = {"title": title, "hwnd": hwnd, "pid": pid, "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]}, "size": f"{rect[2]-rect[0]}x{rect[3]-rect[1]}"}
        except Exception as _e:
            print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
    win32gui.EnumWindows(_cb, None)
    return found

def _get_active_window():
    try:
        import win32gui, win32process
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return {"title": title, "hwnd": hwnd, "pid": pid, "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]}, "size": f"{rect[2]-rect[0]}x{rect[3]-rect[1]}"}
    except ImportError:
        return None

def _focus_window(hwnd):
    """强激活窗口 — 绕过Windows前台锁 (SetForegroundWindow对后台进程限制)"""
    try:
        import win32gui, win32con, win32process, win32api
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        try:
            cur = win32api.GetCurrentThreadId()
            fg = win32gui.GetForegroundWindow()
            fg_t = win32process.GetWindowThreadProcessId(fg)[0]
            if fg_t != cur:
                win32process.AttachThreadInput(cur, fg_t, True)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                finally:
                    win32process.AttachThreadInput(cur, fg_t, False)
        except Exception:
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception as _e:
                print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
        try:
            win32gui.BringWindowToTop(hwnd)
        except Exception as _e:
            print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
        try:
            if win32gui.GetForegroundWindow() != hwnd:
                import ctypes
                ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
                win32gui.SetForegroundWindow(hwnd)
        except Exception as _e:
            print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
        return win32gui.GetForegroundWindow() == hwnd
    except Exception:
        return False


def _uia_set_value_by_window(window_title, text):
    """UIA ValuePattern 直写 — 目标窗口内首个可编辑控件(Edit/Document) SetValue
    ⛔ 2026-08-13 打磨: 不依赖焦点/前台, 穿透完整性边界(UIA 跨同用户窗口无障碍)。
    前台被高完整性窗口锁定时物理输入无法落地(Medium→High UIPI), 此路径兜底。
    → {"ctrl", "method": "uia_setvalue"} | None
    """
    try:
        import uiautomation as _uia
        with _uia.UIAutomationInitializerInThread():
            root = _uia.GetRootControl()
            for w in root.GetChildren():
                try:
                    n = w.Name or ""
                    if window_title.lower() in n.lower() and "运行窗口" not in n:
                        _budget = [120]
                        def _walk(h, d=0):
                            if d > 6 or _budget[0] <= 0:
                                return None
                            try:
                                for c in h.GetChildren():
                                    if _budget[0] <= 0:
                                        return None
                                    _budget[0] -= 1
                                    ct = c.ControlTypeName.replace("Control", "")
                                    if ct in ("Edit", "Document"):
                                        try:
                                            vp = c.GetValuePattern()
                                            if vp is not None:
                                                vp.SetValue(text)
                                                return {"ctrl": (c.Name or "")[:50],
                                                        "method": "uia_setvalue"}
                                        except Exception as _e:
                                            print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
                                    rr = _walk(c, d + 1)
                                    if rr:
                                        return rr
                            except Exception as _e:
                                print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
                            return None
                        rr = _walk(w)
                        if rr:
                            return rr
                except Exception:
                    continue
    except Exception as _e:
        print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
    return None


def _uia_set_value_by_label(label, text):
    """UIA 标签定位直写 — 找到含 label 的控件所在窗口, 向窗口内首个可编辑控件(Edit/Document) SetValue
    ⛔ 2026-08-13 打磨: type_to_field UIA 兜底, 不依赖焦点/前台。
    两遍遍历: ① 窗口子树存在含 label 控件 → ② SetValue 该窗口首个可编辑控件。
    → {"ctrl", "window", "method": "uia_setvalue"} | None
    """
    try:
        import uiautomation as _uia
        with _uia.UIAutomationInitializerInThread():
            root = _uia.GetRootControl()
            for w in root.GetChildren():
                try:
                    n = w.Name or ""
                    if not n.strip() or "运行窗口" in n:
                        continue
                    _budget = [180]
                    def _has_label(h, d=0):
                        if d > 6 or _budget[0] <= 0:
                            return False
                        try:
                            for c in h.GetChildren():
                                if _budget[0] <= 0:
                                    return False
                                _budget[0] -= 1
                                cn = c.Name or ""
                                if label.lower() in cn.lower():
                                    return True
                                if _has_label(c, d + 1):
                                    return True
                        except Exception as _e:
                            print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
                        return False
                    if not _has_label(w):
                        continue
                    def _set_first(h, d=0):
                        if d > 6 or _budget[0] <= 0:
                            return None
                        try:
                            for c in h.GetChildren():
                                if _budget[0] <= 0:
                                    return None
                                _budget[0] -= 1
                                ct = c.ControlTypeName.replace("Control", "")
                                if ct in ("Edit", "Document"):
                                    try:
                                        vp = c.GetValuePattern()
                                        if vp is not None:
                                            vp.SetValue(text)
                                            return {"ctrl": (c.Name or "")[:50],
                                                    "window": (w.Name or "")[:60],
                                                    "method": "uia_setvalue"}
                                    except Exception as _e:
                                        print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
                                rr = _set_first(c, d + 1)
                                if rr:
                                    return rr
                        except Exception as _e:
                            print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
                        return None
                    rr = _set_first(w)
                    if rr:
                        return rr
                except Exception:
                    continue
    except Exception as _e:
        print(f"⚠️ omni_core: 吞错: {_e}", file=sys.stderr)
    return None


# ═══════════════════════════════════════════
#  ⛔ 自动生成: omni_core 共享基础设施 (拆分自 omni_tentacle, 2026-08-10)
#  所有 mixin 通过 `from omni_core import *` 获得模块级符号
# ═══════════════════════════════════════════
__all__ = ['sys', 'json', 'time', 'base64', 'io', 'Path', 'datetime', 'ROOT', '_MSS_SCT', '_DXCAM', '_DXCAM_FAIL_TS', '_DXCAM_BASE', '_DXCAM_BASE_TIME', '_NV_LITE', '_NV_LITE_TS', '_get_sct', '_get_dxcam', '_dxcam_frame', '_native_lite_eye', '_screen_capture', '_mouse_move', '_mouse_click', '_mouse_double_click', '_mouse_scroll', '_keyboard_type', '_keyboard_press', '_keyboard_hotkey', '_mouse_position', '_screen_size', '_enum_windows', 'window_title_matches', '_WINDOW_TITLE_MAP', '_find_window', '_get_active_window', '_focus_window', '_uia_set_value_by_window', '_uia_set_value_by_label']
