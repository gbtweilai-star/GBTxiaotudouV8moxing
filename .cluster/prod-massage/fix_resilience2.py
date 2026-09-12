import io
# 找到根因了: 延迟=入队→取item 的调度延迟。测试里 victim 只有2条指令, 慢指令 2500ms 是"执行时长",
# 但队列立即取走 → 调度延迟≈0ms → 平均延迟不涨 → 熔断不触发。
# 而真正的触发场景是"积压"(多指令排队)——早前 verify_breaker3 用 20 条积压才触发。
# 修复: 韧性测试的熔断验证段改为"积压触发"——victim 快速塞入多条 sleep 指令制造排队延迟
f = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\universal_plugin\run.py"
src = io.open(f, "r", encoding="utf-8").read()

old = '''    # 熔断生效验证: 高延迟窗口期新分发应被限流
    r_limited = _daemon_req(port, {"op": "dispatch", "project": victim, "command": {
        "kind": "sleep", "ms": 5}}, timeout=10.0)
    breaker_engaged = bool(r_limited.get("limited")) or bool(r_limited.get("ok") is False)'''

new = '''    # 熔断生效验证: 2026-09-12 修复 — 延迟统计的是"入队→取件"调度延迟(非执行时长),
    # 需积压排队才会推高均值 → victim 快速塞入多条 sleep 制造积压, 第 11 条应被限流
    for _qi in range(10):
        _daemon_req(port, {"op": "dispatch", "project": victim, "command": {
            "kind": "sleep", "ms": 400}}, timeout=10.0)
    time.sleep(1.5)
    r_limited = _daemon_req(port, {"op": "dispatch", "project": victim, "command": {
        "kind": "sleep", "ms": 5}}, timeout=10.0)
    breaker_engaged = bool(r_limited.get("limited")) or bool(r_limited.get("ok") is False)'''

if new in src:
    print("already patched")
elif old in src:
    src = src.replace(old, new, 1)
    io.open(f, "w", encoding="utf-8").write(src)
    compile(io.open(f, encoding="utf-8").read(), f, "exec")
    print("breaker-engagement 修复 OK + syntax OK")
else:
    print("anchor not found")
