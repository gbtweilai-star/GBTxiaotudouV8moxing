"""韧性测试逐环节诊断"""
import json, socket, time, subprocess, sys

ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
st = json.load(open(ROOT + r"\.gbt\universal_plugin\daemon_state.json", encoding="utf-8"))
port = st["port"]

def req(payload, timeout=15.0):
    s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    try:
        s.settimeout(timeout)
        s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        line = b""
        while True:
            ch = s.recv(1)
            if not ch or ch == b"\n":
                break
            line += ch
        return json.loads(line.decode("utf-8"))
    finally:
        s.close()

print("逐环节诊断:")
# 1) 重置
print("1) reset:", req({"op": "reset_metrics"}).get("ok"))

# 2) 设置激进阈值
r_cfg = req({"op": "reconfigure", "trip_ms": 100, "resume_ms": 50, "auto_balance": False})
print(f"2) reconfigure trip=100: {json.dumps(r_cfg, ensure_ascii=False)[:150]}")

# 3) attach
for pr in ["diag_a", "diag_b"]:
    req({"op": "attach", "project": pr, "kind": "resilience"})
print("3) attach diag_a/diag_b: OK")

# 4) 失败指令
r_bad = req({"op": "dispatch", "project": "diag_a", "command": {
    "kind": "cap", "cap": "no_such_cap_xyz", "action": "status"}})
print(f"4) 失败指令: ok={r_bad.get('ok')} err={str(r_bad.get('error',''))[:60]}")

# 5) 慢指令
t0 = time.time()
r_slow = req({"op": "dispatch", "project": "diag_a", "command": {"kind": "sleep", "ms": 2500}})
print(f"5) 慢指令(2500ms): ok={r_slow.get('ok')} (耗时 {time.time()-t0:.1f}s)")

# 6) 健康项目正常指令
r_ok = req({"op": "dispatch", "project": "diag_b", "command": {
    "kind": "cap", "cap": "universal_plugin", "action": "extract_copy", "params": {"topic": "diag_b"}}})
print(f"6) 健康指令: ok={r_ok.get('ok')}")

time.sleep(1.2)
st_h = req({"op": "status", "project": "diag_b"})
h_done = any(v.get("status") == "done" for v in st_h.get("results", {}).values())
print(f"6b) 健康项目提前完成: {h_done}")

time.sleep(2.6)
# 7) 熔断验证: 高延迟窗口期新分发应被限流
r_lim = req({"op": "dispatch", "project": "diag_a", "command": {"kind": "sleep", "ms": 5}})
print(f"7) 熔断期新指令: limited={r_lim.get('limited')} ok={r_lim.get('ok')} err={str(r_lim.get('error',''))[:70]}")

# 8) 等待全部完成
for _ in range(30):
    st_all = req({"op": "dashboard"})
    if st_all.get("idle", True):
        break
    time.sleep(1)
st_v = req({"op": "status", "project": "diag_a"})
print(f"8) victim errors: {st_v.get('errors')}")

# 9) 恢复
req({"op": "reset_metrics"})
time.sleep(0.5)
r_after = req({"op": "dispatch", "project": "diag_a", "command": {"kind": "sleep", "ms": 10}})
print(f"9) 恢复后指令: ok={r_after.get('ok')}")

# 10) 熔断器状态
bk = req({"op": "breaker"})
print(f"10) breaker: {json.dumps(bk.get('breaker', {}), ensure_ascii=False)[:120]}")

# 恢复生产配置
req({"op": "reconfigure", "trip_ms": 600, "resume_ms": 250, "auto_balance": True})
print("\n生产配置已恢复 (600/250/auto)")
