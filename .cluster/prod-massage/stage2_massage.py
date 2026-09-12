"""生产上线马杀鸡 · 第二阶段: 细节大扫除"""
import json, os, subprocess, sys, time, socket, io

ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
CANON = r"C:\Users\ADMIN\Desktop\GBT小土豆V8"

print("=" * 62)
print("第二阶段: 生产细节大扫除")
print("=" * 62)

# [F] 全 caps Python 语法编译检查
print("\n[F] 全部 caps run.py 语法编译 (523 个)")
bad_syntax = []
caps_dir = os.path.join(ROOT, "caps")
n_checked = 0
for name in sorted(os.listdir(caps_dir)):
    rp = os.path.join(caps_dir, name, "run.py")
    if not os.path.isfile(rp):
        continue
    n_checked += 1
    try:
        compile(io.open(rp, encoding="utf-8", errors="replace").read(), rp, "exec")
    except SyntaxError as se:
        bad_syntax.append((name, str(se)[:80]))
print(f"  检查 {n_checked} 个: {'✅ 全部语法通过' if not bad_syntax else f'❌ {len(bad_syntax)} 个语法错误'}")
for name, err in bad_syntax[:8]:
    print(f"    ✗ {name}: {err}")

# [G] brain 层语法检查
print("\n[G] brain 层 227 模块语法编译")
bad_brain = []
brain_dir = os.path.join(ROOT, "brain")
n_brain = 0
for f_py in sorted(os.listdir(brain_dir)):
    if not f_py.endswith(".py") or f_py == "__init__.py":
        continue
    n_brain += 1
    p = os.path.join(brain_dir, f_py)
    try:
        compile(io.open(p, encoding="utf-8", errors="replace").read(), p, "exec")
    except SyntaxError as se:
        bad_brain.append((f_py, str(se)[:80]))
print(f"  检查 {n_brain} 个: {'✅ 全部语法通过' if not bad_brain else f'❌ {len(bad_brain)} 个语法错误'}")
for name, err in bad_brain[:8]:
    print(f"    ✗ {name}: {err}")

# [H] 守护进程自愈验证(杀掉→自动复活)
print("\n[H] 守护进程自愈")
try:
    st = json.load(open(ROOT + r"\.gbt\universal_plugin\daemon_state.json", encoding="utf-8"))
    old_pid, old_port = st["pid"], st["port"]
    subprocess.run(["taskkill", "/F", "/PID", str(old_pid)], capture_output=True)
    time.sleep(1)
    CAP = ROOT + r"\caps\universal_plugin\run.py"
    p = subprocess.run([sys.executable, CAP, "status"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT, timeout=120)
    ok_heal = '"ok": true' in (p.stdout or "")
    st2 = json.load(open(ROOT + r"\.gbt\universal_plugin\daemon_state.json", encoding="utf-8"))
    print(f"  {'✅' if ok_heal else '❌'} 杀 pid {old_pid} → 复活 pid {st2.get('pid')} port {st2.get('port')}")
except Exception as e:
    ok_heal = False
    print(f"  ❌ {e}")

# [I] 端到端业务流: 万能插全链路(定义工作流→执行→验证)
print("\n[I] 端到端业务流")
def run_cap(action, params, timeout=180):
    pr = subprocess.run([sys.executable, CAP, action, json.dumps(params, ensure_ascii=False)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        cwd=ROOT, timeout=timeout)
    try:
        return json.loads((pr.stdout or "").strip())
    except Exception:
        return {"ok": False, "error": (pr.stdout or pr.stderr or "")[:200]}

r_def = run_cap("define", {"project": "prod_e2e", "name": "生产验证流", "max_parallel": 3,
    "nodes": [
        {"id": "n1", "cap": "universal_plugin", "action": "invoke",
         "params": {"cap": "brain_nexus", "action": "map", "params": {}}},
        {"id": "n2", "cap": "universal_plugin", "action": "invoke",
         "params": {"cap": "memory", "action": "status", "params": {}}},
    ], "edges": []})
r_run = run_cap("run", {"project": "prod_e2e"})
e2e_ok = r_run.get("ok") and not r_run.get("failed", [])
print(f"  定义:{'✅' if r_def.get('ok') else '❌'} 执行:{'✅' if e2e_ok else '❌'} "
      f"节点 {r_run.get('nodes_done')}/{r_run.get('nodes_total')} 耗时 {r_run.get('elapsed_ms')}ms")
run_cap("detach", {"project": "prod_e2e"})

# [J] 关键端口健康
print("\n[J] 关键端口")
for name, port in [("gbt-brain MCP(经gateway)", None), ("万能插守护", None)]:
    pass
st3 = json.load(open(ROOT + r"\.gbt\universal_plugin\daemon_state.json", encoding="utf-8"))
try:
    s = socket.create_connection(("127.0.0.1", st3["port"]), timeout=5)
    s.sendall((json.dumps({"op": "ping"}) + "\n").encode("utf-8"))
    s.settimeout(5)
    line = b""
    while True:
        ch = s.recv(1)
        if not ch or ch == b"\n":
            break
        line += ch
    s.close()
    pong = json.loads(line.decode("utf-8"))
    print(f"  ✅ 万能插守护 port={st3['port']}: ping→pong={pong.get('pong')}")
except Exception as e:
    print(f"  ❌ 万能插守护: {e}")

print("\n" + "=" * 62)
all_ok = (not bad_syntax) and (not bad_brain) and ok_heal and e2e_ok
print(f"第二阶段: {'✅ 生产细节全清' if all_ok else '⚠️ 还有细节'}")
print(f"  语法caps:{'✅' if not bad_syntax else '❌'} 语法brain:{'✅' if not bad_brain else '❌'} "
      f"自愈:{'✅' if ok_heal else '❌'} 端到端:{'✅' if e2e_ok else '❌'}")

out = {"caps_syntax_bad": len(bad_syntax), "brain_syntax_bad": len(bad_brain),
       "daemon_heal": ok_heal, "e2e": e2e_ok}
os.makedirs(os.path.join(CANON, ".cluster", "prod-massage"), exist_ok=True)
with open(os.path.join(CANON, ".cluster", "prod-massage", "stage2.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
