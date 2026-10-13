# -*- coding: utf-8 -*-
"""专业级 · 投影式脸部重贴图（本地、零积分、零依赖：numpy + cv2 + PIL）

思路（与商业管线里的 projection texturing 同源）：
  1) 从网格数据**自己算出模型"正面"方向**（头部顶点法线的水平分量均值）—— 不猜轴；
  2) 以正面正交投影把头部顶点映到 2D，把参考脸图的**主体框**对齐到头部 2D 框；
  3) 在 **UV 空间**做反向映射：逐三角形、逐 texel 求重心坐标 → 插值出 3D 点 → 投影 → 采样参考脸图 → 写入 baseColor；
  4) 掩码羽化后与原贴图合成，**只改脸岛**，其余贴图原样；
  5) 重建 GLB（只替换 baseColor 的字节，其余 bufferView 原样搬移，保持对齐）。

读数：正面方向 / 头部 2D 框 / 命中三角形数 / 写入 texel 数 / 覆盖率 / 新图字节。
"""
import io
import json
import pathlib
import struct
import numpy as np
import cv2
from PIL import Image

WS = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
DH = WS / "holo_pet/assets/digital-human"
SRC_GLB = DH / "raw/phase15/model.glb"
REF = DH / "samples/rebuild/ref-face-clean.png"
OUT_GLB = DH / "raw/phase15/model-face.glb"

raw = SRC_GLB.read_bytes()
jlen, = struct.unpack_from("<I", raw, 12)
J = json.loads(raw[20:20 + jlen].decode("utf-8"))
boff = 20 + jlen + ((-jlen) % 4)
blen, = struct.unpack_from("<I", raw, boff)
BIN = bytearray(raw[boff + 8: boff + 8 + blen])


def acc(i):
    a = J["accessors"][i]
    bv = J["bufferViews"][a["bufferView"]]
    n = {"VEC3": 3, "VEC2": 2, "SCALAR": 1}[a["type"]]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a["componentType"]]
    arr = np.frombuffer(bytes(BIN), dt, a["count"] * n, bv.get("byteOffset", 0)).reshape(a["count"], n)
    return arr.copy()


pr = J["meshes"][0]["primitives"][0]
P = acc(pr["attributes"]["POSITION"]).astype(np.float64)
N = acc(pr["attributes"]["NORMAL"]).astype(np.float64)
UV = acc(pr["attributes"]["TEXCOORD_0"]).astype(np.float64)
IDX = acc(pr["indices"]).astype(np.int64).reshape(-1, 3)
print(f"网格: 顶点 {len(P)} · 三角形 {len(IDX)}")

# ① 正面方向（数据驱动）
ymax, ymin = P[:, 1].max(), P[:, 1].min()
h = ymax - ymin
head = P[:, 1] > (ymax - h * 0.20)
m = N[head].mean(axis=0)
front = np.array([m[0], 0.0, m[2]])
front /= (np.linalg.norm(front) + 1e-9)
up = np.array([0.0, 1.0, 0.0])
right = np.cross(up, front)
right /= (np.linalg.norm(right) + 1e-9)
print(f"头部顶点 {int(head.sum())} · 正面方向 = ({front[0]:.3f}, {front[1]:.3f}, {front[2]:.3f}) · 右向量 = ({right[0]:.3f}, {right[2]:.3f})")

hc = P[head].mean(axis=0)


def to2d(v):
    d = v - hc
    return np.stack([d @ right, d @ up], axis=-1)


h2d = to2d(P[head])
x0, x1 = h2d[:, 0].min(), h2d[:, 0].max()
y0, y1 = h2d[:, 1].min(), h2d[:, 1].max()
print(f"头部 2D 框: x {x0:.3f}..{x1:.3f} · y {y0:.3f}..{y1:.3f}")

# ② 参考脸（主体框 = 非白区域）
ref = Image.open(REF).convert("RGB")
ra = np.asarray(ref)
rg = cv2.cvtColor(ra, cv2.COLOR_RGB2GRAY)
ys, xs = np.where(rg < 245)
rb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
print(f"参考脸 {ref.size} · 主体框 {rb}")

# ③ 解析 baseColor 槽位并解码
mat = J["materials"][0]
pbr = mat.get("pbrMetallicRoughness", {})
bc_img_idx = J["textures"][pbr["baseColorTexture"]["index"]]["source"]
bv = J["bufferViews"][J["images"][bc_img_idx]["bufferView"]]
bc_off, bc_len = bv.get("byteOffset", 0), bv["byteLength"]
tex = Image.open(io.BytesIO(bytes(BIN[bc_off:bc_off + bc_len]))).convert("RGB")
TW, TH = tex.size
tarr = np.asarray(tex).copy()
print(f"baseColor image[{bc_img_idx}] {TW}×{TH}")

