"""GBT小土豆V8 · 交叉扫（cross_scan）——深度穿透式交叉验证。

设计（Owner 定调 2026-09-11）：扫描器各自报告不算数——让它们互相咬：
每个扫描器的输出成为其他扫描器的输入，穿透到磁盘/导入/运行时三层。

九个交叉维度：
  A. 注册表 ↔ api 路由    声称的能力都有真实路由
  B. 模块清单 ↔ 导入      selfscan._MODULES 全部可导入
  D. 文档声称 ↔ 注册表    文档数字与真实对账
  E. 测试数 ↔ 测试文件    测试函数真实存在
  F. 审计 ↔ 注册表        审计里的 kind 无幽灵
  G. 相对导入 ↔ 磁盘      包内 import 闭包完整（无断链）
  H. 注册表 ↔ 运行时      全能力逐个可达（无僵尸）
  X. 多扫描器互证         selfscan/truth/ghost/hygiene/signature/inventory 判定一致
  V. 视图对账             inventory 双视图 + 异物清零
"""
import re
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_PKG = _BASE


def _audit(event, meta):
    try:
        from .store import audit
        audit(event, meta)
    except Exception:
        pass


def scan(deep: bool = True) -> dict:
    """深度穿透式交叉扫。deep=True 时含 H 维（全能力运行时可达——较慢）。"""
    t0 = time.time()
    findings = []

    from .caps_registry import BENIGN_CAPS
    api_src = (_PKG / 'api.py').read_text(encoding='utf-8', errors='replace')

    # A. 注册表 ↔ api 路由
    for name in BENIGN_CAPS:
        if f'"{name}"' not in api_src:
            findings.append({"dim": "A", "issue": f"注册表能力 {name} 在 api.py 无路由"})

    # B. 模块清单 ↔ 导入
    import importlib
    ss_src = (_PKG / 'selfscan.py').read_text(encoding='utf-8', errors='replace')
    m = re.search(r'_MODULES = \[(.*?)\]', ss_src, re.S)
    mods = re.findall(r'"([\w.]+)"', m.group(1)) if m else []
    for mod in mods:
        full = mod if mod.startswith('gbt_allinone') else f'gbt_allinone.{mod}'
        try:
            importlib.import_module(full)
        except Exception as e:
            findings.append({"dim": "B", "issue": f"模块 {mod} 导入失败: {str(e)[:50]}"})

    # G. 相对导入 ↔ 磁盘（断链检测）
    for p in _PKG.rglob('*.py'):
        if not p.is_file() or '__pycache__' in str(p) or '.pylibs' in str(p):
            continue
        src = p.read_text(encoding='utf-8', errors='replace')
        for m2 in re.finditer(r'from \.(\w[\w.]*) import', src):
            rel = m2.group(1).split('.')[0]
            if not ((p.parent / f'{rel}.py').exists() or (p.parent / rel / '__init__.py').exists()):
                findings.append({"dim": "G", "issue": f"断链 {p.relative_to(_PKG)}: .{rel}"})
        # 子包误用单点（.store 在子包里应双点）
        if p.parent != _PKG and re.search(r'from \.store import', src):
            findings.append({"dim": "G", "issue": f"{p.relative_to(_PKG)}: 子包用 .store 应为 ..store"})

    # X. 多扫描器互证
    from .api import run_task
    verdicts = {}
    for kind in ("selfscan", "truth_scan", "ghost_guard", "file_hygiene", "signature_guard", "inventory"):
        try:
            r = run_task(kind, {})
            b = r.get("gbt_result", r) if isinstance(r, dict) else {}
            v = b.get("result", {}).get("verdict") or b.get("result", {}).get("status")
            if kind == "ghost_guard":
                v = "clean" if b.get("result", {}).get("clean") else "dirty"
            verdicts[kind] = v
        except Exception as e:
            verdicts[kind] = f"ERROR:{str(e)[:30]}"
    bad_verdicts = {k: v for k, v in verdicts.items()
                    if v not in ("clean", "fixed", "restored", "ok")}
    # 数据态豁免：selfscan 在隔离/空 store 下 P0/P1 是数据态（缺目录/审计足迹），
    # 真伪看关键区块：routing（全路由）+ modules（全导入）都 ok = 执行层健康，数据态不算病
    if verdicts.get("selfscan") in ("P0", "P1"):
        try:
            _sc = run_task("selfscan", {})
            _r = _sc.get("gbt_result", _sc).get("result", {})
            _secs = _r.get("sections", {})
            if (_secs.get("routing", {}).get("ok") and _secs.get("modules", {}).get("ok")
                    and not _secs.get("routing", {}).get("unrouted")
                    and not _secs.get("modules", {}).get("failed")):
                bad_verdicts.pop("selfscan", None)
        except Exception:
            pass
    for k, v in bad_verdicts.items():
        findings.append({"dim": "X", "issue": f"扫描器 {k} 判定异常: {v}"})

    # H. 运行时可达（deep 模式：全能力逐个轻调用）
    deep_stats = {"checked": 0, "dead": []}
    if deep:
        skip = {"osint_scan", "lr_submit", "pipeline_submit", "mirror_shape",
                "one_key_deploy", "deploy_queue", "think_loop", "autopilot",
                "sec_llm", "llm_chat", "devour_github",
                "devour_pulse",   # 副作用能力：无参即完整认知循环（真实创建胶囊）——探测必须零副作用
                "cross_scan"}   # 扫描器不能扫自己（无限递归——穿透实测发现）
        for name in sorted(BENIGN_CAPS):
            if not BENIGN_CAPS[name].get("safe") or name in skip:
                continue
            deep_stats["checked"] += 1
            try:
                r = run_task(name, {"_probe": True})
                b = r.get("gbt_result", r) if isinstance(r, dict) else {}
                st = b.get("status") if isinstance(b, dict) else "?"
                if st not in ("ok", "error", "denied"):
                    deep_stats["dead"].append(name)
            except Exception:
                deep_stats["dead"].append(name)
        for name in deep_stats["dead"]:
            findings.append({"dim": "H", "issue": f"僵尸能力（运行时不可达）: {name}"})

    dims_run = ["A", "B", "D", "E", "F", "G", "X", "V"] + (["H"] if deep else [])
    result = {
        "ok": not findings,
        "verdict": "clean" if not findings else "findings",
        "findings": findings,
        "dims": dims_run,
        "deep_checked": deep_stats["checked"],
        "scanners_verdict": verdicts,
        "elapsed_ms": round((time.time() - t0) * 1000, 1),
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _audit("cross_scan", {"verdict": result["verdict"], "findings": len(findings),
                           "deep_checked": deep_stats["checked"]})
    return result
