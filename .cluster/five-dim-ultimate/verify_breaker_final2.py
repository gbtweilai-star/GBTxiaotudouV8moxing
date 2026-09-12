import json, socket, time
# 熔断器终极验证 v2（直连新守护进程）
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
STATE = ROOT + r"\.gbt\universal_plugin\daemon_state.json"
port = json.load(open(STATE, encoding="utf-8"))["port"]
print(f"[熔断终极验证 v2 port={port}]")

def req(payload, timeout=15.0):
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

# 单并发 + 低阈值
req({"op": "reconfigure", "max_concurrent": 1, "trip_ms": 50, "resume_ms": 20, "auto_balance": False})
req({"op": "attach", "project": "bk5", "kind": "probe"})

# 积压 20 条 100ms sleep
for i in range(20):
    req({"op": "dispatch", "project": "bk5", "command": {"kind": "sleep", "ms": 100}})

time.sleep(3.0)

# 发新指令 → 应被限流
r_block = req({"op": "dispatch", "project": "bk5", "command": {"kind": "sleep", "ms": 5}})
blocked = bool(r_block.get("limited")) or not r_block.get("ok")
print(f"  积压后新指令被限流: {'YES ✅' if blocked else 'NO'} → {json.dumps(r_block, ensure_ascii=False)[:130]}")

st = req({"op": "breaker"})
print(f"  熔断状态: tripped={st.get('breaker', {}).get('tripped')}")

# 等待队列排空 + 空闲恢复（补丁逻辑：全空闲>3s 自动清窗恢复）
print("  等待恢复（15 秒）...")
time.sleep(15)
st2 = req({"op": "breaker"})
print(f"  恢复后熔断状态: tripped={st2.get('breaker', {}).get('tripped')} avg={st2.get('avg_latency_ms')}ms")

# 再发新指令 → 应放行
r_ok = req({"op": "dispatch", "project": "bk5", "command": {"kind": "sleep", "ms": 5}})
released = bool(r_ok.get("ok"))
print(f"  恢复后新指令放行: {'YES ✅' if released else 'NO'} → {json.dumps(r_ok, ensure_ascii=False)[:120]}")

verdict = blocked and released
print(f"\n  熔断器终极判定: {'✅ PASS（能拦截、能自愈恢复）' if verdict else '❌ FAIL'}")

# 清理
req({"op": "reconfigure", "max_concurrent": 8, "trip_ms": 600, "resume_ms": 250, "auto_balance": True})
req({"op": "detach", "project": "bk5"})
req({"op": "detach", "project": "warmup"})
print("[完成]")
