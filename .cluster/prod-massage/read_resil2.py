import io, re
src = io.open(r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\universal_plugin\run.py", encoding="utf-8", errors="replace").read()
# 搜 resilience 相关位置
for m in re.finditer(r"resilience", src):
    i = m.start()
    seg = src[max(0,i-100):i+150].replace("\n", "⏎")
    print(f"@{i}: …{seg[:180]}…\n")
