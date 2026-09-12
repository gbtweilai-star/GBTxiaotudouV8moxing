"""GBT小土豆V8 · 触手桥（tentacle bridge）—— 连接大脑执行层的金钥匙。

Owner 定位（2026-09-11）：触手是连接大脑执行层的金钥匙——触手拥有小土豆的全部能力。
所有邻域皆触手所化：感知/桌面/侦察/自动化/运维/信息/金融……触手每一次强化 = 全邻域提升。

架构（V8 复活版，从归档区 brain/tentacle_bridge.py + omni_tentacle.py 迁移重写）：
  tentacle/           硬件层（10 个 omni_* 文件，原样迁移，不改一行逻辑）
  tentacle/bridge.py  金钥匙（本文件）：全框架唯一一只眼睛一双手的单例管理
                      + 66 项能力清单 + 10 邻域覆盖映射 + 六铁律

依赖（已装入 .pylibs，缺哪层哪层如实降级）——实测 DXGI 热路径 28-34ms/帧：
  ctypes（键鼠/窗口，标准库）→ 0 依赖可用
  mss（BitBlt 截图兜底）→ 截图可用
  uiautomation+comtypes（UIA 穿透）→ 读屏/域操作可用
  dxcam+numpy（DXGI 硬采加速）→ 可选，缺失自动降级 mss

铁律（继承自原版 MANIFEST，不可绕过）：
  ①先看再动 ②动后等稳定 ③找不到就滚 ④遇弹窗必关 ⑤每步亲眼验证 ⑥不确定就对比前后截图
"""
import json
import sys
import time
from pathlib import Path

_TENTACLE_DIR = Path(__file__).resolve().parent

# 依赖注入：触手包依赖 .pylibs 的 mss/uiautomation/comtypes
_PYLIBS = _TENTACLE_DIR.parent / ".pylibs"
if _PYLIBS.exists() and str(_PYLIBS) not in sys.path:
    sys.path.insert(0, str(_PYLIBS))
if str(_TENTACLE_DIR) not in sys.path:
    sys.path.insert(0, str(_TENTACLE_DIR))

_eye = None
_manifest = ""
_eye_error = ""


def get_eye():
    """获取共享触手实例——整个框架只有这一只眼睛一双手（单例）。"""
    global _eye, _eye_error
    if _eye is None:
        try:
            import importlib.util as iu
            spec = iu.spec_from_file_location("_omni_v8", str(_TENTACLE_DIR / "omni_tentacle.py"))
            mod = iu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _eye = mod.get_omni()
        except Exception as e:  # noqa: BLE001
            _eye_error = f"{type(e).__name__}: {e}"[:200]
            _eye = _DummyEye(_eye_error)
    return _eye


def eye_ready() -> bool:
    """触手是否就绪（硬件层加载成功）。"""
    return not isinstance(get_eye(), _DummyEye)


def eye_error() -> str:
    """触手未就绪时的根因（如实报告，不吞）。"""
    get_eye()
    return _eye_error


def get_manifest() -> str:
    """触手能力总纲——85 项能力 + 三通道感官 + 六铁律。"""
    global _manifest
    if not _manifest:
        try:
            import importlib.util as iu
            spec = iu.spec_from_file_location("_omni_mf_v8", str(_TENTACLE_DIR / "omni_tentacle.py"))
            mod = iu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _manifest = getattr(mod, "TENTACLE_MANIFEST", "")
        except Exception:
            _manifest = "触手能力清单暂不可用"
    return _manifest


# ═══════════════════════════════════════════════════════════
#  触手→邻域 能力映射（继承原版 17 邻域：所有邻域皆触手所化）
# ═══════════════════════════════════════════════════════════

