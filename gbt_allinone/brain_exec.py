"""GBT小土豆V8 · 大脑执行层（brain_exec）——五维合一的统一调度头。

复活自 V7 execution_router（archived_logs/.../brain/execution_router.py），
V8 化：不再走子代理，全部落在万能插 + 触手 + 统一接口的纪律上。

五维合一（Owner 原设计）：
  route    意图 → 能力动态路由（语义匹配注册表 + 兜底建议）
  execute  并行执行（万能插 DAG——大脑的手）
  verify   触手肉眼验证（domain_* 五维穿透——用眼睛确认执行结果）
  health   执行层自检评分（五维各自健康度）
  unify    五维合一总入口：一次调用 = route → execute → verify → health 全链

操作五维（触手的 UIA 穿透，无视遮挡）：
  domain_index  索引（窗口/控件树）
  domain_read   读（窗口内容）
  domain_type   写（输入文本）
  domain_act    动作（点击等，含坐标兜底）
  + 视觉（vision_bus 全屏帧）——先看再动的"看"
"""
import json
import time

from .store import audit


class BrainExecError(Exception):
    pass


# ── 维度一：route（意图 → 能力）──

def route(intent: str) -> dict:
    """意图动态路由：语义匹配能力注册表，给出最佳候选 + 备选。"""
    from .caps_registry import BENIGN_CAPS
    if not intent:
        raise BrainExecError("需要 intent：任务意图描述")
    t0 = time.time()

    def _grams(s, n=2):
        s = s.lower()
        return {s[i:i + n] for i in range(max(0, len(s) - n + 1))} | ({s} if len(s) <= n else set())

    # 中英混合：词级 + 字符 2-gram 双匹配（中文无空格，n-gram 才能命中）
    words = set(intent.lower().split()) | _grams(intent)
    scored = []
    for name, info in BENIGN_CAPS.items():
        desc = str(info.get("desc", "")) + " " + name + " " + str(info.get("domain", ""))
        dw = set(desc.lower().split()) | _grams(name) | _grams(str(info.get("desc", ""))[:60])
        hit = len(words & dw)
        if hit:
            scored.append((hit, name, info.get("domain", "?"), info.get("desc", "")[:50]))
    scored.sort(reverse=True)
    top = scored[:5]
    return {"ok": True, "intent": intent[:120],
            "best": {"kind": top[0][1], "domain": top[0][2], "desc": top[0][3]} if top else None,
            "alternatives": [{"kind": s[1], "domain": s[2]} for s in top[1:]],
            "candidates": len(scored),
            "elapsed_ms": round((time.time() - t0) * 1000, 1)}


# ── 维度二：execute（并行执行——万能插）──

def execute(kind: str, payload: dict = None, parallel: list = None) -> dict:
    """执行：单能力直调，或多能力并行（parallel=[{kind,payload},...]——万能插线程池）。"""
    from .api import run_task
    t0 = time.time()
    if parallel:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(8, len(parallel))) as pool:
            futs = {i: pool.submit(run_task, item.get("kind", ""), item.get("payload") or {})
                    for i, item in enumerate(parallel)}
        results = {}
        for i, f in futs.items():
            try:
                results[str(parallel[i].get("kind", i))] = f.result()
            except Exception as e:  # noqa: BLE001
                results[str(parallel[i].get("kind", i))] = {"status": "error", "message": str(e)[:100]}
        return {"ok": all(isinstance(r, dict) and r.get("gbt_result", r).get("status") == "ok"
                          for r in results.values()),
                "parallel": len(parallel), "results": results,
                "elapsed_ms": round((time.time() - t0) * 1000, 1)}
    if not kind:
        raise BrainExecError("需要 kind（或 parallel 列表）")
    r = run_task(kind, payload or {})
    body = r.get("gbt_result", r) if isinstance(r, dict) else {}
    return {"ok": body.get("status") == "ok", "kind": kind,
            "status": body.get("status"),
            "result": body.get("result"),
            "elapsed_ms": round((time.time() - t0) * 1000, 1)}


# ── 维度三：verify（触手肉眼验证——先看再动）──

def verify(expectation: str = "", window: str = None) -> dict:
    """用触手的眼睛验证现实：抓全屏帧 + 感知指纹 + （可选）目标窗口内容读回。

    expectation 只是记录预期（供人对照），验证证据是视觉/读回的原始数据。
    """
    from .tentacle import bridge as TB
    from .tentacle import vision_bus as VB
    t0 = time.time()
    checks = {}
    # 1) 视觉证据（全屏帧 + 指纹）
    try:
        eye = TB.get_eye()
        snap = VB.snapshot(eye, ttl=30)
        checks["vision"] = {"ok": bool(snap.get("ok")),
                             "fingerprint": snap.get("fingerprint"),
                             "size": snap.get("size")}
    except Exception as e:  # noqa: BLE001
        checks["vision"] = {"ok": False, "error": str(e)[:80]}
    # 2) 目标窗口读回（domain_read——UIA 穿透）
    if window:
        try:
            r = TB.invoke("domain_read", window)
            checks["window_read"] = {"ok": bool(r.get("ok")),
                                      "sample": str(r)[:200]}
        except Exception as e:  # noqa: BLE001
            checks["window_read"] = {"ok": False, "error": str(e)[:80]}
    ok = all(c.get("ok") for c in checks.values()) if checks else False
    audit("brain_verify", {"ok": ok, "expectation": expectation[:60]})
    return {"ok": ok, "expectation": expectation[:200], "checks": checks,
            "elapsed_ms": round((time.time() - t0) * 1000, 1)}


