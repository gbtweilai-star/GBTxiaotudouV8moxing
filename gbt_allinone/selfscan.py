"""GBT小土豆V8 · 框架体检层（眼睛 + 声带）。

Owner 定调（2026-09-11）：哪里有毛病、断连、丢失，框架必须第一时间知道、
追踪根源、给出修复——不能手臂掉了眼睛看不见，连个响都没有。

五个体检维度：
  1. 路由完整性：BENIGN_CAPS 注册的每项能力在 api.py 必须有真实分派路径
     （静态提取 == / in (...) / startswith 三种路由形态，注册与路由双向对账）
  2. 模块健康：全部核心模块 import 必须成功（含 src.core、子包）
  3. 存储健康：store 下全部 JSON 必须可解析；关键目录必须存在
  4. 审计异常：近期 error/denied/svc_down/longrun_failed/stalled/pipeline_blocked
     聚合计数 + 按能力分组的根源线索
  5. 桩缺口：needs_dependency 的能力如实清点（不算病，算缺口）

严重度：P0 = 断连/损坏（必须修）；P1 = 异常在发生（要看）；P2 = 缺口（要知道）。
autofix=True 时只做安全修复：缺目录补建、损坏 JSON 备份后重置；其余只报不动。
"""
import importlib
import json
import re
import time
import sys
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_ROOT = _BASE          # V8 独立家：根就是 gbt_allinone 自己

_MODULES = [
    "api", "app", "cli", "engine", "ghost_guard", "longrun",
    "pipeline", "quant_tech", "schedule", "services", "soul", "store",
    "tactics",
    "integration.auth", "integration.platform_client",
    "integration.smoke_test",
    "recon.scanner", "recon.guard",
    "hygiene", "signature", "transfer", "auth_gate", "mirror_space", "qiankun", "think_loop", "brain_exec", "inventory", "cross_scan", "root_fix",
    # 补齐验收观察项：caps_registry 直接入列（不再只靠 routing 间接覆盖）
    "caps_registry",
    # 集成收口：第九批新模块全部入列（黑客大脑/LLM网关/自主编排/真实性审计/触手）
    "security.security_brain", "security.abl_gateway",
    "llm.bridge", "truth_scan", "autopilot", "tentacle.bridge",
]

# 资金模块（纯全能 AI 框架不随库分发）：存在则检查，不存在不算病
_MONEY_MODULES = [
    "notify", "export_statement", "loop",
    "ledger.core", "ledger.pool",
    "wallet.hd", "wallet.rpc", "wallet.consolidate",
    "adapters.wallet_adapter",
    "bridge.deposit_bridge",
]

# 适配器/桥目录为空目录时 Python 不导入，需目录探测
_PROBE_DIRS = ["adapters", "bridge"]

_ANOMALY_EVENTS = ("error", "svc_down", "longrun_failed",
                   "longrun_stalled", "pipeline_blocked")
# denied 是护栏正常拦截（测试/演示触发为主），单独统计不算病
_RESERVED_SERVICES = {"v8_isolated"}  # 预留端口，未启动属预期，不算掉线


_RECOVERED_CACHE = {}  # name -> (结论, 时刻)——热路径防抖：同 kind 30s 内只探一次


def _service_recovered(name: str) -> bool:
    """svc_down 的服务当前是否已探活在线（历史掉线已恢复）。

    TTL 缓存 30s：窗口内几十条同 kind 的 svc_down 只真实探活一次（性能基线守卫——
    每次 0.6s 探活 × 41 条曾把 selfscan 热路径顶到 600ms）。quiet=True 纯探活不落审计。
    """
    now = time.time()
    hit = _RECOVERED_CACHE.get(name)
    if hit and now - hit[1] < 30:
        return hit[0]
    try:
        from . import services
        snap = services.inspect(str(name), timeout=0.15, quiet=True)
        up = bool(snap.get("services", {}).get(str(name), {}).get("up"))
    except Exception:
        up = False
    _RECOVERED_CACHE[name] = (up, now)
    return up


