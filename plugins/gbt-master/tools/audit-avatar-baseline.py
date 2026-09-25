# -*- coding: utf-8 -*-
"""Phase 0.5 基线验收：把现有数字人 GLB 的骨架 / 绑定姿势 / 蒙皮 / 动作 / 资产体量逐项读实。

判据（专业口径）：
  1 骨架层级与骨名       —— 能不能被重定向器认出来
  2 绑定姿势 T/A pose    —— 由静止变换算 肩→手 世界向量与水平夹角（T≈0°，A≈35–45°）
  3 蒙皮质量             —— JOINTS_0/WEIGHTS_0 覆盖
  4 动作真数据           —— 时长/轨道数/髋部有无位移轨/可否循环
  5 自然度缺口           —— 有无头发/裙摆弹簧骨链
  6 资产体量             —— 顶点数 / 贴图字节
"""
import json, math, struct, pathlib, sys

# ⚠️ 必须 reconfigure：本机控制台是 GBK，脚本里任何非 GBK 字符（🔴 等）都会
#    在**错误处理路径**上抛 UnicodeEncodeError —— 那会把"如实报错"变成"二次崩"（本轮实测踩到）。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 🔴 2026-09-22 更正默认路径：原默认写的是 `holo_pet/assets/digital-human/tripo-human.glb`，
#    而那个文件**全树不存在**（资产已整理进 `raw/` 分层）⇒ 本器一跑就 `FileNotFoundError` 崩掉，
#    于是"数字人基线"这件事**长期没有能跑的工具**。现在默认指**真正在用的那件**
#    （`raw/rig/model-rigged-anim.glb`，形象页与主控台都指它），并在文件不在时**如实报候选**而不是抛栈。
DEFAULT = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\holo_pet\assets\digital-human\raw\rig\model-rigged-anim.glb"
P = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
if not P.is_file():
    print("🔴 文件不在：%s" % P)
    base = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\holo_pet\assets\digital-human")
    cands = sorted((p for p in base.rglob("*.glb") if p.is_file()),
                   key=lambda p: -p.stat().st_size)[:10]
    if cands:
        print("   现读候选（按体量降序，前 10）：")
        for c in cands:
            print("     %8.2f MB  %s" % (c.stat().st_size / 1048576, c.relative_to(base).as_posix()))
    print("   用法：py -3.14 %s <某个 .glb 路径>" % pathlib.Path(__file__).name)
    print("   ⚠️ 别再指 `assets/digital-human/tripo-human.glb` —— 那是**已作废路径**"
          "（见 plugins/gbt-master/README.md §「作废路径」）。")
    raise SystemExit(2)
raw = P.read_bytes()
magic, ver, total = struct.unpack_from("<4sII", raw, 0)
off, chunks = 12, []
while off < len(raw):
    clen, ctype = struct.unpack_from("<I4s", raw, off)
    chunks.append((ctype, off + 8, clen)); off += 8 + clen
j = json.loads(next(raw[s:s + n] for t, s, n in chunks if t == b"JSON").decode("utf-8"))
BIN = next((raw[s:s + n] for t, s, n in chunks if t == b"BIN\x00"), b"")

print(f"文件 {total/1024/1024:.2f} MB · 生成器 {j['asset'].get('generator')}")
print("=" * 72)

# ── 1 骨架 ────────────────────────────────────────────────────────────────
nodes = j.get("nodes") or []
skins = j.get("skins") or []
print(f"[1] 骨架：nodes={len(nodes)} skins={len(skins)}")
joints = skins[0].get("joints") if skins else []
names = [nodes[i].get("name", f"#{i}") for i in joints]
print(f"    关节 {len(joints)} 个：")
for i, nm in enumerate(names):
    ch = nodes[joints[i]].get("children") or []
    chn = [nodes[c].get("name", f"#{c}") for c in ch]
    print(f"      - {nm}" + (f"  → 子: {', '.join(chn)}" if chn else "  （叶）"))

# ── 2 绑定姿势：由静止 TRS 组合出世界位置，量 肩→手 夹角 ───────────────────
def mat_mul(a, b):
    return [sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)) for r in range(4) for c in range(4)]

def trs(node):
    t = node.get("translation") or [0, 0, 0]
    r = node.get("rotation") or [0, 0, 0, 1]
    s = node.get("scale") or [1, 1, 1]
    x, y, z, w = r
    m = [
        (1 - 2 * (y * y + z * z)) * s[0], 2 * (x * y - z * w) * s[0], 2 * (x * z + y * w) * s[0], 0,
        2 * (x * y + z * w) * s[1], (1 - 2 * (x * x + z * z)) * s[1], 2 * (y * z - x * w) * s[1], 0,
        2 * (x * z - y * w) * s[2], 2 * (y * z + x * w) * s[2], (1 - 2 * (x * x + y * y)) * s[2], 0,
        t[0], t[1], t[2], 1,
    ]
    return m

