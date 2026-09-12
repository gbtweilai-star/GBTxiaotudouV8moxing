import json, subprocess, sys, time
# 诊断：run.py status 为什么没能拉起新守护进程
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
cap = ROOT + r"\caps\universal_plugin\run.py"
p = subprocess.run([sys.executable, cap, "status"], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", cwd=ROOT, timeout=90)
print("STDOUT:", (p.stdout or "")[:500])
print("STDERR:", (p.stderr or "")[:800])
print("RC:", p.returncode)

time.sleep(2)
try:
    st = json.load(open(ROOT + r"\.gbt\universal_plugin\daemon_state.json", encoding="utf-8"))
    print("state:", st)
except Exception as e:
    print("state read fail:", e)
