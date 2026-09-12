import io
src = io.open(r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\universal_plugin\run.py", encoding="utf-8", errors="replace").read()
i = src.find("def h_run_resilience")
j = src.find("\ndef ", i + 10)
print(src[i:j][:4200])