parent = {}
for i, n in enumerate(nodes):
    for c in (n.get("children") or []):
        parent[c] = i

def world(i):
    m = trs(nodes[i])
    p = parent.get(i)
    while p is not None:
        m = mat_mul(m, trs(nodes[p]))
        p = parent.get(p)
    return m

def find(keys):
    for i, n in enumerate(nodes):
        nm = (n.get("name") or "").lower()
        if any(k in nm for k in keys):
            return i, n.get("name")
    return None, None

# Tripo/Blender 常见命名：shoulder/upperarm/forearm/hand
pairs = [(["shoulder", "upperarm", "upper_arm", "arm"], ["hand"]),
         (["upperarm", "upper_arm", "arm"], ["forearm", "lowerarm", "lower_arm"])]
print("[2] 绑定姿势推断（由静止变换算世界向量夹角；T≈0°，A≈35–45°）")
for akeys, bkeys in pairs:
    ai, an = find(akeys); bi, bn = find(bkeys)
    if ai is None or bi is None:
        print(f"    {akeys[0]} → {bkeys[0]}：骨名没匹配上，跳过")
        continue
    aw, bw = world(ai), world(bi)
    v = [bw[12] - aw[12], bw[13] - aw[13], bw[14] - aw[14]]
    horiz = math.hypot(v[0], v[2])
    ang = math.degrees(math.atan2(-v[1], horiz)) if horiz > 1e-9 else 0.0
    print(f"    {an} → {bn}：dx={v[0]:+.3f} dy={v[1]:+.3f} dz={v[2]:+.3f} → 与水平夹角 {ang:+.1f}°")

# ── 3 蒙皮质量 ────────────────────────────────────────────────────────────
meshes = j.get("meshes") or []
prims = [p for m in meshes for p in (m.get("primitives") or [])]
skinned = [p for p in prims if "JOINTS_0" in (p.get("attributes") or {})]
verts = 0
for p in prims:
    acc = j["accessors"][p["attributes"]["POSITION"]]
    verts += acc.get("count") or 0
print(f"[3] 蒙皮：primitive {len(prims)} 个 · 带 JOINTS_0 的 {len(skinned)} 个 · 顶点合计 {verts}")
print(f"    属性键：{sorted(set(k for p in prims for k in (p.get('attributes') or {})))}")

# ── 4 动作真数据 ──────────────────────────────────────────────────────────
anims = j.get("animations") or []
print(f"[4] 动作 {len(anims)} 段")
for a in anims:
    dur = 0.0
    tracks = {"rotation": 0, "translation": 0, "scale": 0}
    hips_tr = False
    for ch in (a.get("channels") or []):
        path = (ch.get("target") or {}).get("path")
        tracks[path] = tracks.get(path, 0) + 1
        smp = a["samplers"][ch["sampler"]]
        acc = j["accessors"][smp["input"]]
        if acc.get("max"):
            dur = max(dur, float(acc["max"][0]))
        tname = (nodes[(ch.get("target") or {}).get("node", 0)].get("name") or "").lower()
        if path == "translation" and ("hip" in tname or "pelvis" in tname or "root" in tname):
            hips_tr = True
    print(f"    「{a.get('name')}」时长 {dur:.2f}s · 轨道 r={tracks['rotation']} t={tracks['translation']} s={tracks['scale']} · 髋部位移轨={hips_tr}")

# ── 5 自然度缺口：弹簧骨链 ────────────────────────────────────────────────
prob = [k for k in ("hair", "skirt", "cloth", "tail", "ribbon", "cloth", "breast", "skirt") if any(k in (n.get("name") or "").lower() for n in nodes)]
print(f"[5] 弹簧骨候选（骨名含 hair/skirt/cloth/tail/ribbon/breast）：{prob if prob else '无'}")

# ── 6 资产体量 ────────────────────────────────────────────────────────────
imgs = j.get("images") or []
bvs = j.get("bufferViews") or []
img_bytes = 0
for im in imgs:
    if "bufferView" in im:
        img_bytes += bvs[im["bufferView"]].get("byteLength") or 0
print(f"[6] 资产：贴图 {len(imgs)} 张 合计 {img_bytes/1024/1024:.2f} MB · BIN 段 {len(BIN)/1024/1024:.2f} MB · 顶点 {verts}")
print(f"    材质：{[m.get('name') for m in (j.get('materials') or [])]}")
