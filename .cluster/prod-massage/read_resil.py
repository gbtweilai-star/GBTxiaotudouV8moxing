import io, re
# 找 run_resilience 的判定逻辑
src = io.open(r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\universal_plugin\run.py", encoding="utf-8", errors="replace").read()
i = src.find('"run_resilience"')
# 找实现函数
for pat in ["def op_run_resilience", "run_resilience"]:
    j = src.find("def " + pat, 0)
    if j >= 0:
        print(f"=== {pat} @ {j} ===")
        k = src.find("\ndef ", j + 10)
        print(src[j:k if k > 0 else j+4000][:3500])
        break
