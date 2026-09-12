"""万能插三件套 + 触手生产体检 · 马杀鸡四线全开"""
import json, subprocess, sys, time, socket

ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
CAP = ROOT + r"\caps\universal_plugin\run.py"

def run_cap(action, params, timeout=300):
    p = subprocess.run([sys.executable, CAP, action, json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=timeout)
    raw = (p.stdout or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"ok": False, "error": (raw or p.stderr or "")[:300]}

print("=" * 62)
print("生产上线马杀鸡 · 万能插三件套 + 触手体检")
print("=" * 62)

# A) 压力测试
print("\n[A] 压力测试 (5项目×4指令并发)")
ra = run_cap("run_stress", {"projects": 5, "per": 4, "timeout": 120})
stress_ok = ra.get("ok") and ra.get("pass_rate", 0) >= 95
print(f"  {'✅' if stress_ok else '❌'} pass_rate={ra.get('pass_rate')}% "
      f"total={ra.get('total')} ok={ra.get('ok_count')} elapsed={ra.get('elapsed_ms')}ms")

# B) 隔离测试
print("\n[B] 隔离测试 (3项目数据隔离)")
rb = run_cap("run_contention", {"projects": 3, "per": 3})
cont_ok = rb.get("ok") and rb.get("pass_rate", 0) >= 100
print(f"  {'✅' if cont_ok else '❌'} all_isolated={rb.get('all_isolated')} "
      f"pass_rate={rb.get('pass_rate')}%")

# C) 韧性测试
print("\n[C] 韧性测试 (异常注入)")
rc = run_cap("run_resilience", {})
print(f"  结果: {json.dumps({k: rc.get(k) for k in ['ok','pass_rate','system_stable','error_count']}, ensure_ascii=False)}")
res_ok = rc.get("ok") and rc.get("pass_rate", 0) >= 95

# D) 熔断器健康
print("\n[D] 熔断器状态")
try:
    st = json.load(open(ROOT + r"\.gbt\universal_plugin\daemon_state.json", encoding="utf-8"))
    port = st["port"]
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    s.sendall((json.dumps({"op": "breaker"}) + "\n").encode("utf-8"))
    s.settimeout(10)
    line = b""
    while True:
        ch = s.recv(1)
        if not ch or ch == b"\n":
            break
        line += ch
    s.close()
    bk = json.loads(line.decode("utf-8"))
    tripped = bk.get("breaker", {}).get("tripped", False)
    print(f"  {'✅ 未触发' if not tripped else '⚠️ 已触发: ' + str(bk.get('breaker',{}).get('reason',''))[:60]}")
    breaker_ok = not tripped
except Exception as e:
    print(f"  ⚠️ 守护进程: {e}")
    breaker_ok = False

# E) 扫描历史持久化
print("\n[E] 扫描持久化")
try:
    sc = json.load(open(ROOT + r"\.gbt\scan\scan_result.json", encoding="utf-8"))
    print(f"  ✅ 持久化在位: total={sc.get('total_caps')} persisted_at={sc.get('persisted_at')}")
    persist_ok = True
except Exception as e:
    print(f"  ❌ {e}")
    persist_ok = False

print("\n" + "=" * 62)
all_pass = stress_ok and cont_ok and res_ok and breaker_ok and persist_ok
print(f"马杀鸡第一阶段: {'✅ 全部通过' if all_pass else '⚠️ 有问题需修'}")
print(f"  压测:{'✅' if stress_ok else '❌'} 隔离:{'✅' if cont_ok else '❌'} "
      f"韧性:{'✅' if res_ok else '❌'} 熔断:{'✅' if breaker_ok else '❌'} 持久化:{'✅' if persist_ok else '❌'}")

out = {"stress": {"ok": stress_ok, "rate": ra.get("pass_rate")},
       "isolation": {"ok": cont_ok, "isolated": rb.get("all_isolated")},
       "resilience": {"ok": res_ok, "rate": rc.get("pass_rate")},
       "breaker": {"ok": breaker_ok}, "persist": {"ok": persist_ok}}
with open(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\prod-massage\stage1.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("结果已存 stage1.json")
