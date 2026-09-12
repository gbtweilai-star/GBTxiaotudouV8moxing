import json, socket, time
# 直接手动拉起守护进程并验证熔断修复
import subprocess, sys
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
cap = ROOT + r"\caps\universal_plugin\run.py"

# 用 attach 强制走 _daemon_ensure → _daemon_spawn 路径
p = subprocess.run([sys.executable, cap, "attach", json.dumps({"project": "warmup", "kind": "probe"})],
                   capture_output=True, text=True, encoding="utf-8", errors="replace",
                   cwd=ROOT, timeout=120)
print("attach:", (p.stdout or "")[:200], (p.stderr or "")[:200])

STATE = ROOT + r"\.gbt\universal_plugin\daemon_state.json"
st = json.load(open(STATE, encoding="utf-8"))
port = st["port"]
print("new port:", port, "pid:", st.get("pid"))

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

print("ping:", req({"op": "ping"}))