def _routed_kinds():
    """静态提取 api.py 里全部真实分派路径。"""
    src = (_BASE / "api.py").read_text(encoding="utf-8")
    kinds = set(re.findall(r'kind == "(\w+)"', src))
    for tup in re.findall(r'if kind in \((.*?)\)', src, re.DOTALL):
        kinds.update(re.findall(r'"(\w+)"', tup))
    # 变量形式元组：_XXX_KINDS = (...) / _MONEY_KINDS = (...) ——赋值后 `if kind in _XXX`
    # （降级占位路由也算有效路由：能力有明确的分派路径与响应语义）
    for var, tup in re.findall(r'(_\w*KINDS\w*)\s*=\s*\((.*?)\)', src, re.DOTALL):
        if f"if kind in {var}" in src:
            kinds.update(re.findall(r'"(\w+)"', tup))
    prefixes = set(re.findall(r'kind\.startswith\("(\w+)"\)', src))
    # _STUB_DEPS 桩家族（如实缺口，不算断连）
    stubs = set()
    for k, v in re.findall(r'"(\w+)":\s*"([^"]*)"', src):
        if v.startswith("需") and k not in ("note",):
            stubs.add(k)
    return kinds, prefixes, stubs


def check_routing():
    from .caps_registry import BENIGN_CAPS
    routed, prefixes, stubs = _routed_kinds()
    registered = set(BENIGN_CAPS)

    def _covered(k):
        return k in routed or k in stubs or any(k.startswith(p) for p in prefixes)

    unrouted = sorted(k for k in registered if not _covered(k))
    ghost_routes = sorted(k for k in (routed | stubs) if k not in registered)
    return {"registered": len(registered), "routed": len(routed | stubs),
            "unrouted": unrouted, "ghost_routes": ghost_routes,
            "ok": not unrouted and not ghost_routes}


_MODULE_CACHE = {"result": None}


def check_modules():
    """模块健康检查（进程内缓存：导入结果不会中途变化，缓存后 0ms）。"""
    if _MODULE_CACHE["result"] is not None:
        r = dict(_MODULE_CACHE["result"])
        r["cached"] = True
        return r
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    bad = []
    for m in _MODULES:
        full = m if m.startswith("gbt_allinone") else "gbt_allinone." + m
        try:
            importlib.import_module(full)
        except Exception as e:  # noqa: BLE001
            bad.append({"module": full, "error": f"{type(e).__name__}: {e}"[:160]})
    # 资金模块：存在则检查，不存在不算病（纯全能 AI 框架不随库分发）
    money_checked = 0
    for m in _MONEY_MODULES:
        full = m if m.startswith("gbt_allinone") else "gbt_allinone." + m
        try:
            mod = importlib.import_module(full)
        except ImportError:
            continue  # 未分发→跳过，不算失败
        except Exception as e:  # noqa: BLE001
            bad.append({"module": full, "error": f"{type(e).__name__}: {e}"[:160]})
            money_checked += 1
            continue
        money_checked += 1
    _MODULE_CACHE["result"] = {"checked": len(_MODULES) + money_checked, "failed": bad, "ok": not bad}
    return dict(_MODULE_CACHE["result"])


