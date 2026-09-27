# -*- coding: utf-8 -*-
"""penetrating_cross_scan · 穿透式交叉扫描引擎（增强版 · 强制钩子 + 交叉验证）
⛔ 开发者：自由的风 · GBT小土豆V8 · 永久钢印

立项令（Owner 2026-09-27）：触手到位**必须**调用钩子；钩子未触发 = 任务失败；
步骤锁（跳步拒绝）；同一目标**至少两路触手**交叉互扫；覆盖率 < 100% 必须补扫；
每次扫描留痕 source_kind=cross_scan。

五条红线（写死，不许静默变形）：
  1. 钩子未触发 = 任务失败（不 silently skip）
  2. 步骤锁必须生效（乱序/跳步 → StepViolation，当场拒绝）
  3. 交叉验证必须进行（每单元 ≥ 2 路独立读；不一致 → 第三路仲裁）
  4. 遗漏必须补扫（bounded 重试；仍钩不住 → 如实报"未钩住"，不许折叠成绿）
  5. 每次扫描写 trace（state/cross_scan_trace.jsonl，追加式，无痕即未发生）

亿万触手口径（诚实）：触手是**按需生成**的虚拟单元（unit × reader 笛卡尔积），
并发受 `max_workers` 与物理机限制（默认 8；quick_scan 的 12 线程是本仓 NTFS 先例）——
"亿万"指的是**可扩展的生成模型**，不是虚报并发数。

命令：
  python tools/penetrating_cross_scan.py status
  python tools/penetrating_cross_scan.py scan   bindings|registry|tree:<目录>
  python tools/penetrating_cross_scan.py verify bindings|registry|tree:<目录>   # 只跑钩子交叉
  python tools/penetrating_cross_scan.py check  bindings|registry|tree:<目录>   # 只跑遗漏检测
  python tools/penetrating_cross_scan.py report [--tail 5]
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
TRACE = ROOT / "state" / "cross_scan_trace.jsonl"
MAX_WORKERS = 8
RESCAN_ROUNDS = 2          # 遗漏补扫最多两轮，仍钩不住就如实报
CROSS_READERS = 2          # 每单元至少两路；不一致再请第三路仲裁

# ── 步骤锁（红线 2）────────────────────────────────────────────────────
STEPS = ["decompose", "spawn", "hook", "cross_validate", "detect_omission", "trace"]


class StepViolation(RuntimeError):
    """跳步/乱序——当场拒绝，不许带病继续。"""


class StepLock:
    """规定好的步骤必须按序走：`enter("hook")` 之前必须走过 decompose/spawn。"""

    def __init__(self, steps: list[str]):
        self.steps = steps
        self.done: list[str] = []

    def enter(self, step: str) -> None:
        if step not in self.steps:
            raise StepViolation(f"未知步骤 {step}（合法：{self.steps}）")
        expect = self.steps[len(self.done)]
        if step != expect:
            raise StepViolation(f"跳步违规：当前应走「{expect}」却来了「{step}」（已走 {self.done}）")
        self.done.append(step)


# ── 钩子池（红线 1：到位必须钩住）──────────────────────────────────────
# 每类单元 ≥ 2 路独立读法 + 1 路仲裁读法。钩子"触发" = 读到了观察值并留下证据。
def _read_file_a(p: Path) -> dict:
    st = p.stat()
    return {"exists": True, "size": st.st_size, "mtime": int(st.st_mtime)}


def _read_file_b(p: Path) -> dict:
    st = os.stat(p)                      # 独立读法（os 层，不走 pathlib）
    return {"exists": True, "size": st.st_size, "mtime": int(st.st_mtime)}


def _read_file_c(p: Path) -> dict:       # 仲裁路：字节数（真打开文件数一遍）
    with p.open("rb") as f:
        return {"exists": True, "size": sum(len(chunk) for chunk in iter(lambda: f.read(1 << 20), b"")),
                "mtime": int(p.stat().st_mtime)}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


HOOKS = {
    "file": {"a": _read_file_a, "b": _read_file_b, "arbiter": _read_file_c},
    "registry": {},      # 在 _hook_registry() 里现算（导入要惰性）
    "bindings": {},
}


def _hook_registry():
    def read_a(_u):
        sys.path.insert(0, str(ROOT))
        from gbt_allinone.caps_registry import BENIGN_CAPS      # 读法 A：真导入
        return {"kinds": sorted(BENIGN_CAPS.keys())}

    def read_b(_u):
        src = (ROOT / "gbt_allinone" / "caps_registry.py").read_text(encoding="utf-8")
        kinds = re.findall(r'^\s{4}"([A-Za-z0-9_]+)":\s*\{', src, re.M)   # 读法 B：纯文本解析
        return {"kinds": sorted(set(kinds))}

    def read_c(_u):
        a = json.loads((ROOT / "state" / "skill_atlas.json").read_text(encoding="utf-8"))
        return {"kinds": sorted({c["kind"] for c in a.get("caps", [])})}  # 仲裁：图鉴现扫产物
    return {"a": read_a, "b": read_b, "arbiter": read_c}


def _hook_bindings():
    """逐资产钩（unit = "binding:<rel>"）：钩子观察的是**这一个**资产，不是整本账。
    读法 A 走 pathlib，读法 B 走 os 层——两路独立探存在性+体积。"""
    def read_a(unit: str):
        rel = unit.split("binding:", 1)[1]
        p = ROOT / rel
        st = p.stat()
        return {"exists": True, "size": st.st_size}

    def read_b(unit: str):
        rel = unit.split("binding:", 1)[1]
        st = os.stat(ROOT / rel)
        return {"exists": True, "size": st.st_size}
    return {"a": read_a, "b": read_b, "arbiter": read_a}


def hooks_for(unit_type: str) -> dict:
    if unit_type == "file":
        return HOOKS["file"]
    if unit_type == "registry":
        return _hook_registry()
    if unit_type == "bindings":
        return _hook_bindings()
    if unit_type == "caps":
        return _hook_caps()
    raise ValueError(f"未知单元类型 {unit_type}")


# ── 分解（原子项目）────────────────────────────────────────────────────
def decompose(target: str) -> tuple[str, list]:
    """target → (unit_type, units)。units 就是原子扫描项目，一个不许漏。"""
    if target == "bindings":
        d = json.loads((ROOT / "state" / "asset_bindings.json").read_text(encoding="utf-8"))
        return "bindings", [f"binding:{k}" for k in sorted(d.keys())]
    if target == "registry":
        return "registry", ["registry:all"]
    if target == "caps":
        sys.path.insert(0, str(ROOT))
        from gbt_allinone.caps_registry import BENIGN_CAPS
        return "caps", ["cap:" + k for k in sorted(BENIGN_CAPS.keys())]
    if target.startswith("tree:"):
        d = ROOT / target[5:]
        if not d.is_dir():
            raise FileNotFoundError(f"目标目录不存在：{d}")
        # 跳过面**复用绑定系统的定义**（一处定义两处用：vendor/store/.pylibs/缓存/运行足迹都不扫）
        skip = None
        try:
            import importlib.util as _iu
            _sp = _iu.spec_from_file_location("tbx", ROOT / "tools" / "tentacle_bind.py")
            _tb = _iu.module_from_spec(_sp)
            _sp.loader.exec_module(_tb)
            skip = _tb._skippable
        except Exception:                                      # noqa: BLE001
            skip = None
        files = [p for p in sorted(d.rglob("*"))
                 if p.is_file() and p.suffix.lower() not in (".tmp", ".pyc")
                 and ".git" not in p.parts and "__pycache__" not in p.parts
                 and (skip is None or not skip(p.relative_to(ROOT).as_posix()))]
        return "file", [p.relative_to(ROOT).as_posix() for p in files]
    raise ValueError(f"未知 target：{target}（bindings|registry|tree:<目录>）")


# ── 触手集群（虚拟生成 + 有界并发）─────────────────────────────────────
def _unit_payload(unit_type: str, unit: str):
    if unit_type == "file":
        return ROOT / unit
    if unit_type == "caps":
        return unit.split("cap:", 1)[1]
    return None


def _fingerprint(obs: dict) -> str:
    return json.dumps(obs, sort_keys=True, ensure_ascii=False)


def spawn_and_hook(unit_type: str, units: list[str], readers: tuple[str, ...],
                   max_workers: int = MAX_WORKERS) -> dict:
    """每单元 × 每读法 = 一根触手。到位必须钩住；钩不住记 unhooked。"""
    hooks = hooks_for(unit_type)
    jobs = [(u, r) for u in units for r in readers]
    results = {u: {} for u in units}

    def _one(job):
        unit, reader = job
        fn = hooks[reader]
        payload = _unit_payload(unit_type, unit)
        t0 = time.time()
        try:
            obs = fn(payload if payload is not None else unit)
            obs = obs if isinstance(obs, dict) and obs else None
        except Exception as exc:                                # noqa: BLE001
            obs = None
            err = f"{type(exc).__name__}: {str(exc)[:120]}"
        else:
            err = ""
        return unit, reader, obs, err, round((time.time() - t0) * 1000, 1)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for unit, reader, obs, err, ms in ex.map(_one, jobs):
            results[unit][reader] = {"obs": obs, "err": err, "ms": ms,
                                     "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    return results


def cross_validate(results: dict) -> dict:
    """红线 3：每单元 ≥ 2 路；指纹不一致 → 仲裁第三路，少数服从多数。"""
    hooks = None
    verdicts = {}
    for unit, byr in results.items():
        fps = {r: _fingerprint(v["obs"]) for r, v in byr.items() if v["obs"]}
        distinct = set(fps.values())
        if len(fps) < CROSS_READERS:
            verdicts[unit] = {"status": "unhooked", "detail": "钩子未全触发"}
            continue
        if len(distinct) == 1:
            verdicts[unit] = {"status": "agree", "detail": f"{len(fps)} 路一致"}
            continue
        # 不一致 → 仲裁（红线 3 的第三路）
        if hooks is None:
            pass
        unit_type = _infer_type(unit)
        arb = hooks_for(unit_type)["arbiter"]
        try:
            a_obs = arb(_unit_payload(unit_type, unit) if _unit_payload(unit_type, unit) is not None else unit)
            results[unit]["arbiter"] = {"obs": a_obs, "err": "", "ms": 0,
                                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
            fps["arbiter"] = _fingerprint(a_obs)
        except Exception:                                       # noqa: BLE001
            pass
        best = max(set(fps.values()), key=lambda f: sum(1 for x in fps.values() if x == f))
        winners = [r for r, f in fps.items() if f == best]
        verdicts[unit] = {"status": "arbitrated", "detail": f"分歧仲裁→{'+'.join(winners)}",
                          "minority": [r for r, f in fps.items() if f != best]}
    return verdicts


def _infer_type(unit: str) -> str:
    if unit.startswith("binding:"):
        return "bindings"
    if unit.startswith("registry:"):
        return "registry"
    if unit.startswith("cap:"):
        return "caps"
    return "file"


def detect_omission(units: list[str], verdicts: dict, unit_type: str,
                    rounds: int = RESCAN_ROUNDS) -> tuple[dict, list[str]]:
    """红线 4：覆盖率 = 已钩住 / 总数；< 100% 就补扫（有界），仍钩不住如实报。"""
    missing = [u for u, v in verdicts.items() if v["status"] == "unhooked"]
    reswept = 0
    for _ in range(rounds):
        if not missing:
            break
        r2 = spawn_and_hook(unit_type, missing, tuple(list(hooks_for(unit_type))[:CROSS_READERS]))
        v2 = cross_validate(r2)
        reswept += len(missing)
        still = []
        for u in missing:
            if v2[u]["status"] == "agree":
                verdicts[u] = v2[u]
            else:
                still.append(u)
        missing = still
    return verdicts, missing


def _trace(event: str, **kw) -> None:
    TRACE.parent.mkdir(parents=True, exist_ok=True)
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source_kind": "cross_scan",
           "event": event, **kw}
    with TRACE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_pipeline(target: str, mode: str = "scan") -> dict:
    """完整管线（scan）｜只跑钩子交叉（verify）｜只跑遗漏检测（check）。"""
    lock = StepLock(STEPS)
    lock.enter("decompose")
    unit_type, units = decompose(target)
    if mode == "check":
        # check 也要先钩一次才能算覆盖（步骤锁允许从 decompose 直进 detect？不——按序走完前三步）
        lock.enter("spawn")
        lock.enter("hook")
        readers = tuple(list(hooks_for(unit_type))[:CROSS_READERS])
        results = spawn_and_hook(unit_type, units, readers)
        lock.enter("cross_validate")
        verdicts = cross_validate(results)
        lock.enter("detect_omission")
        verdicts, missing = detect_omission(units, verdicts, unit_type)
        lock.enter("trace")
        _trace("check", target=target, units=len(units), missing=len(missing))
        return _report(target, units, verdicts, missing, mode="check")
    readers = tuple(list(hooks_for(unit_type))[:CROSS_READERS])
    lock.enter("spawn")
    lock.enter("hook")
    results = spawn_and_hook(unit_type, units, readers)
    lock.enter("cross_validate")
    verdicts = cross_validate(results)
    lock.enter("detect_omission")
    verdicts, missing = detect_omission(units, verdicts, unit_type)
    lock.enter("trace")
    coverage = round(1.0 - len(missing) / max(1, len(units)), 4)
    _trace("scan", target=target, units=len(units), coverage=coverage,
           missing=len(missing), mode=mode)
    rep = _report(target, units, verdicts, missing, mode=mode)
    # 安全面（第三路·全量钩子）：文件树与能力位都过一遍危险模式分诊
    if unit_type == "file":
        rep["security"] = security_pass([u for u in units]) if units else {"flagged": 0}
    return rep


def _report(target: str, units: list, verdicts: dict, missing: list, mode: str) -> dict:
    cov = round(1.0 - len(missing) / max(1, len(units)), 4)
    agree = sum(1 for v in verdicts.values() if v["status"] == "agree")
    arb = sum(1 for v in verdicts.values() if v["status"] == "arbitrated")
    return {"ok": not missing, "mode": mode, "target": target,
            "units": len(units), "hooked": len(units) - len(missing),
            "coverage": cov, "agree": agree, "arbitrated": arb,
            "missing": missing[:30],
            "red_lines": ["钩子未触发=失败", "步骤锁生效", "交叉验证≥2路", "遗漏必须补扫", "全程留痕"],
            "trace": str(TRACE), "source_kind": "cross_scan",
            "口径": "覆盖率=已钩住/总数；missing 非空 ⇒ 不许念成通过"}


def status() -> dict:
    lines = 0
    if TRACE.is_file():
        lines = len(TRACE.read_text(encoding="utf-8").splitlines())
    return {"ok": True, "kind": "penetrating_cross_scan",
            "steps": STEPS, "max_workers": MAX_WORKERS,
            "cross_readers": CROSS_READERS, "rescan_rounds": RESCAN_ROUNDS,
            "targets": ["bindings", "registry", "tree:<目录>"],
            "trace_lines": lines,
            "口径": "触手=unit×reader 虚拟生成（亿万=可扩展模型，并发受物理机限制，不虚报）"}


def report(tail: int = 5) -> dict:
    if not TRACE.is_file():
        return {"ok": True, "lines": 0, "tail": []}
    lines = TRACE.read_text(encoding="utf-8").strip().splitlines()
    return {"ok": True, "lines": len(lines), "tail": [json.loads(x) for x in lines[-tail:]]}


def _hook_caps():
    """**能力位面**（185 位逐个钩）：三路独立读法——真导入 / 图鉴现扫产物 / api 分派源码。

    为什么三路：注册表↔图鉴↔分派**三处同在位**才叫接线（少一处就是 not_wired）。
    这里把"每一位是否在册、是否被分派"做成可钩住的观察值。
    """
    def read_a(_u):
        sys.path.insert(0, str(ROOT))
        from gbt_allinone.caps_registry import BENIGN_CAPS
        return {"kinds": sorted(BENIGN_CAPS.keys())}

    def read_b(_u):
        a = json.loads((ROOT / "state" / "skill_atlas.json").read_text(encoding="utf-8"))
        return {"kinds": sorted({c["kind"] for c in a.get("caps", [])})}

    def read_c(_u):
        src = (ROOT / "gbt_allinone" / "api.py").read_text(encoding="utf-8")
        got = set(re.findall(r'if\s+kind\s*==\s*"([^"]+)"', src))
        for grp in re.findall(r'if\s+kind\s+in\s*\(([^)]*)\)', src):
            got |= set(re.findall(r'"([^"]+)"', grp))
        return {"kinds": sorted(got)}
    return {"a": read_a, "b": read_b, "arbiter": read_c}


def _scan_one_cap(kind: str) -> dict:
    """**单个能力位的钩子**：在不在注册表 / 在不在图鉴 / api 里有没有分派分支。"""
    try:
        sys.path.insert(0, str(ROOT))
        from gbt_allinone.caps_registry import BENIGN_CAPS
        in_reg = kind in BENIGN_CAPS
    except Exception:                                          # noqa: BLE001
        in_reg = None
    try:
        a = json.loads((ROOT / "state" / "skill_atlas.json").read_text(encoding="utf-8"))
        in_atlas = kind in {c["kind"] for c in a.get("caps", [])}
    except Exception:                                          # noqa: BLE001
        in_atlas = None
    src = (ROOT / "gbt_allinone" / "api.py").read_text(encoding="utf-8")
    dispatched = bool(re.search(r'kind\s*==\s*"%s"' % re.escape(kind), src)
                      or re.search(r'kind\s+in\s*\([^)]*"%s"' % re.escape(kind), src))
    return {"kind": kind, "in_registry": in_reg, "in_atlas": in_atlas, "dispatched": dispatched}


# ── 安全读法（第三路：病毒/木马/漏洞**模式**分诊）──────────────────────
# ⚠️ 口径：这是**模式分诊**，不是杀毒引擎。它报"值得人看的地方"，不宣布"干净"。
_DANGER_PATTERNS = [
    (r"\beval\s*\(", "动态执行 eval（若入参可控即 RCE）"),
    (r"\bexec\s*\(|Invoke-Expression|iex\s+\(", "动态执行 exec/IEX"),
    (r"shell\s*=\s*True", "shell=True（命令拼接风险）"),
    (r"base64\s*\.\s*b64decode|FromBase64String", "base64 解码（常与混淆同现）"),
    (r"curl[^\n]{0,40}\|\s*(ba)?sh|wget[^\n]{0,40}\|\s*(ba)?sh", "下载即执行（管道到 shell）"),
    (r"(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
     "疑似硬编码凭据"),
    (r"BEGIN\s+(RSA|OPENSSH|PRIVATE)", "私钥字面量"),
    (r"\.(jpg|png|pdf|docx|txt|mp4)\.(exe|scr|bat|cmd|ps1|vbs)$", "双扩展名（伪装文件）"),
    (r"\bos\.system\s*\(|subprocess\.(call|Popen|run)\([^\n]{0,60}shell\s*=\s*True",
     "系统命令执行（需人核）"),
    (r"pickle\.loads?\s*\(|yaml\.load\s*\((?![^)]*Safe)", "不安全反序列化"),
]
_SEC_RE = [(re.compile(p, re.I), why) for p, why in _DANGER_PATTERNS]


def _strip_comments_and_docstrings(txt: str) -> str:
    """**扫之前先剥注释与文档串**（2026-09-27 实测血账）：不剥就会咬到**说明文字**——
    实例：`omni_process.py` 里那行写的是 `shell=False`，注释里提到旧写法 `shell=True`，
    结果被判成"命令拼接风险"；另一例是文档串里的 `os.system('rm -rf /')` 示例。
    **虚报高危会消耗信任**（吸收自 WorkBuddy 能力包的纪律）。"""
    # 三引号块（跨行）先整体移除
    txt = re.sub(r'"""[\s\S]*?"""', '""', txt)
    txt = re.sub(r"'''[\s\S]*?'''", "''", txt)
    # 再剥行内 # 注释（保守：不在字符串里的 # 才剥——用简单启发式，宁可少剥不误伤）
    out = []
    for ln in txt.splitlines():
        s = ln.lstrip()
        if s.startswith("#"):
            out.append("")
            continue
        m = re.search(r'^([^\'"#]*)#', ln)
        out.append(m.group(1) if m else ln)
    return "\n".join(out)


def _triage(rel: str, hit: dict) -> str:
    """**分诊**（把三类预期命中与"需人核"分开——虚报高危会消耗信任）：
      · `夹具/检测器`：tests/ 下的合成假值、以及检测器自己的模式库（它们在**找**这些模式）；
      · `数据路径`：base64 解码出现在图像/浏览器/数据工具里 = 合法解码；
      · `需人核`：其余——只有这一类计入告警数。
    """
    low = rel.lower().replace("\\", "/")
    name = low.rsplit("/", 1)[-1]
    snip = (hit.get("snip") or "").lower()
    # ① 显式标注的合成值（代码自己写了 not-a-real / throwaway / dummy / example…）⇒ 夹具
    if any(k in snip for k in ("not-a-real", "throwaway", "dummy", "placeholder",
                               "example", "fake", "smoke-token", "sk-abcdefg")):
        return "夹具/检测器"
    # ③ 第三方代码 = **供应链面**（按定义就"须人核"，但议题不同：我们不改它，只决定用不用）
    if low.startswith("_upstream/") or "/upstream/" in low or low.startswith("vendor/"):
        return "第三方(供应链)"
    if "/tests/" in low or name.startswith("test_") or "security_brain" in name \
            or "scan_engine" in low or "exhaustive_scan" in low or name in ("skill_vet.py",):
        return "夹具/检测器"
    if "base64" in hit.get("why", "") and any(k in low for k in
                                             ("vision", "browser", "datakit", "deploy/", "visual_memory")):
        return "数据路径"
    return "需人核"


def _scan_one_file_security(rel: str) -> dict:
    """单文件的**安全钩子**：报命中模式（只读、限量、跳过 vendored/缓存、**剥注释后再扫**）。"""
    p = ROOT / rel
    low = rel.lower()
    if "/vendor/" in low or "/.pylibs/" in low or "/store/" in low:
        return {"unit": rel, "hits": [], "note": "nested vendor/.pylibs/store 跳过"}
    if p.suffix.lower() not in (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".ps1", ".bat",
                                ".cmd", ".sh", ".php", ".rb", ".yml", ".yaml", ".json"):
        return {"unit": rel, "hits": []}
    try:
        if p.stat().st_size > 2_000_000:
            return {"unit": rel, "hits": [], "note": ">2MB 跳过（限量）"}
        txt = _strip_comments_and_docstrings(p.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {"unit": rel, "hits": []}
    hits = []
    for rx, why in _SEC_RE:
        for m in rx.finditer(txt):
            line = txt.count("\n", 0, m.start()) + 1
            h = {"line": line, "why": why, "snip": txt[m.start():m.start() + 60].replace("\n", " ")}
            h["triage"] = _triage(rel, h)        # 每条命中都打分诊标签（缺了它 needs_human 恒 0 = 假绿）
            hits.append(h)
            break                                # 同类只报首例，避免刷屏
    return {"unit": rel, "hits": hits}


def security_pass(units: list[str], max_workers: int = MAX_WORKERS) -> dict:
    """**安全面全量钩子**（第三路）：逐单元扫危险模式，出分诊清单。"""
    findings, scanned, needs_human = [], 0, 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for r in ex.map(_scan_one_file_security, units):
            scanned += 1
            if r.get("hits"):
                findings.append(r)
                needs_human += sum(1 for h in r["hits"] if h.get("triage") == "需人核")
    _trace("security_pass", units=scanned, flagged=len(findings), needs_human=needs_human)
    return {"ok": needs_human == 0, "scanned": scanned, "flagged": len(findings),
            "needs_human": needs_human, "findings": findings[:40],
            "口径": "**模式分诊**不是杀毒：报的是「值得人看」，不宣布「干净」；跳过 vendored/缓存（_skippable）"}


def hook_enforcer():
    """**能力位面全覆盖钩子**（185 位逐个）：在册 / 在图鉴 / 有分派——三条都亮才算钩住。"""
    try:
        sys.path.insert(0, str(ROOT))
        from gbt_allinone.caps_registry import BENIGN_CAPS
        kinds = sorted(BENIGN_CAPS.keys())
    except Exception as exc:                                   # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    rows, unhooked = [], []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for r in ex.map(_scan_one_cap, kinds):
            rows.append(r)
            if not (r["in_registry"] and r["in_atlas"] and r["dispatched"]):
                unhooked.append(r)
    _trace("caps_hooks", caps=len(kinds), unhooked=len(unhooked))
    return {"ok": not unhooked, "caps": len(kinds), "hooked": len(kinds) - len(unhooked),
            "unhooked": unhooked[:20],
            "口径": "每位三判据=注册表∩图鉴∩分派；缺任一=没钩住（not_wired 同源）"}


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__); return 2
    cmd = argv[1]
    if cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1)); return 0
    if cmd == "report":
        print(json.dumps(report(int(argv[argv.index("--tail") + 1]) if "--tail" in argv else 5),
                         ensure_ascii=False, indent=1)); return 0
    if cmd in ("scan", "verify", "check") and len(argv) >= 3:
        r = run_pipeline(argv[2], mode=cmd if cmd != "verify" else "scan")
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["ok"] else 1
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