# ④ UV 空间反向映射（只处理头部+朝前的三角形）
mask = np.zeros((TH, TW), np.uint8)
written = 0
picked = 0
for tri in IDX:
    if not head[tri].all():
        continue
    n = N[tri].mean(axis=0)
    if float(n @ front) < 0.25:                      # 只投影朝向正面的面
        continue
    picked += 1
    uv = UV[tri]                                      # (3,2)
    u = uv[:, 0] * TW
    v = uv[:, 1] * TH
    umin, umax = int(max(0, np.floor(u.min()))), int(min(TW - 1, np.ceil(u.max())))
    vmin, vmax = int(max(0, np.floor(v.min()))), int(min(TH - 1, np.ceil(v.max())))
    if umax < umin or vmax < vmin:
        continue
    gu, gv = np.meshgrid(np.arange(umin, umax + 1) + 0.5, np.arange(vmin, vmax + 1) + 0.5)
    a, b, c = uv[0], uv[1], uv[2]
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (gu / TW - c[0]) + (c[0] - b[0]) * (gv / TH - c[1])) / den
    w1 = ((c[1] - a[1]) * (gu / TW - c[0]) + (a[0] - c[0]) * (gv / TH - c[1])) / den
    w2 = 1 - w0 - w1
    ins = (w0 >= -0.002) & (w1 >= -0.002) & (w2 >= -0.002)
    if not ins.any():
        continue
    pos = (w0[..., None] * P[tri[0]] + w1[..., None] * P[tri[1]] + w2[..., None] * P[tri[2]])
    d = pos - hc
    px = d @ right
    py = d @ up
    sx = rb[0] + (px - x0) / max(1e-9, (x1 - x0)) * (rb[2] - rb[0])
    sy = rb[3] - (py - y0) / max(1e-9, (y1 - y0)) * (rb[3] - rb[1])   # 图像 y 向下
    ok = ins & (sx >= 0) & (sx < ra.shape[1] - 1) & (sy >= 0) & (sy < ra.shape[0] - 1)
    if not ok.any():
        continue
    yy, xx = np.where(ok)
    tarr[gv[yy, xx].astype(int), gu[yy, xx].astype(int)] = ra[sy[yy, xx].astype(int), sx[yy, xx].astype(int)]
    mask[gv[yy, xx].astype(int), gu[yy, xx].astype(int)] = 255
    written += int(ok.sum())

cov = float((mask > 0).mean() * 100)
print(f"命中朝前头部三角形 {picked} · 写入 texel {written} · 涂到贴图上 {cov:.2f}%")

# ⑤ 掩码羽化后合成（只在脸岛生效）
feather = cv2.GaussianBlur(mask, (0, 0), 1.2).astype(np.float32) / 255.0
feather = cv2.erode((feather > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8))
feather = cv2.GaussianBlur(feather.astype(np.float32), (0, 0), 1.0)[..., None]
out = (tarr.astype(np.float32) * feather + tarr.astype(np.float32) * (1 - feather)).astype(np.uint8)
# 锐化脸部（专业修图口径：只在脸岛内做频率分离式锐化）
lap = cv2.addWeighted(tarr, 1.45, cv2.GaussianBlur(tarr, (0, 0), 1.1), -0.45, 0)
out = np.where(feather > 0.02, lap, tarr).astype(np.uint8)
# 轻微保边平滑，去掉投影接缝的硬边
sm = cv2.bilateralFilter(out, 5, 24, 5)
out = np.where(feather > 0.02, sm, out).astype(np.uint8)

new_img = Image.fromarray(out)
buf = io.BytesIO()
new_img.save(buf, format="JPEG", quality=94)
new_bytes = buf.getvalue()
print(f"新 baseColor: {len(new_bytes)/1024:.0f} KB（原 {bc_len/1024:.0f} KB）")

# ⑥ 重建 GLB：只换 baseColor 的 bufferView，其余原样搬移（4 字节对齐）
views = J["bufferViews"]
new_bin = bytearray()
for i, v in enumerate(views):
    while len(new_bin) % 4:
        new_bin.append(0)
    v["byteOffset"] = len(new_bin)
    if i == J["images"][bc_img_idx]["bufferView"]:
        v["byteLength"] = len(new_bytes)
        new_bin.extend(new_bytes)
        J["images"][bc_img_idx]["mimeType"] = "image/jpeg"
    else:
        new_bin.extend(bytes(BIN[v["byteOffset"] if False else 0:0]) if False else bytes(BIN[v.get("byteOffset", 0): v.get("byteOffset", 0) + v["byteLength"]]))
J["buffers"][0]["byteLength"] = len(new_bin)
while len(new_bin) % 4:
    new_bin.append(0)
js = json.dumps(J, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
while len(js) % 4:
    js += b" "
glb = (b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(new_bin))
       + struct.pack("<I", len(js)) + b"JSON" + js
       + struct.pack("<I", len(new_bin)) + b"BIN\x00" + bytes(new_bin))
OUT_GLB.write_bytes(glb)

# ⑦ 自证：回读
back = OUT_GLB.read_bytes()
lj, = struct.unpack_from("<I", back, 12)
JB = json.loads(back[20:20 + lj].decode("utf-8"))
boff2 = 20 + lj + ((-lj) % 4)
lb, = struct.unpack_from("<I", back, boff2)
ok = back[:4] == b"glTF" and JB["buffers"][0]["byteLength"] == lb and len(JB["bufferViews"]) == len(views)
print(f"写出 {OUT_GLB.name} · {len(back)/1024/1024:.2f} MB · 自证 {'通过 ✓' if ok else '不通过 ✗'}")
Image.fromarray(out).resize((768, 768)).save(WS / "render" / "tex-baseColor-换脸后.jpg", quality=90)
print("  贴图对照 → render/tex-baseColor-换脸后.jpg")
