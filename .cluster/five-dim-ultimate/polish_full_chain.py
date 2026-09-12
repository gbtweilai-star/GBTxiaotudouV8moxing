import json, subprocess, sys, time
# 五维合一系统 × 万能插：全链路打磨
# 1) 万能插三件套复测  2) 五维工作流通过万能插编排执行  3) 语音流利度打磨
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
cap = ROOT + r"\caps\universal_plugin\run.py"
FD = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate"

sys.path.insert(0, FD + r"\caps")

def run_cap(action, params, timeout=180):
    p = subprocess.run([sys.executable, cap, action, json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=timeout)
    raw = (p.stdout or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"ok": False, "error": (raw or p.stderr or "")[:300]}

print("=" * 56)
print("五维合一 × 万能插 全链路打磨")
print("=" * 56)

# ---- A) 万能插三件套复测（熔断修复后回归）----
print("\n[A] 万能插三件套复测")
ra = run_cap("run_stress", {"projects": 4, "per": 3, "timeout": 120})
stress_ok = ra.get("ok") and ra.get("pass_rate", 0) >= 95
print(f"  压测: {'✅' if stress_ok else '❌'} pass_rate={ra.get('pass_rate')}% elapsed={ra.get('elapsed_ms')}ms")

rb = run_cap("run_contention", {"projects": 3, "per": 2})
cont_ok = rb.get("ok") and rb.get("pass_rate", 0) >= 100
print(f"  隔离: {'✅' if cont_ok else '❌'} all_isolated={rb.get('all_isolated')}")

# ---- B) 五维工作流通过万能插编排 ----
print("\n[B] 五维工作流经万能插编排执行")
# 五个节点 = 脑眼耳嘴手，用 python 指令内联调用各模块自测逻辑
nodes = [
    {"id": "brain", "cap": "universal_plugin", "action": "invoke",
     "params": {"cap": "brain_nexus", "action": "map", "params": {}}},
    {"id": "eye", "cap": "universal_plugin", "action": "invoke",
     "params": {"cap": "ai_vision", "action": "status", "params": {}}},
    {"id": "ear", "cap": "universal_plugin", "action": "invoke",
     "params": {"cap": "audio_capture", "action": "status", "params": {}}},
    {"id": "mouth", "cap": "universal_plugin", "action": "invoke",
     "params": {"cap": "voice_speak", "action": "status", "params": {}}},
    {"id": "hand", "cap": "universal_plugin", "action": "invoke",
     "params": {"cap": "executor", "action": "status", "params": {}}},
]
r_def = run_cap("define", {"project": "five_dim_flow", "name": "五维合一链路", "nodes": nodes, "edges": [], "max_parallel": 5})
print(f"  定义工作流: {'✅' if r_def.get('ok') else '❌'}")
r_run = run_cap("run", {"project": "five_dim_flow"})
if r_run.get("ok"):
    failed = r_run.get("failed", [])
    data_flow = r_run.get("data_flow", {})
    print(f"  执行工作流: {'✅' if not failed else '❌'} 节点完成 {r_run.get('nodes_done')}/{r_run.get('nodes_total')} 失败:{failed} 耗时 {r_run.get('elapsed_ms')}ms")
    for nid, st in data_flow.items():
        print(f"    {nid}: {st}")
    flow_ok = not failed and r_run.get("nodes_done") == 5
else:
    print(f"  执行工作流: ❌ {r_run.get('error', '')[:200]}")
    flow_ok = False

# ---- C) 语音流利度打磨（多轮快速说话测试）----
print("\n[C] 语音流利度打磨（voice_mouth 连续说话）")
from voice_mouth import VoiceMouth
mouth = VoiceMouth()
phrases = [
    "五维合一系统，全链路打磨开始。",
    "脑部决策完成，置信度百分之八十五。",
    "视觉识别就绪，听觉分析就绪。",
    "现在由我播报执行结果。",
    "五维合一，打磨完成，系统顺口。",
]
total_ms = 0.0
ok_count = 0
for i, ph in enumerate(phrases):
    t0 = time.time()
    r = mouth.speak(ph, style="professional")
    dt = (time.time() - t0) * 1000
    if r.get("status") == "success":
        ok_count += 1
        total_ms += dt
        print(f"  [{i+1}/5] ✅ {dt:.0f}ms «{ph[:18]}…»")
    else:
        print(f"  [{i+1}/5] ❌ {r.get('message', '')[:80]}")
avg = total_ms / max(1, ok_count)
fluency = ok_count == len(phrases)
print(f"  连续说话成功率: {ok_count}/5 {'✅' if fluency else '❌'} | 平均句耗时 {avg:.0f}ms")

# ---- 汇总 ----
print("\n" + "=" * 56)
final = stress_ok and cont_ok and flow_ok and fluency
print(f"全链路打磨总判定: {'✅ 全部通过' if final else '⚠️ 部分未过'}")
print(f"  压测:{'✅' if stress_ok else '❌'} 隔离:{'✅' if cont_ok else '❌'} 五维编排:{'✅' if flow_ok else '❌'} 语音流利:{'✅' if fluency else '❌'}")
print("=" * 56)
