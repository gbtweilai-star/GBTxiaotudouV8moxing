"""工具能力层：让小土豆真正"会干活"。

参照 Miku On Desktop / Desktop Pet 的 MCP 工具集成思路，
提供本地工具注册表 + GLM function calling + 离线关键词触发双通道。
"""
from __future__ import annotations

import datetime
import logging
import os
import subprocess
import webbrowser

logger = logging.getLogger("potato.tools")

# CPU 采样基线：psutil 的 interval=None 是「距上次调用以来的平均占用」，
# 只有先建立基线才能给出真实读数。第一次必须带一个极短 interval，
# 否则首帧会显示假的 0%。
_CPU_BASELINE_READY = False


def _cpu_percent(psutil_mod) -> float:
    """非阻塞 CPU 读数。

    旧实现是 `psutil.cpu_percent(interval=0.3)`：面板每 5 秒在主线程直接调用
    （main.py 的 telemetry_timer 未 moveToThread），实测本机 psutil 7.2.2
    该调用实耗 0.303s —— 每 5 秒硬冻面板 300ms，正好压在打字/看流式输出时。
    现在只有首次调用花 50ms 建基线，之后是零阻塞取瞬时值。
    """
    global _CPU_BASELINE_READY
    if not _CPU_BASELINE_READY:
        _CPU_BASELINE_READY = True
        return float(psutil_mod.cpu_percent(interval=0.05))
    return float(psutil_mod.cpu_percent(interval=None))

# ---- 工具注册表（GLM function calling 的 tools 定义） ----
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "获取当前日期时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "获取电脑 CPU、内存、电池状态",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "打开一个应用或网站。app 参数从白名单里选：browser/notepad/calculator/bilibili/github",
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {
                        "type": "string",
                        "enum": ["browser", "notepad", "calculator", "bilibili", "github"],
                    }
                },
                "required": ["app"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder_hint",
            "description": "口头提醒用户某事（仅对话内提醒，不持久化）",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "提醒内容"},
                },
                "required": ["text"],
            },
        },
    },
]

# ---- 白名单 ----
_APP_WHITELIST = {
    "browser": "https://www.bing.com",
    "notepad": "notepad",
    "calculator": "calc",
    "bilibili": "https://www.bilibili.com",
    "github": "https://github.com",
}


def get_time() -> str:
    now = datetime.datetime.now()
    weekdays = "一二三四五六日"
    return f"现在是 {now.strftime('%Y年%m月%d日')} 星期{weekdays[now.weekday()]} {now.strftime('%H:%M')}"


def get_system_status() -> str:
    try:
        import psutil
        cpu = _cpu_percent(psutil)
        mem = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        parts = [f"CPU {cpu:.0f}%", f"内存 {mem.percent:.0f}%（{mem.used/1e9:.1f}/{mem.total/1e9:.1f}GB）"]
        if battery is not None:
            state = "充电中" if battery.power_plugged else "电池"
            parts.append(f"{state} {battery.percent:.0f}%")
        return "，".join(parts)
    except ImportError:
        # psutil 不可用时用 ctypes 拿内存（保持零依赖兜底）
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return f"内存占用 {m.dwMemoryLoad}%（总量 {m.ullTotalPhys/1e9:.1f}GB），CPU 数据需要 psutil"


def open_app(app: str) -> str:
    target = _APP_WHITELIST.get(app)
    if not target:
        return f"不认识「{app}」哦，我只会开：{'、'.join(_APP_WHITELIST)}"
    try:
        if target.startswith(("http://", "https://")):
            webbrowser.open(target)
        else:
            # R-H295：原来是 os.system(f"start {target}") —— 把 target 拼进 shell 命令行。
            # 实测追溯：target 只可能来自 _APP_WHITELIST 的 5 个常量（app 未命中就提前 return），
            # 所以**当前没有可达的注入路径**，扫描器报的 critical 是「无污点分析」的误报。
            # 但这层安全性依赖「白名单以后永不放入带参数的值」——是脆的（改一行白名单就破）。
            # 改成不经 shell 的启动方式：注入面按构造消失，不再依赖白名单纪律。
            if hasattr(os, "startfile"):        # Windows：走 ShellExecute，不经 shell
                os.startfile(target)
            else:                               # 非 Windows 兜底：列表形式同样不经 shell
                subprocess.Popen([target])
        return f"已为你打开 {app}~"
    except Exception as e:
        return f"打不开 {app}：{e}"


def set_reminder_hint(text: str) -> str:
    return f"好的，记住了：{text}"


# ---- 工具执行器 ----
def execute_tool(name: str, arguments: dict) -> str:
    handlers = {
        "get_time": get_time,
        "get_system_status": get_system_status,
        "open_app": lambda: open_app(arguments.get("app", "")),
        "set_reminder_hint": lambda: set_reminder_hint(arguments.get("text", "")),
    }
    fn = handlers.get(name)
    if fn is None:
        return f"未知工具：{name}"
    try:
        return fn()
    except Exception as e:
        logger.warning("tool %s failed: %s", name, e)
        return f"工具执行出错：{e}"


# ---- 离线关键词触发（无 API key 时的本地能力） ----
def try_offline_tool(text: str):
    """命中关键词时返回 (工具结果, True)，否则 (None, False)。"""
    t = text.strip()
    if any(k in t for k in ("几点", "时间", "日期", "几号", "星期几", "今天多少号")):
        return get_time(), True
    if any(k in t for k in ("电脑状态", "系统状态", "cpu", "CPU", "内存", "电量", "电池")):
        return get_system_status(), True
    if any(k in t for k in ("打开", "开一下", "帮我开")):
        for key in _APP_WHITELIST:
            if key.lower() in t.lower():
                return open_app(key), True
        return None, False
    return None, False
