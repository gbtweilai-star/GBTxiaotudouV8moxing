import json, socket, subprocess, sys, time
# 熔断器验证 v3：直连守护进程 socket，绕开每次冷启动 run_cap 的延迟稀释问题
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
STATE = ROOT + r"\.gbt\universal_plugin\daemon_state.json"

def req(port, payload, timeout=15.0):
    s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    try:
        s.settimeout(timeout)
        s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        line = b""
        while True:
            ch = s.recv(1)
            if not ch:
                break
            line += ch
            if ch == b"\n":
                break
        return json.loads(line.decode("utf-8"))
    finally:
        s.close()

# 读取守护进程端口
st = json.load(open(STATE, encoding="utf-8"))
port = st["port"]
print(f"[直连守护进程 port={port}]")
print(f"  ping: {req(port, {'op': 'ping'})}")

# 重新配置为极低阈值 + 单并发
print(req(port, {"op": "reconfigure", "max_concurrent": 1, "trip_ms": 50, "resume_ms": 20, "auto_balance": False}))
print(f"  attach: {req(port, {'op': 'attach', 'project': 'bk3', 'kind': 'probe'})}")

# 快速连发 30 条 sleep(100ms)，单并发必然排队 → 调度等待延迟飙升
for i in range(30):
    req(port, {"op": "dispatch", "project": "bk3", "command": {"kind": "sleep", "ms": 100}})

time.sleep(0.8)
r = req(port, {"op": "breaker"})
print(f"  熔断器: {json.dumps(r.get('breaker', {}), ensure_ascii=False)}")
print(f"  平均调度延迟: {r.get('avg_latency_ms')}ms | 并发: {r.get('n_current')}")
tripped = bool(r.get("breaker", {}).get("tripped"))
print(f"  熔断触发: {'YES ✅' if tripped else 'NO'}")

if tripped:
    r2 = req(port, {"op": "dispatch", "project": "bk3", "command": {"kind": "sleep", "ms": 5}})
    print(f"  熔断期间限流: {'YES ✅' if (r2.get('limited') or not r2.get('ok')) else 'NO'} → {json.dumps(r2, ensure_ascii=False)[:120]}")
    print("  等待恢复...")
    time.sleep(8)
    r3 = req(port, {"op": "breaker"})
    print(f"  恢复后: tripped={r3.get('breaker', {}).get('tripped')} avg={r3.get('avg_latency_ms')}ms")
    r4 = req(port, {"op": "dispatch", "project": "bk3", "command": {"kind": "sleep", "ms": 5}})
    print(f"  恢复后可分发: {'YES ✅' if r4.get('ok') else 'NO'}")
else:
    # 输出 dashboard 帮助诊断
    d = req(port, {"op": "dashboard"})
    print(f"  dashboard: {json.dumps(d, ensure_ascii=False)[:400]}")

# 清理
req(port, {"op": "reconfigure", "max_concurrent": 8, "trip_ms": 600, "resume_ms": 250, "auto_balance": True})
req(port, {"op": "detach", "project": "bk3"})
print("[完成]")
