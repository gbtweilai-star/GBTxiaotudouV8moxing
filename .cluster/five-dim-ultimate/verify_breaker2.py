import json, subprocess, sys, time
# 熔断器深度验证 v2：连发高频指令 + 快速查询，捕捉调度延迟并观察熔断行为
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
cap = ROOT + r"\caps\universal_plugin\run.py"

def run_cap(action, params, timeout=120):
    p = subprocess.run([sys.executable, cap, action, json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=timeout)
    raw = (p.stdout or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"ok": False, "error": (raw or p.stderr or "")[:300]}

print("[熔断器深度验证 v2]")
run_cap("reconfigure", {"max_concurrent": 1, "trip_ms": 50, "resume_ms": 20, "auto_balance": False})
run_cap("attach", {"project": "bk2", "kind": "probe"})
# 并发=1，连续塞 20 条 150ms sleep，队列必然积压，调度等待延迟飙升
for i in range(20):
    run_cap("dispatch", {"project": "bk2", "command": {"kind": "sleep", "ms": 150}})
time.sleep(0.5)
r = run_cap("breaker", {})
print(f"  熔断器: {json.dumps(r.get('breaker', {}), ensure_ascii=False)}")
print(f"  平均调度延迟: {r.get('avg_latency_ms')}ms | 并发上限: {r.get('n_current')}")
tripped = bool(r.get("breaker", {}).get("tripped"))
print(f"  熔断触发: {'YES ✅' if tripped else 'NO'}")
if tripped:
    # 验证限流：熔断期间新指令应被拒
    r2 = run_cap("dispatch", {"project": "bk2", "command": {"kind": "sleep", "ms": 5}})
    limited = bool(r2.get("limited")) or (not r2.get("ok"))
    print(f"  熔断期间新指令被限流: {'YES ✅' if limited else 'NO'}")
    # 等待恢复窗口
    print("  等待熔断恢复...")
    time.sleep(6)
    r3 = run_cap("breaker", {})
    print(f"  恢复后状态: tripped={r3.get('breaker', {}).get('tripped')} avg={r3.get('avg_latency_ms')}ms")
    r4 = run_cap("dispatch", {"project": "bk2", "command": {"kind": "sleep", "ms": 5}})
    print(f"  恢复后新指令可分发: {'YES ✅' if r4.get('ok') else 'NO'}")
# 清理
run_cap("reconfigure", {"max_concurrent": 8, "trip_ms": 600, "resume_ms": 250, "auto_balance": True})
run_cap("detach", {"project": "bk2"})
print("[验证完成]")
