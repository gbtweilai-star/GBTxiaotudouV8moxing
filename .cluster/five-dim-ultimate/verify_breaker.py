import json, subprocess, sys, time
# 熔断器本体验证：手动制造高延迟场景，确认 trip/resume 逻辑可用
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

print("[熔断器本体验证]")
# 降低熔断阈值到 1ms，让任何调度延迟都能触发
r = run_cap("reconfigure", {"max_concurrent": 4, "trip_ms": 1, "resume_ms": 0.5, "auto_balance": False})
print(f"  重配置: ok={r.get('ok')} trip_ms={r.get('trip_ms')} resume_ms={r.get('resume_ms')}")

# attach 项目
r = run_cap("attach", {"project": "breaker_probe", "kind": "probe"})
print(f"  接入项目: ok={r.get('ok')}")

# 快速连发多条 sleep 指令制造调度排队延迟
for i in range(12):
    run_cap("dispatch", {"project": "breaker_probe", "command": {"kind": "sleep", "ms": 150}})
time.sleep(1.0)

# 查看熔断器状态
r = run_cap("breaker", {})
print(f"  熔断器: {json.dumps(r.get('breaker', {}), ensure_ascii=False)}")
print(f"  平均延迟: {r.get('avg_latency_ms')}ms | 当前并发: {r.get('n_current')}")

tripped = bool(r.get("breaker", {}).get("tripped"))
print(f"  熔断触发: {'YES' if tripped else 'NO'}")

# 恢复默认配置
r = run_cap("reconfigure", {"max_concurrent": 8, "trip_ms": 600, "resume_ms": 250, "auto_balance": True})
print(f"  恢复默认: ok={r.get('ok')}")

# 分离项目
run_cap("detach", {"project": "breaker_probe"})
print("[验证完成]")
