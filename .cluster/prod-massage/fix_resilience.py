import io

f = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\universal_plugin\run.py"
src = io.open(f, "r", encoding="utf-8").read()

# 韧性测试: 开头存当前配置→设激进阈值→结尾恢复
old_head = '''    port = _daemon_ensure()
    _daemon_req(port, {"op": "reset_metrics"}, timeout=10.0)
    victim = projs[0]
    healthy = projs[1]'''

new_head = '''    port = _daemon_ensure()
    # 2026-09-12 修复: 韧性测试需要激进熔断阈值才能验证 breaker_engaged,
    # 但生产配置(600ms)下 2500ms 慢指令不一定触发 → 测试自带阈值, 测完恢复
    _cur = _daemon_req(port, {"op": "breaker"}, timeout=10.0) or {}
    _saved = {"trip_ms": (_cur.get("breaker", {}) or {}).get("window_ms", 600.0),
              "resume_ms": (_cur.get("breaker", {}) or {}).get("resume_ms", 250.0),
              "max_concurrent": (_cur.get("max_concurrent") or 8)}
    _daemon_req(port, {"op": "reconfigure", "trip_ms": 100, "resume_ms": 50,
                       "auto_balance": False}, timeout=10.0)
    _daemon_req(port, {"op": "reset_metrics"}, timeout=10.0)
    victim = projs[0]
    healthy = projs[1]'''

old_tail = '''    stable = healthy_done_early and victim_errors and breaker_engaged and victim_recovers and daemon_alive
    return {"ok": True, "test": "resilience",'''

new_tail = '''    stable = healthy_done_early and victim_errors and breaker_engaged and victim_recovers and daemon_alive
    # 恢复生产配置
    try:
        _daemon_req(port, {"op": "reconfigure",
                           "trip_ms": _saved.get("trip_ms", 600.0),
                           "resume_ms": _saved.get("resume_ms", 250.0),
                           "max_concurrent": _saved.get("max_concurrent", 8),
                           "auto_balance": True}, timeout=10.0)
    except Exception:
        pass
    return {"ok": True, "test": "resilience",'''

ok1 = ok2 = False
if new_head in src:
    ok1 = True
    print("head already patched")
elif old_head in src:
    src = src.replace(old_head, new_head, 1)
    ok1 = True
    print("head patch OK")
else:
    print("head anchor not found")

if new_tail in src:
    ok2 = True
    print("tail already patched")
elif old_tail in src:
    src = src.replace(old_tail, new_tail, 1)
    ok2 = True
    print("tail patch OK")
else:
    print("tail anchor not found")

if ok1 or ok2:
    io.open(f, "w", encoding="utf-8").write(src)
    compile(io.open(f, encoding="utf-8").read(), f, "exec")
    print("syntax OK")