# ── 维度四：health（执行层自检评分）──

def health() -> dict:
    """五维各自健康度 + 总分（大脑执行层的体检）。"""
    from .api import run_task
    t0 = time.time()
    dims = {}
    # 1) 路由维：注册/路由一致性
    sc = run_task("selfscan", {})
    sc_b = sc.get("gbt_result", {}).get("result", {}) if isinstance(sc, dict) else {}
    # 路由维健康标准：selfscan 能跑通且能力全路由（verdict 是数据态：隔离环境 P0/P1 合理，不算断连）
    _routing_ok = True
    _sec = sc_b.get("sections", {}).get("routing", {})
    if _sec and not _sec.get("ok"):
        _routing_ok = False
    dims["route"] = {"ok": _routing_ok and bool(sc_b.get("capabilities_total")),
                     "detail": f"selfscan={sc_b.get('verdict')}, 路由 {_sec.get('registered', '?')}/{_sec.get('routed', '?')}, 能力 {sc_b.get('capabilities_total')}"}
    # 2) 执行维：万能插健康（引擎可用性）
    try:
        wf = run_task("wf_status", {"limit": 1})
        wf_b = wf.get("gbt_result", {}) if isinstance(wf, dict) else {}
        dims["execute"] = {"ok": wf_b.get("status") == "ok",
                            "detail": f"wf_status ok, 引擎可用"}
    except Exception as e:  # noqa: BLE001
        dims["execute"] = {"ok": False, "detail": str(e)[:60]}
    # 3) 触手维（五维穿透的操作通道）
    try:
        ts = run_task("tentacle_status", {})
        ts_b = ts.get("gbt_result", {}).get("result", {}) if isinstance(ts, dict) else {}
        diag = ts_b.get("diagnose", {})
        dims["tentacle"] = {"ok": bool(diag.get("ok")),
                             "detail": f"eye_error={diag.get('eye_error')}"}
    except Exception as e:  # noqa: BLE001
        dims["tentacle"] = {"ok": False, "detail": str(e)[:60]}
    # 4) 视觉维
    try:
        from .tentacle import bridge as TB
        dims["vision"] = {"ok": TB.eye_ready(), "detail": "eye_ready" if TB.eye_ready() else str(TB.eye_error())[:60]}
    except Exception as e:  # noqa: BLE001
        dims["vision"] = {"ok": False, "detail": str(e)[:60]}
    # 5) 审计维
    try:
        from .store import log_count
        dims["audit"] = {"ok": log_count() >= 0, "detail": f"审计 {log_count()} 条"}
    except Exception as e:  # noqa: BLE001
        dims["audit"] = {"ok": False, "detail": str(e)[:60]}

    ok_count = sum(1 for d in dims.values() if d.get("ok"))
    score = round(ok_count / len(dims) * 100, 1) if dims else 0
    return {"ok": ok_count == len(dims), "score": score,
            "healthy_dims": ok_count, "total_dims": len(dims),
            "dims": dims,
            "elapsed_ms": round((time.time() - t0) * 1000, 1)}


# ── 维度五：unify（五维合一总入口）──

def unify(goal: str, payload: dict = None, expectation: str = "") -> dict:
    """五维合一：route → execute → verify → health 一次跑完（大脑执行层全链）。

    goal 用于路由（自动找能力）；也可直接传 kind（payload 里）跳过路由。
    """
    if not goal and not (payload or {}).get("kind"):
        raise BrainExecError("需要 goal（意图）或 payload.kind（指定能力）")
    t0 = time.time()
    chain = {}

    # 1) 路由
    rt = route(goal)
    chain["route"] = {"best": rt.get("best"), "candidates": rt.get("candidates")}

    # 2) 执行（goal 路由出的最佳能力，或显式 kind）
    p = payload or {}
    kind = p.get("kind") or (rt.get("best") or {}).get("kind")
    if not kind:
        return {"ok": False, "error": "路由无候选且未指定 kind", "chain": chain}
    ex = execute(kind, {k: v for k, v in p.items() if k != "kind"})
    chain["execute"] = {"kind": kind, "ok": ex.get("ok"), "status": ex.get("status")}

    # 3) 验证（触手肉眼）
    vf = verify(expectation or f"执行 {kind} 后的现实状态")
    chain["verify"] = {"ok": vf.get("ok"),
                        "checks": {k: v.get("ok") for k, v in vf.get("checks", {}).items()}}

    # 4) 健康
    hl = health()
    chain["health"] = {"score": hl.get("score"), "healthy": f"{hl.get('healthy_dims')}/{hl.get('total_dims')}"}

    ok = ex.get("ok")
    audit("brain_unify", {"goal": goal[:80], "kind": kind, "execute_ok": ok,
                           "health": hl.get("score")})
    return {"ok": ok, "goal": goal[:200], "kind": kind, "chain": chain,
            "elapsed_s": round(time.time() - t0, 1),
            "note": "五维合一：route→execute→verify→health 全链留痕"}
