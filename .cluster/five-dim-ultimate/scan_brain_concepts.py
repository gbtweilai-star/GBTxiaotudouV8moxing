import os, json, re

# 在 gbt 工作区全树里搜概念命名的 brain 模块（核查员超时前发现 aesthetic_brain/emotion_brain/intuition_brain 等线索）
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"
targets = ["aesthetic_brain", "emotion_brain", "intuition_brain", "consciousness", "意识",
           "审美", "情绪", "直觉", "常识", "启发", "时序", "平衡", "校准", "合成", "洞察",
           "直觉", "价值", "模式", "情绪", "汇报", "建议", "预测", "图谱", "决策", "评估",
           "协调", "恢复", "社交", "风险", "鞭策", "灵感", "循环", "本体感知", "状态",
           "exploration", "insight", "common_sense", "heuristic", "temporal", "calibration"]

found = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    # 跳过缓存和深层归档
    rel = os.path.relpath(dirpath, ROOT)
    depth = rel.count(os.sep)
    if depth > 3 or "__pycache__" in dirpath or ".git" in dirpath:
        dirnames[:] = []
        continue
    for fn in filenames:
        base = os.path.splitext(fn)[0]
        for t in targets:
            if t.lower() in base.lower() or t in fn:
                found.setdefault(t, []).append(os.path.join(dirpath, fn))

print(f"命中 {len(found)} 个概念线索:")
for t, paths in sorted(found.items()):
    print(f"\n[{t}] {len(paths)} 个文件")
    for p in paths[:4]:
        print(f"  {p}")

# 也扫 caps 目录的 description 里含这些词的
print("\n\n=== caps 描述扫描 ===")
caps_root = os.path.join(ROOT, "caps")
desc_hits = {}
for name in sorted(os.listdir(caps_root)):
    cj = os.path.join(caps_root, name, "capability.json")
    if not os.path.isfile(cj):
        continue
    try:
        with open(cj, encoding="utf-8") as f:
            d = json.load(f)
        desc = (d.get("description") or "") + " " + (d.get("mode") or "")
        for t in ["意识", "情绪", "审美", "直觉", "常识", "启发", "时序", "平衡", "校准",
                  "合成", "洞察", "价值", "模式", "汇报", "建议", "预测", "图谱", "决策",
                  "评估", "协调", "恢复", "社交", "风险", "鞭策", "灵感", "状态", "探索"]:
            if t in desc:
                desc_hits.setdefault(t, []).append(name)
    except Exception:
        pass

print(f"描述命中 {len(desc_hits)} 个概念:")
for t, names in sorted(desc_hits.items()):
    print(f"  {t}: {', '.join(names[:8])}")

out = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\brain_concept_scan.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump({"file_hits": found, "desc_hits": desc_hits}, f, indent=2, ensure_ascii=False)
print(f"\n已保存: {out}")
