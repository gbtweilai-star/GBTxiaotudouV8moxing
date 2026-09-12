"""GBT 量化技术能力（读取 Workspace 项目真实代码，返回真实技术分析）。

只读：解析量化引擎/回测 API 的类、信号、参数模型。不读取 .env/密钥，不触发任何交易。"""
import re
from pathlib import Path

WS = Path(r"C:\Users\ADMIN\Desktop\Workspace")
ENGINE_FILES = [
    WS / "01_量化收割引擎" / "cis_scalper" / "cis_quant_engine.py",
    WS / "01_量化收割引擎" / "cis_harvesting" / "cis_harvesting_system_v2.py",
]
BACKTEST_FILES = [
    WS / "01_量化收割引擎" / "backtest" / "backtest_api_v3.py",
    WS / "01_量化收割引擎" / "backtest" / "backtest_engine_v3.py",
]


def _read_first(p, n=400):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:n]
    except Exception:
        return ""


def _extract_enums(text):
    """提取所有 enum 类名与其成员。"""
    enums = []
    for m in re.finditer(r"class\s+(\w+)\(Enum\):([^\n]*(?:\n\s{4}\w+[^\n]*)*)", text):
        name = m.group(1)
        members = re.findall(r"^\s{4}(\w+)\s*=\s*[\"']?([^\"'\n]*)", m.group(2), re.M)
        enums.append({"enum": name, "members": [a for a, b in members]})
    return enums


def _extract_dataclass_fields(text):
    """提取标 @dataclass 的类及其字段。"""
    out = []
    for m in re.finditer(r"@dataclass\s*\nclass\s+(\w+):\n((?:[ \t]+\w+.*\n)+)", text):
        cls = m.group(1)
        fields = [l.strip().split("=")[0].strip().lstrip(":")[0].split(":")[0].strip()
                  for l in m.group(2).splitlines() if l.strip()]
        out.append({"class": cls, "fields": fields})
    return out


def quant_strategy():
    """读取真实量化引擎，返回策略信号模型与仓位模型。"""
    report = {}
    for p in ENGINE_FILES:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        report[p.name.replace(".py", "")] = {
            "enums": _extract_enums(t),
            "dataclasses": _extract_dataclass_fields(t),
            "bytes": len(t.encode("utf-8")),
        }
    if not report:
        return {"status": "no_engine_found", "hint": str(WS)}
    return {"engine_files": [p.name for p in ENGINE_FILES if p.exists()], "models": report}


def quant_backtest():
    """读取真实回测 API，返回类/函数/参数线索。"""
    report = []
    for p in BACKTEST_FILES:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        classes = re.findall(r"class\s+(\w+)", t)
        funcs = re.findall(r"def\s+(\w+)", t)
        params = re.findall(r"(\w+)\s*:\s*[A-Za-z_][\w.]*\s*=\s*([^\n,]+)", t)
        report.append({"file": p.name, "classes": classes[:20], "functions": funcs[:20],
                       "default_params": dict(params[:30])})
    return {"backtest_modules": report}


_PROFILE_CACHE = {"ts": 0.0, "data": None}


def platform_profile(ttl: int = 30):
    """读取 Workspace 项目结构（真实；TTL 缓存——目录遍历 87ms→首次后 0ms）。

    缓存 30 秒：项目结构不会秒级变化，而调用方（autopilot/巡检）可能高频调。
    """
    import time as _t
    if _PROFILE_CACHE["data"] is not None and _t.time() - _PROFILE_CACHE["ts"] < ttl:
        return dict(_PROFILE_CACHE["data"])
    profile = {"workspace": str(WS), "exists": WS.exists(), "top_level_dirs": [],
               "quant_py": 0, "py_total": 0}
    if WS.exists():
        profile["top_level_dirs"] = sorted(d.name for d in WS.iterdir() if d.is_dir())
        py = list(WS.rglob("*.py"))
        profile["py_total"] = sum(1 for f in py if "__pycache__" not in f.parts)
        qdir = WS / "01_量化收割引擎"
        profile["quant_py"] = sum(1 for f in qdir.rglob("*.py") if "__pycache__" not in f.parts) if qdir.exists() else 0
    _PROFILE_CACHE["ts"] = _t.time()
    _PROFILE_CACHE["data"] = profile
    return dict(profile)


def quant_params():
    """读取真实量化引擎的数值型策略参数（如动量周期/阈值/止损倍数）。"""
    out = {}
    for p in ENGINE_FILES:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        params = {}
        for m in re.finditer(r"^\s*(\w+)\s*:\s*(?:int|float)\s*=\s*([0-9]+(?:\.[0-9]+)?)", t, re.M):
            params[m.group(1)] = float(m.group(2))
        out[p.name] = params
    return {"engine_params": out}
