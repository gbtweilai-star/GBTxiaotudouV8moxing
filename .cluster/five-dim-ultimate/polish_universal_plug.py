import json, subprocess, sys, time
# 五维合一系统·万 能插打磨脚本
# 1) 万能插 stress 测试  2) 语音流利度打磨  3) 自控循环验证
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
cap = ROOT + r"\caps\universal_plugin\run.py"
env_io = "utf-8"

def run_cap(action, params, timeout=120):
    p = subprocess.run([sys.executable, cap, action, json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=timeout)
    raw = (p.stdout or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"ok": False, "error": (raw or p.stderr or "")[:300]}

print("=" * 56)
print("五维合一系统 高强度打磨 · 万能插通道")
print("=" * 56)

# ---- 1) 压力测试: 5 项目并发 x 4 指令 ----
print("\n[阶段 1] 万能插并发压力测试 (5 项目 x 4 指令)")
r = run_cap("run_stress", {"projects": 5, "per": 4, "timeout": 120})
if r.get("ok"):
    print(f"  分发: {r.get('dispatched')} | 成功: {r.get('succeeded')} | 失败: {r.get('failed')}")
    print(f"  通过率: {r.get('pass_rate')}% | 总耗时: {r.get('elapsed_ms')}ms")
    print(f"  分发延迟 p50: {r.get('dispatch_latency_ms', {}).get('p50')}ms | max: {r.get('dispatch_latency_ms', {}).get('max')}ms")
    print(f"  执行延迟 p50: {r.get('exec_latency_ms', {}).get('p50')}ms | max: {r.get('exec_latency_ms', {}).get('max')}ms")
    stress_pass = r.get("pass_rate", 0) >= 95
    print(f"  判定: {'PASS' if stress_pass else 'FAIL'} (≥95%)")
else:
    print(f"  压测失败: {r.get('error', '')[:150]}")
    stress_pass = False

# ---- 2) 争抢隔离测试 ----
print("\n[阶段 2] 跨项目资源争抢隔离测试 (3 项目)")
r2 = run_cap("run_contention", {"projects": 3, "per": 3})
if r2.get("ok"):
    print(f"  项目数: {r2.get('projects')} | 全部隔离: {r2.get('all_isolated')} | 数据目录唯一: {r2.get('data_dirs_unique')}")
    print(f"  通过率: {r2.get('pass_rate')}%")
    contention_pass = r2.get("pass_rate", 0) >= 100
    print(f"  判定: {'PASS' if contention_pass else 'FAIL'}")
else:
    print(f"  隔离测试失败: {r2.get('error', '')[:150]}")
    contention_pass = False

# ---- 3) 稳定性/熔断恢复测试 ----
print("\n[阶段 3] 异常退出的稳定性 + 熔断恢复测试")
r3 = run_cap("run_resilience", {"projects": ["resil_a", "resil_b"]})
if r3.get("ok"):
    v = r3.get("victim", {})
    h = r3.get("healthy", {})
    print(f"  故障项目错误数: {v.get('errors')} | 恢复正常: {v.get('recovers_after_failure')}")
    print(f"  健康项目独立完成: {h.get('completed_independently')} | 熔断生效: {r3.get('breaker_engaged')}")
    print(f"  守护进程存活: {r3.get('daemon_alive')} | 系统稳定: {r3.get('system_stable')}")
    resilience_pass = bool(r3.get("system_stable"))
    print(f"  判定: {'PASS' if resilience_pass else 'FAIL'}")
else:
    print(f"  稳定性测试失败: {r3.get('error', '')[:150]}")
    resilience_pass = False

# ---- 汇总 ----
print("\n" + "=" * 56)
all_pass = stress_pass and contention_pass and resilience_pass
print(f"万能插通道打磨总判定: {'✅ 全部通过' if all_pass else '⚠️ 部分未通过'}")
print(f"  压力测试: {'✅' if stress_pass else '❌'} | 隔离测试: {'✅' if contention_pass else '❌'} | 稳定性: {'✅' if resilience_pass else '❌'}")
print("=" * 56)
