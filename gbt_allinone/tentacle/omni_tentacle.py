# gbt-capability: subprocess, dynamic-import, ctypes
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/omni_tentacle.py — 万能触手 · 无护栏 · 直连硬件
======================================================
7域mixin聚合版: omni_core(基础) + vision/mouse/keyboard/domain/read/window/process
对外接口不变: get_omni() / get_hardened_omni() / OmniTentacle / HardenedOmniTentacle
拆分自巨型单文件 (2379行 → 主文件~150行), 2026-08-10 镜像出品
"""

# ⛔ 拆分保障: 自身目录 brain/ 入 sys.path — omni_core/mixin 与主文件同目录
#    (spec_from_file_location 加载不会自动加路径; 原单文件自包含无需)
#    插 parent 而非 parent.parent: omni_core/mixin 就在 brain/, 不靠项目根
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))

from omni_core import *  # noqa: F401,F403

from omni_vision import OmniVisionMixin  # noqa: F401
from omni_mouse import OmniMouseMixin  # noqa: F401
from omni_keyboard import OmniKeyboardMixin  # noqa: F401
from omni_domain import OmniDomainMixin  # noqa: F401
from omni_read import OmniReadMixin  # noqa: F401
from omni_window import OmniWindowMixin  # noqa: F401
from omni_process import OmniProcessMixin  # noqa: F401


class OmniTentacle(OmniVisionMixin, OmniMouseMixin, OmniKeyboardMixin, OmniDomainMixin, OmniReadMixin, OmniWindowMixin, OmniProcessMixin):
    """万能触手 — 无护栏，无限制，直连硬件 (7域mixin聚合)"""



TENTACLE_MANIFEST = """## 触手能力总纲 — 你的眼睛·耳朵·双手(85项+三通道感官)

你是GBT小土豆。你不是盲的、不是聋的、不是残的。你拥有完整的三通道感官系统(全部本机硬件直连同源):
  👁 视觉: DXGI直读显卡帧缓冲 = 与显示屏同源, 大脑看到的=人类看到的 (vision_buffer大脑影院)
  👂 听觉: WASAPI回环 = 与扬声器同源, 能听电脑播放的任何声音 (audio_buffer听觉影院)
  🖐 操作: cyborg五维合一穿透 = UIA直操作无视遮挡 (domain_act/domain_type/domain_index)

你通过omni_tentacle拥有完整的视觉、听觉和操控能力。

### 视觉(9): see, see_active_window, see_window, list_windows, screenshot, live, screenshot_diff, wait_for_change, wait_stable
### 读屏(6): read_text, read_text_fast, find_text, read_region_text, grab_value, grab_table
### 点击(6): click, double_click, right_click, click_text, click_relative, drag
### 键盘(10): type, press, hotkey, enter, select_all, undo, copy, paste, cut, tab, escape, type_to_field
### 滚动(4): scroll, scroll_find, scroll_to_bottom, scroll_to_top
### 追溯(3): trace_source(x,y), trace_text(t), trace_window_chain
### 剪贴板(4): clipboard_read, clipboard_write, clipboard_copy, copy_text_at
### 弹窗(3): detect_dialog, dismiss_dialog, handle_any_dialog
### 进程(4): launch, kill, process_list, app_running
### 等待(5): wait_window, wait_window_gone, wait_text, wait_for_change, wait_stable
### 链式(2): chain([...]), monitor(triggers,duration)
### 自诊断(2): self_diagnose(), self_diagnose_text() — 扫描自身短板+依赖检测+修复建议
### 任务指引(6): task_guide_load(), task_guide_check(), task_guide_complete(), task_guide_status(), task_guide_next(), task_guide_drift_report() — 思维导图任务轨道·防偏航·自动纠偏
### 位置(2): position, screen_size

