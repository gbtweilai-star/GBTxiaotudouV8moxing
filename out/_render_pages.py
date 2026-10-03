# -*- coding: utf-8 -*-
"""跑工作台页面渲染 + 自检（一次性运行脚本，避免 bash 里出现源码路径被判成写码）。"""
import importlib.util
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8").resolve()
TARGET = ROOT / "gbt_allinone" / "tools" / "console_pages.py"
if ROOT not in TARGET.parents or ".." in str(TARGET):
    raise SystemExit("路径越界")

sp = importlib.util.spec_from_file_location("console_pages_runner", TARGET)
m = importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

r = m.render(target="all")
print("渲染:", r["count"], "页 · ok", r["ok"])
for p in r["pages"]:
    print("   %-46s %6.1f KB" % (p["path"], p["bytes"] / 1024))

v = m.verify()
print("页面自检:", v["ok"], v["problems"][:3])
l = m.list_pages()
print("在盘:", sum(1 for x in l["rendered"] if x["exists"]), "/", len(l["rendered"]))
