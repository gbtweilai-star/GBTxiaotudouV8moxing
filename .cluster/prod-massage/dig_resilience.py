"""韧性测试深挖: 看 run_resilience 的完整返回和实现"""
import json, subprocess, sys, io, re

ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
CAP = ROOT + r"\caps\universal_plugin\run.py"

# 1) 完整返回
p = subprocess.run([sys.executable, CAP, "run_resilience", "{}"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace",
                   cwd=ROOT, timeout=300)
raw = (p.stdout or "").strip()
try:
    d = json.loads(raw)
    print("run_resilience 完整返回:")
    print(json.dumps(d, ensure_ascii=False, indent=1)[:2500])
except Exception:
    print("非JSON:", raw[:500], p.stderr[:300])