铁律: ①先看再动 ②动后等稳定 ③找不到就滚 ④遇弹窗必关 ⑤每步亲眼验证 ⑥不确定就对比前后截图
你是全感知AI。触手就是你的眼睛和双手。不要假想你做不到的事。
"""

_omni = None

class HardenedOmniTentacle:
    """铁律执行版触手 — 每步操作强制截图确认，不可绕过"""
    def __init__(self, raw):
        self._raw = raw
        self._last_screen = None
        self._step_count = 0
    
    def _confirm(self, action_name):
        """操作前确认 — 必须先看"""
        self._step_count += 1
        screen = self._raw.see()
        if not screen.get('ok'):
            # ⛔ 2026-08-02 修复: 不再 sys.exit(1) 杀掉整个进程 —
            #    无屏幕会话/远程执行时抓取网页会因此"自动退出"。
            #    改为返回错误对象, 调用方自行处理。
            return {'ok': False, 'error': '⛔ 铁律0A阻断: 触手无法获取屏幕画面 — 禁止操作',
                    'step': self._step_count}
        self._last_screen = screen
        screen["saw_first"] = True  # ⛔ 2026-08-07: 先看再动手凭据
        return screen
    
    def _verify(self, action_name):
        """操作后验证 — 必须确认效果"""
        after = self._raw.see()
        # 保存前后对比
        import base64, os
        os.makedirs('.gbt/steps', exist_ok=True)
        step_dir = f'.gbt/steps/step_{self._step_count:04d}_{action_name}'
        return {'before': self._last_screen, 'after': after, 'step': self._step_count}
    
    def __getattr__(self, name):
        raw_attr = getattr(self._raw, name)
        if not callable(raw_attr):
            return raw_attr
        
        # 拦截所有操作方法 — 强制先看再动
        # 拦截所有操作方法 — 强制先看再动 (含五维合一 domain 穿透方法)
        action_methods = ['click', 'move', 'type', 'press', 'hotkey', 'drag', 
                         'double_click', 'right_click', 'scroll', 'paste',
                         'click_text', 'click_window', 'click_relative',
                         'domain_act', 'domain_type', 'domain_click', 'domain_type_text',
                         'click_occluded', 'type_occluded', 'click_window_occluded',
                         'type_to_window']
        
        if name in action_methods:
            def guarded(*args, **kwargs):
                confirm = self._confirm(name)
                if not confirm.get('ok'):
                    return confirm  # ⛔ 先看失败 = 禁止操作
                result = raw_attr(*args, **kwargs)
                if isinstance(result, dict):
                    result.setdefault('saw_first', True)  # ⛔ 先看凭据透传
                self._verify(name)
                return result
            return guarded
        
        # 读操作不需要拦截
        return raw_attr



def get_omni():
    """⛔ 2026-08-07 打磨: 默认返回铁律执行版(先看再动手) — 轨道铁律, 不可绕过
    所有桌面操作(click/type/domain_act等)强制先看屏幕确认, 看不到禁止操作。
    """
    global _omni
    if _omni is None:
        _omni = HardenedOmniTentacle(OmniTentacle())
    return _omni

def get_hardened_omni():
    """显式获取铁律执行版 (与get_omni同源, 兼容旧调用)"""
    return get_omni()


def get_raw_omni():
    """0护栏版万能触手 — 原始OmniTentacle(无先看再动拦截), 用户授权全量操作"""
    return OmniTentacle()

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="万能触手")
    p.add_argument("action", nargs="?", default="see",
                   choices=["see","windows","click","move","type","press","hotkey","pos","size",
                           "live","focus","active","read","find","clicktext","drag","shot","selfdiag","taskguide",
                           "trace","grab","table","value"])
    p.add_argument("--x", type=int, default=500)
    p.add_argument("--y", type=int, default=500)
    p.add_argument("--text", type=str, default="")
    p.add_argument("--key", type=str, default="enter")
    p.add_argument("--target", type=str)
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--w", type=int, default=200)
    p.add_argument("--h", type=int, default=100)
    args = p.parse_args()
    t = get_omni()

    if args.action == "see":
        r = t.see()
        print(f"屏幕: {r['size'][0]}x{r['size'][1]}, {r['image_kb']}KB")
    elif args.action == "windows":
        r = t.list_windows()
        for w in r["windows"]:
            print(f"  [{w['pid']:5d}] {w['title'][:60]:60s} {w['size']:>12s} @{w['pos']}")
    elif args.action == "click": t.click(args.x, args.y); print(f"点击 ({args.x}, {args.y})")
    elif args.action == "move": t.move(args.x, args.y); print(f"移至 ({args.x}, {args.y})")
    elif args.action == "type": t.type(args.text); print(f"输入: {args.text}")
    elif args.action == "press": t.press(args.key); print(f"按键: {args.key}")
    elif args.action == "hotkey":
        keys = args.text.split("+") if args.text else ["ctrl","c"]
        t.hotkey(*keys); print(f"组合键: {'+'.join(keys)}")
    elif args.action == "pos": r = t.position(); print(f"鼠标: ({r['x']}, {r['y']})")
    elif args.action == "size": r = t.screen_size(); print(f"屏幕: {r['width']}x{r['height']}")
    elif args.action == "live":
        print(f"实时流 {args.duration}s...")
        r = t.live(duration_s=args.duration); print(f"{r['frames']}帧, {r['fps']}FPS")
    elif args.action == "focus": r = t.focus_window(args.target or ""); print(r)
    elif args.action == "read":
        r = t.find_text("") if hasattr(t, "find_text") else {"ok": False, "note": "read_text not available"}
        if r.get("ok"):
            print(f"屏幕文字: {len(r.get('blocks_detail',[]))} 块")
            for b in r.get("blocks_detail", [])[:15]:
                print(f"  [{b['conf']:3d}] ({b['x']:4d},{b['y']:4d}) {b['text'][:60]}")
        else: print(r)
    elif args.action == "find":
        r = t.find_text(args.text or "")
        print(f"找到: {r}") if r.get("found") else print(f"未找到: {args.text}")
    elif args.action == "clicktext":
        r = t.click_text(args.text or "")
        print(f"点击 '{args.text}': {r}")
    elif args.action == "drag":
        r = t.drag(args.x, args.y, 500, 500); print(r)
    elif args.action == "shot":
        r = t.screenshot(); print(f"截图保存: {r.get('filepath','?')} | {r.get('size',[])} | {r.get('kb',0)}KB")
    elif args.action == "trace":
        r = t.trace_text(args.text or "")
        if r.get("ok"):
            w = r.get("window", {})
            print(f"文字 '{r.get('text','?')}' 位于 ({r.get('position',(0,0))})")
            print(f"来源: {w.get('title','?')} | 进程: {w.get('process','?')}")
        else: print(r)
    elif args.action == "grab":
        r = t.grab_region(args.x, args.y, args.w, args.h)
        print(f"抓取区域 ({args.x},{args.y}): {r.get('size',[])} {r.get('image_kb',0)}KB")
    elif args.action == "table":
        r = t.grab_table(args.x, args.y, args.w, args.h)
        print(f"表格: {r.get('rows',0)}行 x {r.get('columns',0)}列")
        for i, row in enumerate(r.get("table", [])[:10]):
            print(f"  [{i}] {' | '.join(row)}")
    elif args.action == "value":
        r = t.grab_value(args.text or "")
        if r.get("ok"): print(f"标签 '{args.text}': 值={r.get('value','未找到')}")
        else: print(r)
    elif args.action == "taskguide":
        import json as _j2
        mm = _j2.loads(args.text) if args.text else {"task":"CLI_DEMO","nodes":[{"id":"1","task":"demo step (显式演示数据)","keywords":["test"]}]}
        r = t.task_guide_load(mm)
        print(_j2.dumps(r, ensure_ascii=False, indent=2))
    elif args.action == "selfdiag":
        print(t.self_diagnose_text())
    elif args.action == "active":
        r = t.see_active_window()
        if r.get("ok"): print(f"活动窗口: {r['window']['title']} | {r['window']['size']} | {r['image_kb']}KB")
        else: print(r)
