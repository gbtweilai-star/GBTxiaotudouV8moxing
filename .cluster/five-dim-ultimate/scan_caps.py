import os, re, json

# 扫描 gbt 工作区全部 cap 名单
ROOT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps"
caps = []
for name in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, name)
    if os.path.isdir(d):
        # 判定状态
        has_run = os.path.isfile(os.path.join(d, "run.py"))
        has_spec = os.path.isfile(os.path.join(d, "capability.json"))
        if has_run or has_spec:
            caps.append(name)

print(f"caps 总数: {len(caps)}")

# 用户点名的 50 项
wanted = ["推理", "编程", "设计", "视觉", "认知", "进化", "镜像", "审计", "意图", "触手",
          "黑客", "本体感知", "鞭策", "灵感", "循环", "Gaia", "元认知", "直觉", "审美", "记忆",
          "时序", "社交", "学习", "策略", "风险", "执行", "解释", "想象", "价值", "状态",
          "平衡", "模式", "情绪", "汇报", "建议", "任务", "技能", "预测", "校准", "图谱",
          "决策记录", "评估", "合成", "协调", "恢复", "洞察", "常识", "启发", "探索", "意识"]

# 能力名精确/模糊匹配
found = {}
missing = []
for w in wanted:
    # 先精确子串匹配
    hits = [c for c in caps if w.lower() in c.lower()]
    if hits:
        found[w] = hits
    else:
        missing.append(w)

print(f"\n直接命中: {len(found)}/50")
for w, hits in found.items():
    print(f"  {w}: {', '.join(hits[:6])}{' …' if len(hits) > 6 else ''}")

print(f"\n未直接命中: {len(missing)} 项")
print(" ", ", ".join(missing))

# 保存完整清单供后续对齐
out = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\cap_inventory.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump({"total_caps": len(caps), "caps": caps, "wanted": wanted,
               "found": found, "missing": missing}, f, indent=2, ensure_ascii=False)
print(f"\n已保存: {out}")
