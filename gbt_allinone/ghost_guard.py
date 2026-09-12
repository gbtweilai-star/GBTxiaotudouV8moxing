"""GBT小土豆V8 · 注册表防复发检测（Ghost Guard）。

背景（Owner 口径）：旧体系"每次扫都一大堆问题"的根源是分类口径打架 +
三套镜像副本反复滋生。V8 已收口为唯一注册表，本模块负责保证它不再长回来。

检测项（V8 专属防复发——对齐旧体系三大死因）：
  1. absorbed/ 不允许回来（幽灵镜像目录）
  2. _shadowed/ _build/ 不允许回来
  3. *.deploy_bak 不允许回来
  4. 攻击类命名目录不允许回来（在 caps 类目录中出现即报警）
  5. 注册表自身：DISABLED 与 BENIGN 不得重叠
  6. 口径唯一性——包内代码不得出现私有能力清单（旧病根：三口径打架交集仅 50）
  7. 胶囊滋生率——devoured 杂交链（_x_）出现即报警（旧病根：unclassified 越裁决越滋生）
  8. 活跃区能力副本——capability.json 出现在 store 外（旧病根：三套镜像 510 副本）
  9. 胶囊降威完整性——devoured 内不得有 capability.json / auto_exec: True

用法：python -m gbt_allinone.ghost_guard   （退出码 0=干净，1=发现复发）
"""
import json
import re
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_ROOT = _BASE          # V8 独立家：根就是 gbt_allinone 自己（不再上溯混居目录）

FORBIDDEN_DIRS = [
    _ROOT / "gbt_allinone" / "absorbed",
    _ROOT / "gbt_allinone" / "absorbed" / "_shadowed",
    _ROOT / "gbt_allinone" / "absorbed" / "_build",
]

ATTACK_NAMES = {
    "keylogger", "mimikatz", "xss_tester", "sqli_tester", "phishing_engine",
    "data_hijack", "paywallbuster", "process_injector", "command_injector",
    "dir_buster", "_2captcha", "twocaptcha", "penetration_scan", "abliterator",
}

SCAN_CAP_ROOTS = ["caps"]


class _CaliberCache:
    sig = None
    result = None


_CALIBER_CACHE = _CaliberCache()   # V8 自有 caps（旧 gbt_runtime 已不随迁）