def check_store():
    store = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR
    need_dirs = ["pipeline/mirror", "pipeline/gate", "pipeline/quarantine",
                 "pipeline/production", "pipeline/records", "wf_runs"]
    missing = [d for d in need_dirs if not (store / d).exists()]
    corrupted = []
    n = 0
    if store.exists():
        # 性能纪律：全量列出 + 分层检查——活跃工作文件（顶层）全查，
        # 历史记录目录（wf_runs/pipeline/records）每目录抽前 50 个
        all_json = list(store.rglob("*.json"))
        n = len(all_json)
        active = [jf for jf in store.glob("*.json")]
        sampled = [jf for jf in all_json if jf not in active][:150]
        for jf in active + sampled:
            try:
                json.loads(jf.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                corrupted.append({"file": str(jf.relative_to(_BASE)),
                                  "error": str(e)[:100]})
    return {"json_files": n, "missing_dirs": missing,
            "corrupted": corrupted, "ok": not missing and not corrupted}


def check_audit(last=500):
    """审计体检（信号分级版）。

    三级信号：
      runtime  运行时故障——真正要追的病（默认算 anomaly）
      guard    护栏拦截——内网/安全策略/门禁在正常工作（不算病，如实列出）
      trace    测试足迹——能力不存在/参数缺失等测试与联调残留（不算病，可清）
    """
    from .store import query_log
    rows = query_log(limit=last)

    # 恢复证据索引：窗口内每 kind 的成功调用（audit('ok')）——error 之后有 ok = 已恢复。
    # 性能：单遍预扫描同时完成轻字段归一（rows 行已是 dict，避免二次全量解析）。
    ok_kinds = set()
    for _r in rows:
        if _r.get("event") == "ok":
            _m = _r.get("meta") or {}
            _k = _m.get("kind") or _m.get("services") or _m.get("name")
            if isinstance(_k, str):
                ok_kinds.add(_k)
            elif isinstance(_k, list):
                ok_kinds.update([x for x in _k if isinstance(x, str)])
    by_event = {}
    by_kind = {}
    by_signal = {"runtime": 0, "guard": 0, "trace": 0, "recovered": 0}
    samples = []
    for r in rows:
        ev = r.get("event", "")
        if ev not in _ANOMALY_EVENTS:
            continue
        meta = r.get("meta") or {}
        kind = meta.get("kind") or meta.get("task_id") or meta.get("name") or meta.get("services", ["?"])
        if isinstance(kind, list):
            kind = [k for k in kind if k not in _RESERVED_SERVICES] or None
        if kind is None:
            continue  # 纯预留端口足迹
        key = kind if isinstance(kind, str) else ",".join(map(str, kind))
        reason = str(meta.get("reason", ""))

        # 信号分级（v2 源头分类版——判例法退役）：
        # user_error 事件天然不算 anomaly（不在 _ANOMALY_EVENTS 里），
        # error 事件现在只剩真故障——唯一的判例只剩护栏与不可改名的历史足迹。
        if meta.get("probe"):
            sig = "trace"     # 探针/观察者足迹（源头标记）：不是现行故障——最优先判定
        elif ("内网" in reason or "安全策略" in reason
                or (ev == "pipeline_blocked" and str(key).startswith("t-"))):
            sig = "guard"
        elif key.startswith("T00"):   # 历史长程测试任务（审计轮转前的旧记录，不可改名）
            sig = "trace"
        elif ev == "svc_down" and _service_recovered(key):
            sig = "recovered"  # 历史掉线且当前已探活在线：如实报已恢复，不算现行故障
        elif ev == "svc_down":
            # 多服务合并行：逐服务探活，全部在线则视为已恢复（修复验收提出的盲点）
            names = [n.strip() for n in str(key).split(",") if n.strip()]
            if names and all(_service_recovered(n) for n in names):
                sig = "recovered"
            else:
                sig = "runtime"
        elif ev == "error" and key in ok_kinds:
            sig = "recovered"  # 故障后同能力已有成功调用：如实报已恢复，不算现行故障
        else:
            sig = "runtime"

        by_event[ev] = by_event.get(ev, 0) + 1
        by_signal[sig] = by_signal.get(sig, 0) + 1
        by_kind.setdefault(key, {"runtime": 0, "guard": 0, "trace": 0, "recovered": 0})[sig] += 1
        if sig == "runtime" and len(samples) < 5:
            samples.append({"event": ev, "kind": key, "reason": reason[:120],
                            "at": r.get("iso")})

    total = sum(by_event.values())
    runtime = by_signal["runtime"]
    return {"window": last, "anomalies": total, "runtime_faults": runtime,
            "by_event": by_event, "by_signal": by_signal,
            "errors_by_kind": by_kind, "recent_runtime": samples,
            "ok": runtime == 0}


def alerts(last=500):
    """声带：近期异常摘要 + 根源线索（分级版）。"""
    a = check_audit(last)
    if a["anomalies"] == 0:
        return {"quiet": True, "anomalies": 0,
                "note": "窗口期内无异常事件"}
    top = sorted(a["errors_by_kind"].items(),
                 key=lambda x: -(x[1].get("runtime", 0)) )[:5]
    return {"quiet": a["runtime_faults"] == 0,
            "anomalies": a["anomalies"],
            "runtime_faults": a["runtime_faults"],
            "by_signal": a["by_signal"],
            "by_event": a["by_event"],
            "top_offenders": [{"capability": k, "runtime": v.get("runtime", 0),
                                "guard": v.get("guard", 0), "trace": v.get("trace", 0)}
                               for k, v in top],
            "note": "runtime=要追的病；guard=护栏正常工作；trace=测试足迹；recovered=历史掉线已恢复"}


def _autofix(sec_store):
    """安全自动修复：补目录、损坏 JSON 备份后重置。返回修复清单。"""
    fixed = []
    store = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR
    for d in sec_store.get("missing_dirs", []):
        (store / d).mkdir(parents=True, exist_ok=True)
        fixed.append(f"补建目录 store/{d}")
    for c in sec_store.get("corrupted", []):
        f = _BASE / c["file"]
        bak = f.with_suffix(f.suffix + f".corrupt-{int(time.time())}")
        f.rename(bak)
        default = {"next_id": 1, "tasks": []} if f.name == "tasks.json" else {}
        f.write_text(json.dumps(default, ensure_ascii=False), encoding="utf-8")
        fixed.append(f"损坏 JSON 已备份重置: {c['file']} -> {bak.name}")
    return fixed


def scan(autofix: bool = False) -> dict:
    routing = check_routing()
    modules = check_modules()
    store_sec = check_store()
    audit_sec = check_audit()
    stubs = sorted(_routed_kinds()[2])

    findings = []
    if not routing["ok"]:
        findings.append("P0 路由断连: " +
                        (f"未路由能力 {routing['unrouted']} " if routing["unrouted"] else "") +
                        (f"幽灵路由 {routing['ghost_routes']}" if routing["ghost_routes"] else ""))
    if not modules["ok"]:
        findings.append(f"P0 模块导入失败: {[b['module'] for b in modules['failed']]}")
    if not store_sec["ok"]:
        findings.append(f"P0/P1 存储异常: 缺目录{store_sec['missing_dirs']} 损坏{len(store_sec['corrupted'])}个")
    if not audit_sec["ok"]:
        findings.append(f"P1 运行时故障 {audit_sec['runtime_faults']} 起: "
                        f"{ {k: v['runtime'] for k, v in audit_sec['errors_by_kind'].items() if v['runtime'] > 0} }")

    verdict = "clean"
    if any(f.startswith("P1") for f in findings):
        verdict = "P1"
    if any(f.startswith("P0") for f in findings):
        verdict = "P0"

    fixed = _autofix(store_sec) if autofix else []
    if fixed:
        store_sec = check_store()  # 复验
        findings.append("已自动修复: " + "; ".join(fixed))

    return {
        "verdict": verdict,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "findings": findings,
        "sections": {
            "routing": routing,
            "modules": modules,
            "store": store_sec,
            "audit": audit_sec,
            "stub_gaps": stubs,
        },
        "capabilities_total": routing["registered"],
        "note": "P0=断连/损坏必须修；P1=异常在发生；clean=五维全过（桩缺口如实列出不算病）",
    }
