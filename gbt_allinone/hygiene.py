# -*- coding: utf-8 -*-
"""文件卫生层：按 LAYOUT.md 自检乱放 + 自动归位 + 审计留痕。

判定规则与 LAYOUT.md 铁律一一对应（家规与执行永远一致）。
"""
import json
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent          # gbt_allinone/
_HOME = _BASE.parent                             # 家根

# ── 家规常量（与 LAYOUT.md 同步）──
# 家根归属单一来源（v2 根治版）：不再枚举白名单（枚举永远追不上变化）——
# 唯一裁判是 inventory._classify（framework / environment / transient / foreign）。
# 框架三件之外，凡 inventory 判为 environment（OpenClaw 工作区）或 transient（运行足迹）一律放行。
HOME_ALLOWED = {"README.md", "requirements.txt", "gbt_allinone"}


def _home_allowed(p) -> bool:
    """家根单文件归属裁决（单一来源：inventory 分类）。"""
    name = p.name if hasattr(p, "name") else str(p)
    if name in HOME_ALLOWED:
        return True
    try:
        from .inventory import _is_environment
        if _is_environment(name):
            return True
        from .inventory import _classify
        return _classify(p if hasattr(p, "name") else __import__("pathlib").Path(str(p))) == "transient"
    except Exception:
        return False
PKG_MD_ALLOWED = {"README.md", "SOUL.md", "CODING_DISCIPLINE.md", "LAYOUT.md"}
PKG_DIRS = {"adapters", "bridge", "deploy", "docs", "examples", "integration",
            "ledger", "llm", "recon", "security", "store", "tentacle", "tests",
            "wallet", "archived_logs", ".pylibs"}
DATA_SUFFIX = {".jsonl"}
TEMP_PREFIXES = ("_",)
SKIP_TREES = {".pylibs", "archived_logs", "store", "__pycache__"}   # 这些树内部不按顶层规则管


def _audit(event, meta):
    try:
        from .store import audit
        audit(event, meta)
    except Exception:
        pass


def scan(fix: bool = False) -> dict:
    """体检家规执行情况。fix=True 时自动归位/清理并留审计。"""
    t0 = time.time()
    findings = []
    fixed = []

    def _fix(action, detail):
        fixed.append({"action": action, "detail": detail})

    # ── 铁律 1：零游离（家根只允许三样；_*.py 临时脚本=运行足迹，观察者效应，不算游离）──
    for p in _HOME.iterdir():
        if p.name in (".git",):
            continue
        if not _home_allowed(p):
            findings.append({"rule": "home_stray", "path": p.name,
                             "why": "家根归属异常（inventory 判为 foreign——既非框架、环境、也非运行足迹）"})
            if fix:
                # 归位：md -> gbt_allinone/docs/（除非与家规冲突），脚本类 -> 删（临时残留）
                if p.suffix == ".py" and p.name.startswith(TEMP_PREFIXES):
                    p.unlink()
                    _fix("del_temp_script", str(p))
                else:
                    print(f"[hygiene] 需人工确认的家根游离物: {p}（不自动移动）")

    # ── 铁律 1b：包根 md 白名单 ──
    for p in _BASE.iterdir():
        if p.is_file() and p.suffix == ".md" and p.name not in PKG_MD_ALLOWED:
            findings.append({"rule": "pkg_md_stray", "path": p.name,
                             "why": f"包根 md 只允许 {sorted(PKG_MD_ALLOWED)}"})
            if fix:
                target = _BASE / "docs" / p.name
                target.parent.mkdir(exist_ok=True)
                p.rename(target)
                _fix("mv_md_to_docs", f"{p.name} -> docs/")

    # ── 铁律 2：零临时残留（包内 _*.py / *.tmp；dunder 与 _paths.py 是家规内文件）──
    KEEP = {"__init__.py", "__main__.py", "_paths.py"}
    for p in _BASE.rglob("*"):
        parts = p.relative_to(_BASE).parts
        if parts[0] in SKIP_TREES:
            continue
        if p.is_file() and p.name not in KEEP and (
                p.name.startswith(TEMP_PREFIXES) and p.suffix == ".py" or p.suffix == ".tmp"):
            findings.append({"rule": "temp_leftover", "path": str(p.relative_to(_BASE)),
                             "why": "工作脚本/临时文件用完应删"})
            if fix:
                p.unlink()
                _fix("del_temp", str(p.relative_to(_BASE)))

    # ── 铁律 3：零缓存入库（__pycache__ 顺带清）──
    n_cache = 0
    for pc in _BASE.rglob("__pycache__"):
        if pc.is_dir():
            n_cache += 1
            if fix:
                import shutil
                shutil.rmtree(pc)
    if n_cache and fix:
        _fix("clear_pycache", f"{n_cache} 个")

    # ── 铁律 4：空壳目录（只含 marker）──
    for d in _BASE.iterdir():
        if d.is_dir() and d.name not in PKG_DIRS and d.name != "__pycache__":
            inner = list(d.iterdir())
            if inner and all(f.name == ".gbt_dir_marker" for f in inner):
                findings.append({"rule": "shell_dir", "path": d.name, "why": "空壳残骸（真身在 store/devoured/）"})
                if fix:
                    import shutil
                    shutil.rmtree(d)
                    _fix("del_shell", d.name)

    # ── 铁律 5：数据不越界（代码目录里的 .jsonl；store/ 与 archived_logs/ 是合法数据家）──
    for p in _BASE.rglob("*.jsonl"):
        parts = p.relative_to(_BASE).parts
        if parts[0] in ("store", "archived_logs"):
            continue
        findings.append({"rule": "data_outside_store", "path": str(p.relative_to(_BASE)),
                         "why": "数据文件一律进 store/"})
        if fix:
            target = _BASE / "store" / p.name
            i = 1
            while target.exists():
                target = _BASE / "store" / f"{p.stem}_{i}{p.suffix}"
                i += 1
            p.rename(target)
            _fix("mv_data_to_store", f"{p.name} -> store/")

    # ── 铁律 9：署名完整性（开发者：自由的风，禁止删除）──
    try:
        from . import signature as _sig
        for p in _sig._scan_pages():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if not _sig.has_signature(text):
                findings.append({"rule": "missing_signature", "path": str(p.relative_to(_BASE)),
                                 "why": f"页面缺开发者署名（{_sig.DEVELOPER}）——禁止删除"})
                if fix:
                    p.write_text(_sig.inject(text, p), encoding="utf-8")
                    _fix("restore_signature", str(p.relative_to(_BASE)))
    except Exception:
        pass

    elapsed = round(time.time() - t0, 3) * 1000
    verdict = "clean" if not findings else ("fixed" if (fix and fixed) else "messy")
    result = {
        "ok": True,
        "verdict": verdict,
        "findings": findings,
        "fixed": fixed,
        "cache_cleared": n_cache,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_ms": elapsed,
        "rules": "LAYOUT.md 八条铁律",
    }
    _audit("file_hygiene", {"verdict": verdict, "findings": len(findings), "fixed": len(fixed)})
    return result
