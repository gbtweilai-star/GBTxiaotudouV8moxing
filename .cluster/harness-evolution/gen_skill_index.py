"""生成 skills_index.json — 把 GBT 539 caps 变成 llm_client 按需注入的技能注册表"""
import json, os
from pathlib import Path

GBT = Path(r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt")
caps_dir = GBT / "caps"

index = []
for name in sorted(os.listdir(caps_dir)):
    cj = caps_dir / name / "capability.json"
    if not cj.is_file():
        continue
    try:
        d = json.loads(cj.read_text(encoding="utf-8"))
    except Exception:
        continue
    desc = str(d.get("description", ""))[:80]
    if not desc:
        desc = f"{name} 能力"
    # tags: 名字分词 + actions 名
    tags = [name.lower()]
    tags += [str(a).lower() for a in (d.get("actions", {}) or {}).keys()][:8]
    index.append({"name": name, "desc": desc, "tags": tags, "path": f"caps/{name}"})

out = GBT / "brain" / "skills_index.json"
out.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"skills_index.json: {len(index)} 条技能注册表 → {out}")
print(f"示例: {index[0]['name']}: {index[0]['desc'][:40]}")
