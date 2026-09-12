import io, os, json, shutil

# ========== 根因修复：变体目录追踪与净化 ==========

# 1. 追踪"GBT 小土豆 V8"（带空格）变体目录的现状
candidates = [
    r"C:\Users\ADMIN\Desktop\GBT 小土豆 V8",
    r"C:\Users\ADMIN\Desktop\GBT小土豆 V8",
    r"C:\Users\ADMIN\Desktop\GBT 小土豆V8",
]
print("=== 1. 变体目录追踪 ===")
live_variants = []
for c in candidates:
    if os.path.isdir(c):
        live_variants.append(c)
        n = sum(len(fs) for _, _, fs in os.walk(c))
        print(f"⚠ 存在变体: {c} | 文件数 {n}")
    else:
        print(f"✓ 不存在: {c}")

# Desktop 现存全部 GBT 相关目录
print("\nDesktop 现存 GBT 相关目录:")
for name in sorted(os.listdir(r"C:\Users\ADMIN\Desktop")):
    if "GBT" in name or "土豆" in name:
        print(f"  {name}")

# 2. 正式工作区唯一性宣言
CANON = r"C:\Users\ADMIN\Desktop\GBT小土豆V8"
print(f"\n=== 2. 正式工作区（唯一权威路径）===\n  {CANON}")

# 3. 把散落在变体目录里的五维文件合并回正式工作区（如有）
print("\n=== 3. 变体目录残留文件回收 ===")
recovered = 0
for c in live_variants:
    src_cluster = os.path.join(c, ".cluster", "five-dim-ultimate")
    if os.path.isdir(src_cluster):
        for root, dirs, files in os.walk(src_cluster):
            for fn in files:
                sp = os.path.join(root, fn)
                rel = os.path.relpath(sp, src_cluster)
                dp = os.path.join(CANON, ".cluster", "five-dim-ultimate", rel)
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                if not os.path.isfile(dp):
                    shutil.copy2(sp, dp)
                    recovered += 1
                    print(f"  回收: {rel}")
if recovered == 0:
    print("  无残留（此前已手动回收）")

# 4. 生成工作区指纹（做人习惯#1：开工先认门牌）
print("\n=== 4. 工作区指纹 ===")
fp = {
    "canonical": CANON,
    "marker_file": "AGENTS.md",
    "marker_exists": os.path.isfile(os.path.join(CANON, "AGENTS.md")),
    "soul_exists": os.path.isfile(os.path.join(CANON, "SOUL.md")),
    "cluster_exists": os.path.isdir(os.path.join(CANON, ".cluster")),
    "variants_live": live_variants,
}
for k, v in fp.items():
    print(f"  {k}: {v}")

out = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\workspace_fingerprint.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(fp, f, indent=2, ensure_ascii=False)
print(f"\n已保存: {out}")