def scan() -> dict:
    findings = []

    for d in FORBIDDEN_DIRS:
        if d.exists():
            findings.append({"kind": "ghost_dir", "path": str(d),
                             "why": "已清理的幽灵/构建目录重新出现"})

    # 定点扫描（性能纪律）：.deploy_bak 历史上只出现在代码目录旁边，
    # 顶层 + 活跃代码目录两层足够覆盖；跳过 .pylibs/store/archived_logs 等大数据树
    baks = []
    scan_roots = [_ROOT]   # 独立家：只扫自己
    _skip = {"archived_logs", ".pylibs", "store", "__pycache__", "gbt_runtime",
             "node_modules", ".venv", "tentacle"}
    for root_dir in scan_roots:
        if not root_dir.exists():
            continue
        try:
            for p in root_dir.glob("*.deploy_bak"):
                baks.append(str(p))
            for child in root_dir.iterdir():
                if child.is_dir() and child.name not in _skip:
                    for p in child.glob("*.deploy_bak"):
                        baks.append(str(p))
                    for sub in child.iterdir():
                        if sub.is_dir() and sub.name not in _skip:
                            for p in sub.glob("*.deploy_bak"):
                                baks.append(str(p))
        except OSError:
            continue
    baks = baks[:20]
    for b in baks[:20]:
        findings.append({"kind": "bak_file", "path": str(b),
                         "why": ".deploy_bak 备份散件复发"})

    for root_name in SCAN_CAP_ROOTS:
        root = _ROOT / root_name
        if not root.exists():
            continue
        for child in root.iterdir():
            if child.is_dir() and child.name.lower() in ATTACK_NAMES:
                findings.append({"kind": "attack_dir", "path": str(child),
                                 "why": f"攻击类命名目录复发: {child.name}"})

    try:
        from .caps_registry import BENIGN_CAPS, DISABLED_CAPS
        overlap = set(BENIGN_CAPS) & set(DISABLED_CAPS)
        for name in overlap:
            findings.append({"kind": "registry_overlap", "item": name,
                             "why": "能力同时出现在良性与禁用名单"})
    except Exception as e:
        findings.append({"kind": "registry_error", "why": f"注册表读取失败: {e}"})

    # ── 6. 口径唯一性：私有能力清单检测（旧病根：三口径打架）──
    # 包内代码里出现"能力字典"形态（>=5 个 "domain": 键值对的大字典）且不引用 caps_registry = 私有口径
    # 指纹缓存：源码清单（路径+mtime）不变则复用结论（性能纪律——检测本身 <5ms）
    # 性能纪律：iterdir 逐层展开（~15ms）替代 rglob（Windows 下 100-600ms）；
    # 跳过 store/archived_logs/.pylibs 大数据树——口径只存在于代码区
    _SKIP_TREES = {"store", "archived_logs", ".pylibs", "__pycache__"}
    _files = []
    _stack = [_BASE]
    while _stack:
        _d = _stack.pop()
        try:
            for _e in _d.iterdir():
                if _e.is_dir():
                    if _e.name not in _SKIP_TREES:
                        _stack.append(_e)
                elif _e.suffix == ".py":
                    _files.append(_e)
        except OSError:
            continue
    _sig = str(sorted((str(p.relative_to(_BASE)), round(p.stat().st_mtime, 2)) for p in _files))
    if getattr(_CALIBER_CACHE, "sig", None) == _sig_str if False else False:
        pass
    _private = _CALIBER_CACHE.result if _CALIBER_CACHE.sig == _sig else None
    if _CALIBER_CACHE.sig != _sig:
        for p in _files:
            if not p.is_file() or p.name in ("ghost_guard.py", "caps_registry.py"):
                continue
            try:
                src = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if "caps_registry" in src:
                continue
            n_domain = len(re.findall(r'"\w+":\s*\{\s*"domain":', src))
            if n_domain >= 5:
                _private = {"kind": "private_registry", "path": str(p.relative_to(_BASE)),
                            "why": f"私有能力清单（{n_domain} 项 domain 字典）——口径必须唯一（caps_registry）"}
                break
        _CALIBER_CACHE.sig = _sig
        _CALIBER_CACHE.result = _private
    if _private:
        findings.append(_private)

    # ── 7. 胶囊滋生率：devoured 杂交链级联（旧病根：越裁决越滋生）──
    # 口径（v2 语义修正）：单级合法知识杂交（bandit × gitleaks）是吞天设计能力，不报；
    # 只有**级联滋生**（_x_ 再杂交出 _x_，或 recombined_from 里已含 _x_）才是旧病根形态。
    devoured = _BASE / "store" / "devoured"
    if devoured.exists():
        for child in devoured.iterdir():
            if not (child.is_dir() and "_x_" in child.name):
                continue
            cascading = child.name.count("_x_") >= 2
            if not cascading:
                kj = child / "knowledge.json"
                if kj.exists():
                    try:
                        parents = json.loads(kj.read_text(encoding="utf-8")).get("recombined_from", [])
                        cascading = any("_x_" in str(x) for x in parents)
                    except Exception:
                        cascading = True   # 读不出溯源 = 来路不明，从严
                else:
                    cascading = True       # 无 knowledge.json 的 _x_ 目录 = 野生滋生，从严
            if cascading:
                findings.append({"kind": "hybrid_chain", "path": f"store/devoured/{child.name}",
                                 "why": "杂交链级联滋生（_x_ 再生 _x_）——重组防膨胀已被绕过"})

    # ── 8. 活跃区能力副本：capability.json 在 store 外（旧病根：镜像 510 副本）──
    for p in _BASE.rglob("capability.json"):
        if not p.is_file() or ".pylibs" in str(p) or "archived_logs" in str(p) or "__pycache__" in str(p):
            continue
        rel = str(p.relative_to(_BASE))
        if rel.startswith("store" + "/") or rel.replace("\\", "/").startswith("store/"):
            continue   # store 内是数据区（下一步降威检查）
        findings.append({"kind": "cap_copy", "path": rel,
                         "why": "capability.json 出现在活跃代码区（镜像副本种子）"})

    # ── 9. 胶囊降威完整性：store 内不得有 capability.json / auto_exec: True ──
    if devoured.exists():
        for p in devoured.rglob("capability.json"):
            findings.append({"kind": "cap_in_devoured", "path": str(p.relative_to(_BASE)),
                             "why": "胶囊未降威（应全部为 knowledge.json 数据形态）"})
        for p in devoured.rglob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if data.get("auto_exec") is True:
                    findings.append({"kind": "capsule_armed", "path": str(p.relative_to(_BASE)),
                                     "why": "胶囊带 auto_exec: True（可执行声明——滋生种子）"})
            except Exception:
                continue

    return {"clean": not findings, "findings": findings, "checked_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")}


def main(argv=None):
    r = scan()
    import json
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
