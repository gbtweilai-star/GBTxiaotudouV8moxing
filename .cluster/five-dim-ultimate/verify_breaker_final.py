import json, socket, subprocess, sys, time
# 熔断器终极验证：先积压队列 → 再发新指令 → 应被限流 → 等恢复 → 应放行
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
STATE = ROOT + r"\.gbt\universal_plugin\daemon_state.json"
CAP = ROOT + r"\caps\universal_plugin\run.py"

# 先通过 run.py 触发守护进程（确保 daemon 存活并读取新端口），带重试
for _ in range(5):
    subprocess.run([sys.executable, CAP, "status"], capture_output=True, cwd=ROOT, timeout=60)
    time.sleep(1.0)
    try:
        _st = json.load(open(STATE, encoding="utf-8"))
        _s = socket.create_connection(("127.0.0.1", _st["port"]), timeout=3)
        _s.close()
        break
    except Exception:
        continue

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

port = json.load(open(STATE, encoding="utf-8"))["port"]
print(f"[熔断器终极验证 port={port}]")

# 单并发 + 低阈值
req(port, {"op": "reconfigure", "max_concurrent": 1, "trip_ms": 50, "resume_ms": 20, "auto_balance": False})
req(port, {"op": "attach", "project": "bk4", "kind": "probe"})

# 第一步：塞 20 条 100ms sleep，让队列积压
for i in range(20):
    req(port, {"op": "dispatch", "project": "bk4", "command": {"kind": "sleep", "ms": 100}})

# 第二步：等队列积压产生真实调度延迟（约 3 秒后队尾等待已超 50ms）
time.sleep(3.0)

# 第三步：发新指令 → 熔断应拦截
r_block = req(port, {"op": "dispatch", "project": "bk4", "command": {"kind": "sleep", "ms": 5}})
blocked = bool(r_block.get("limited")) or not r_block.get("ok")
print(f"  积压后新指令被限流: {'YES ✅' if blocked else 'NO'} → {json.dumps(r_block, ensure_ascii=False)[:150]}")

st = req(port, {"op": "breaker"})
print(f"  熔断状态: {json.dumps(st.get('breaker', {}), ensure_ascii=False)}")

# 第四步：等待队列排空 + 恢复窗口
print("  等待恢复（12 秒）...")
time.sleep(12)
st2 = req(port, {"op": "breaker"})
print(f"  恢复后熔断状态: tripped={st2.get('breaker', {}).get('tripped')} avg={st2.get('avg_latency_ms')}ms")

# 第五步：再发新指令 → 应放行
r_ok = req(port, {"op": "dispatch", "project": "bk4", "command": {"kind": "sleep", "ms": 5}})
print(f"  恢复后新指令放行: {'YES ✅' if r_ok.get('ok') else 'NO'} → {json.dumps(r_ok, ensure_ascii=False)[:120]}")

verdict = blocked and r_ok.get("ok")
print(f"\n  熔断器终极判定: {'✅ PASS（能拦截、能恢复）' if verdict else '❌ FAIL'}")

# 清理
req(port, {"op": "reconfigure", "max_concurrent": 8, "trip_ms": 600, "resume_ms": 250, "auto_balance": True})
req(port, {"op": "detach", "project": "bk4"})
print("[完成]")
