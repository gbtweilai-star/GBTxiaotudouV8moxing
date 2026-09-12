# gbt-capability: subprocess, dynamic-import, ctypes, base64
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# vision 域 mixin — 拆分自 omni_tentacle (自动生成, 2026-08-10)
# ⛔ 拆分保障: 自身目录(brain/)入 sys.path — spec_from_file_location 加载
#    不会自动加路径, 需显式保障 omni_core 可寻址 (插 brain/ 而非项目根)
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
# publish沙盒(非项目根cwd)执行兜底: 类定义不访问core符号, 吞异常安全
try:
    from omni_core import *  # noqa: F401,F403
except Exception:
    pass


class OmniVisionMixin:
    """vision 域能力 — 8 方法"""

    def see(self, region=None):
        cap = _screen_capture(region)
        # ⛔ 2026-08-04 触手→大脑: 截屏摘要穿透传输
        if cap.get("ok"):
            try:
                from brain.tentacle_transmission import transmit as _tx
                _tx({"size": cap.get("size", [0, 0]), "ok": True,
                     "channel": "screen", "format": cap.get("format", "PNG")},
                    source="omni_tentacle.see", channel="visual", priority="normal")
            except Exception: pass  # 容错: 非关键路径
        return cap

    def see_active_window(self):
        win = _get_active_window()
        if not win: return {"ok": False, "error": "无法获取活动窗口"}
        r = win["rect"]
        cap = _screen_capture({"x": r["left"], "y": r["top"], "w": r["right"]-r["left"], "h": r["bottom"]-r["top"]})
        cap["window"] = win
        return cap

    def see_window(self, target):
        win = _find_window(target)
        if not win: return {"ok": False, "error": f"未找到窗口: {target}"}
        r = win["rect"]
        cap = _screen_capture({"x": r["left"], "y": r["top"], "w": r["right"]-r["left"], "h": r["bottom"]-r["top"]})
        cap["window"] = win
        return cap

    def list_windows(self):
        return {"ok": True, "windows": _enum_windows()}

    def screenshot(self, filepath: str = None, region: dict = None):
        """截图 — 默认内存回传不落盘; 显式 filepath 走镜像出品写盘(b64文本)
        ⛔ 2026-08-13 打磨: v5.5 写保护拦截裸写(与 export_data 同类), 且临时画面
        数据落盘违反数据铁律(边操作边过滤)。默认通道 memory, 显式保存走 publish。"""
        cap = _screen_capture(region, fmt="png")
        if not cap["ok"]:
            return cap
        if filepath is None:
            return {"ok": True, "size": cap["size"], "kb": cap["image_kb"],
                    "image_base64": cap["image_base64"], "channel": "memory"}
        try:
            import brain.gatekeeper as _gk_shot
            _res = _gk_shot.publish(str(filepath), cap["image_base64"], "omni_tentacle_screenshot")
        except Exception as e:
            return {"ok": False, "error": f"截图写盘被管线拒绝: {str(e)[:100]}"}
        if not _res.get("ok"):
            return {"ok": False, "error": f"截图写盘被管线拒绝: {_res.get('error','?')[:100]}"}
        return {"ok": True, "filepath": str(filepath), "size": cap["size"], "kb": cap["image_kb"],
                "format": "base64_text", "channel": "mirror_pipeline"}

    def screenshot_diff(self, other_filepath: str = None):
        """截图对比 — 当前画面 vs 之前保存的截图"""
        import hashlib
        current = _screen_capture()
        current_hash = hashlib.sha256(
            __import__('base64').b64decode(current["image_base64"])
        ).hexdigest()[:16]

        if other_filepath:
            try:
                other_data = __import__('base64').b64encode(
                    Path(other_filepath).read_bytes()
                ).decode()
                other_hash = hashlib.sha256(
                    Path(other_filepath).read_bytes()
                ).hexdigest()[:16]
                changed = current_hash != other_hash
                return {"ok": True, "changed": changed, "current_hash": current_hash,
                       "other_hash": other_hash, "other_file": other_filepath}
            except Exception as e:
                return {"ok": False, "error": str(e)[:100]}

        # 与上次对比
        if hasattr(self, '_last_screenshot_hash'):
            changed = current_hash != self._last_screenshot_hash
            result = {"ok": True, "changed": changed, "current_hash": current_hash,
                     "previous_hash": self._last_screenshot_hash}
        else:
            result = {"ok": True, "changed": None, "current_hash": current_hash,
                     "note": "首次截图，无对比基准"}
        
        self._last_screenshot_hash = current_hash
        return result

    def wait_for_change(self, timeout: float = 30, interval: float = 0.5):
        """等待画面变化"""
        import hashlib
        base = _screen_capture()
        base_hash = hashlib.sha256(
            __import__('base64').b64decode(base["image_base64"])
        ).hexdigest()

        end = time.time() + timeout
        while time.time() < end:
            cur = _screen_capture()
            cur_hash = hashlib.sha256(
                __import__('base64').b64decode(cur["image_base64"])
            ).hexdigest()
            if cur_hash != base_hash:
                return {"ok": True, "changed": True,
                       "elapsed": round(timeout - (end - time.time()), 1)}
            time.sleep(interval)
        return {"ok": True, "changed": False, "timeout": timeout}

    def live(self, duration_s=10, interval_ms=500):
        frames = []
        end = time.time() + duration_s
        while time.time() < end:
            t0 = time.time()
            cap = _screen_capture()
            frames.append({"ts": datetime.now().isoformat(), "size": cap["size"], "kb": cap["image_kb"]})
            elapsed = (time.time() - t0) * 1000
            sleep_s = max(0, interval_ms - elapsed) / 1000
            if sleep_s > 0: time.sleep(sleep_s)
        return {"ok": True, "duration_s": duration_s, "frames": len(frames), "fps": round(len(frames) / max(duration_s, 0.1), 1)}

    # ═══ 视觉传输总线（V8：视觉也是传输——缓存/定位/流/回放）═══

    def vision_snapshot(self, region=None, ttl=60):
        """带缓存的视觉快照：同画面指纹命中缓存则零成本复用（视觉的 cache:true）。"""
        import importlib as _il
        try:
            vision_bus = _il.import_module('gbt_allinone.tentacle.vision_bus')
        except Exception:
            vision_bus = _il.import_module('vision_bus')
        return vision_bus.snapshot(self, region, ttl)

    def vision_diff(self, grid=4):
        """变化区域定位：与上次快照对比，给出变化矩形（网格哈希），非只说"变了"。"""
        import importlib as _il
        try:
            vision_bus = _il.import_module('gbt_allinone.tentacle.vision_bus')
        except Exception:
            vision_bus = _il.import_module('vision_bus')
        return vision_bus.diff_with_previous(self, grid)

    def vision_stream_record(self, duration_s=10, interval_ms=500, stream_name=None):
        """视觉流记录：帧时间线（指纹+变化）落 store，可回放。"""
        import importlib as _il
        try:
            vision_bus = _il.import_module('gbt_allinone.tentacle.vision_bus')
        except Exception:
            vision_bus = _il.import_module('vision_bus')
        return vision_bus.stream_record(self, duration_s, interval_ms, stream_name)

    def vision_stream_replay(self, name=None, limit=50):
        """视觉流回放：帧时间线 + 变化段提取。"""
        import importlib as _il
        try:
            vision_bus = _il.import_module('gbt_allinone.tentacle.vision_bus')
        except Exception:
            vision_bus = _il.import_module('vision_bus')
        return vision_bus.stream_replay(name, limit)