TENTACLE_NEIGHBORHOOD_MAP = {
    "感知域": {"powered_by": ["see", "read_text", "find_text", "screenshot", "live", "read_region_text"]},
    "桌面域": {"powered_by": ["click", "type", "scroll", "drag", "hotkey", "move", "click_text",
                              "type_to_field", "launch", "kill", "app_running", "focus_window"]},
    "侦察域": {"powered_by": ["trace_source", "trace_text", "trace_window_chain", "see_window",
                              "list_windows", "grab_value", "grab_table"]},
    "自动化": {"powered_by": ["chain", "monitor", "watch_and_click", "wait_text",
                              "wait_for_change", "handle_any_dialog", "scroll_find"]},
    "信息域": {"powered_by": ["read_text", "find_text", "grab_value", "grab_table", "clipboard_read",
                              "clipboard_write", "copy_text_at", "read_region_text"]},
    "运维域": {"powered_by": ["launch", "kill", "process_list", "app_running", "clipboard_read",
                              "clipboard_write", "screenshot", "wait_window"]},
    "AI编程": {"powered_by": ["type", "hotkey", "click", "clipboard_write", "paste", "launch",
                               "see", "screenshot"]},
    "金融域": {"powered_by": ["read_text", "find_text", "grab_value", "grab_table",
                              "click_text", "type", "screenshot"]},
    "媒体域": {"powered_by": ["see", "screenshot", "live", "see_window", "screenshot_diff"]},
    "安全域": {"powered_by": ["trace_source", "trace_window_chain", "detect_dialog",
                              "handle_any_dialog", "monitor", "see"]},
}


def coverage() -> dict:
    """触手对各邻域的覆盖度 + 协同提升关系。"""
    all_methods = set()
    for info in TENTACLE_NEIGHBORHOOD_MAP.values():
        all_methods.update(info["powered_by"])
    cov = {}
    for domain, info in TENTACLE_NEIGHBORHOOD_MAP.items():
        methods = info["powered_by"]
        cov[domain] = {
            "methods": len(methods),
            "key_capability": methods[0] if methods else "none",
        }
    return {
        "ok": True,
        "total_domains": len(TENTACLE_NEIGHBORHOOD_MAP),
        "total_tentacle_methods_used": len(all_methods),
        "coverage": cov,
        "eye_ready": eye_ready(),
        "truth": "所有邻域皆触手所化。触手每一次强化=全邻域提升。",
    }


def invoke(method: str, *args, **kwargs) -> dict:
    """统一调用入口：大脑执行层经此驱动触手的任意能力。

    走 V8 纪律：结果统一 dict、异常如实报、每次调用落审计（由 api 层负责）。
    """
    e = get_eye()
    if isinstance(e, _DummyEye):
        return {"ok": False, "error": f"触手未就绪: {_eye_error}", "method": method}
    fn = getattr(e, method, None)
    if fn is None or not callable(fn):
        return {"ok": False, "error": f"触手无此能力: {method}", "method": method,
                "hint": "能力清单见 tentacle_manifest"}
    try:
        r = fn(*args, **kwargs)
        if not isinstance(r, dict):
            r = {"ok": True, "value": r, "method": method}
        return r
    except Exception as ex:  # noqa: BLE001
        return {"ok": False, "error": f"{type(ex).__name__}: {ex}"[:200], "method": method}


def self_diagnose() -> dict:
    """触手自诊断：硬件层就绪度 + 依赖分层 + 可用能力数。"""
    deps = {}
    for mod, label in (("ctypes", "键鼠/窗口（标准库）"), ("mss", "截图（BitBlt 兜底）"),
                       ("uiautomation", "读屏/UIA 穿透"), ("dxcam", "DXGI 硬采加速（可选）")):
        try:
            __import__(mod)
            deps[mod] = {"ok": True, "role": label}
        except Exception as ex:  # noqa: BLE001
            deps[mod] = {"ok": False, "role": label, "error": str(ex)[:80]}
    manifest = get_manifest()
    method_count = 0
    if "触手能力清单暂不可用" not in manifest:
        import re
        for m in re.findall(r"###\s*(.+?)\((\d+)\)", manifest):
            method_count += int(m[1])
    return {
        "ok": eye_ready(),
        "eye_error": _eye_error or None,
        "deps": deps,
        "manifest_methods": method_count,
        "neighborhoods": len(TENTACLE_NEIGHBORHOOD_MAP),
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


class _DummyEye:
    """触手未就绪时的占位符——不阻塞框架运行，但如实报错。"""
    def __init__(self, reason=""):
        self._reason = reason

    def __getattr__(self, name):
        def _dummy(*args, **kwargs):
            return {"ok": False, "error": f"触手未就绪: {self._reason}", "method": name}
        return _dummy

    def __bool__(self):
        return False
