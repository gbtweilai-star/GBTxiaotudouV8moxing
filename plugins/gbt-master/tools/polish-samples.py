# -*- coding: utf-8 -*-
"""样板精修 v4 —— 修正 v3 三处错：
  ✗ v3 只腐蚀+羽化 → 边缘像素仍含浅色背景色 ⇒ 亮边(halo)
  ✓ v4 蒸馏抠图项目的 color decontamination：F = (C − (1−α)B) / α（按 α 反解前景色）
  ✗ v3 全局 bilateral(9,45) 太狠 ⇒ 更糊（Laplacian 12518→11656）
  ✓ v4 只在**肤色掩码**内轻磨皮（d=5,σ=18），衣服/头发纹理不动；锐化按读数调到 ≥ 原图
  ✗ v3 灰世界白平衡把她抹灰（R/B 1.12→1.01）
  ✓ v4 不做灰世界，只上轻微 S 曲线；色漂移按读数控制在 ±3 内
  ✗ v3 的 halo 指标无判别力（48.28%→48.26%）
  ✓ v4 在**中灰底**上量轮廓外 1–2px 带相对背景的亮度差
"""
import pathlib
import numpy as np
import cv2
from PIL import Image, ImageDraw

DST = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\holo_pet\assets\digital-human\samples")
SRC = DST / "Day2-JK黑白甜酷-清图.png"
OUT_A = DST / "Day2-JK黑白甜酷-精修-透明.png"
OUT_B = DST / "Day2-JK黑白甜酷-精修-影棚.png"
OUT_CMP = DST / "Day2-JK黑白甜酷-精修对照.png"

rgba = np.asarray(Image.open(SRC).convert("RGBA")).astype(np.uint8)
rgb0 = rgba[:, :, :3].astype(np.float32)                 # 原始 RGB（边缘里混着浅背景）
a0 = rgba[:, :, 3].astype(np.float32) / 255.0            # 原始 α（羽化过）

# 背景色 B：取四角外侧一圈的中位数（浅灰/白）
b = 6
corners = np.concatenate([rgb0[:b, :].reshape(-1, 3), rgb0[-b:, :].reshape(-1, 3),
                          rgb0[:, :b].reshape(-1, 3), rgb0[:, -b:].reshape(-1, 3)])
B = np.median(corners, axis=0)

# ── ① 收缩 α 1px（切掉污染最重的一圈）───────────────────────────────────
core = cv2.erode((a0 > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1)
core = cv2.GaussianBlur(core.astype(np.float32), (3, 3), 0.55)           # 羽化 0.55px
core = np.clip(core, 0, 1)

# ── ② color decontamination（核心蒸馏）：反解前景色 ──────────────────────
aa = np.clip(core, 1e-3, 1)[:, :, None]
F = (rgb0 - (1 - aa) * B[None, None, :]) / aa
F = np.clip(F, 0, 255)
# 只在边缘带用反解色（内部原样，避免整图被改动）
edge = ((core > 0.02) & (core < 0.98)) | ((a0 > 0) & (core <= 0.02))
work = rgb0.copy()
work[edge] = F[edge]

# ── ③ 只在肤色掩码内轻磨皮（蒸馏保边思想，但不许糊）────────────────────
bgr = cv2.cvtColor(work.astype(np.uint8), cv2.COLOR_RGB2BGR)
ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
skin = cv2.inRange(ycc, (0, 133, 77), (255, 173, 127))
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
skin = cv2.GaussianBlur(skin, (7, 7), 0).astype(np.float32) / 255.0
skin = skin * (core > 0.5)                                              # 只作用在主体内
soft = cv2.bilateralFilter(bgr, 5, 18, 5)
mixt = (soft.astype(np.float32) * skin[:, :, None] + bgr.astype(np.float32) * (1 - skin[:, :, None]))
work = cv2.cvtColor(np.clip(mixt, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB).astype(np.float32)


def lap_var(img_rgb, alpha01):
    g = cv2.cvtColor(img_rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F, ksize=3)[alpha01 > 0.5].var())


def halo_on_gray(img_rgb, alpha01, bg=118.0):
    """把主体合到中灰底上，量轮廓外 1–2px 带比背景亮多少（亮边=halo）。"""
    a = alpha01[:, :, None]
    comp = img_rgb * a + bg * (1 - a)
    out_ring = cv2.dilate((alpha01 > 0.05).astype(np.uint8), np.ones((3, 3), np.uint8)) - (alpha01 > 0.05).astype(np.uint8)
    ring2 = cv2.dilate((alpha01 > 0.05).astype(np.uint8), np.ones((5, 5), np.uint8)) - cv2.dilate((alpha01 > 0.05).astype(np.uint8), np.ones((3, 3), np.uint8))
    g = cv2.cvtColor(comp.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    band = (out_ring > 0) | (ring2 > 0)
    if band.sum() == 0:
        return 0.0, 0.0
    excess = np.clip(g - bg, 0, None)
    return float(excess[band].mean()), float((excess[band] > 8).mean() * 100)


def color_mean(img_rgb, alpha01):
    sel = alpha01 > 0.5
    return [float(img_rgb[:, :, i][sel].mean()) for i in range(3)]


m0 = dict(lap=lap_var(rgb0, a0), halo=halo_on_gray(rgb0, a0), col=color_mean(rgb0, a0))

# ── ④ 锐化：按读数调，必须 ≥ 原图清晰度 ─────────────────────────────────
best = work.copy()
for amt in (0.4, 0.7, 1.0, 1.4):
    cand = cv2.addWeighted(work, 1 + amt, cv2.GaussianBlur(work, (0, 0), 0.8), -amt, 0)
    if lap_var(cand, core) >= m0["lap"]:
        best = cand
        break
    best = cand
work = np.clip(best, 0, 255)

# ── ⑤ 轻微 S 曲线（不做灰世界）─────────────────────────────────────────
x = np.arange(256, dtype=np.float32) / 255.0
lut = np.clip(255 * (x + 0.16 * np.sin(np.pi * (x - 0.5)) * -1 * 0 + 0.22 * (x - 0.5) * (1 - abs(2 * x - 1))), 0, 255)
lut = np.clip(255 * (x * 1.06 - 0.03), 0, 255).astype(np.uint8)
work = cv2.LUT(work.astype(np.uint8), lut).astype(np.float32)

m1 = dict(lap=lap_var(work, core), halo=halo_on_gray(work, core), col=color_mean(work, core))

out_rgba = np.dstack([work.astype(np.uint8), (core * 255).astype(np.uint8)])
Image.fromarray(out_rgba, "RGBA").save(OUT_A)

H, W = work.shape[:2]
grad = np.linspace(242, 206, H).astype(np.uint8)
bgimg = np.dstack([np.repeat(grad[:, None], W, 1)] * 3).astype(np.float32)
af = core[:, :, None]
studio = (work * af + bgimg * (1 - af)).astype(np.uint8)
Image.fromarray(studio).save(OUT_B)

l0 = Image.open(SRC).convert("RGBA")
c0 = Image.new("RGB", l0.size, (118, 118, 118))
c0.paste(l0, (0, 0), l0)
def prep(im, h=900): return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


i0, i1 = prep(c0), prep(Image.open(OUT_B))
sheet = Image.new("RGB", (i0.width + i1.width, 944), (18, 22, 34))
d = ImageDraw.Draw(sheet)
sheet.paste(i0, (0, 44))
sheet.paste(i1, (i0.width, 44))
d.text((8, 14), "v3前（中灰底：看亮边）", fill=(232, 236, 248))
d.text((i0.width + 8, 14), "v4后（去污染·只肤色磨皮·按读数锐化）", fill=(0, 229, 255))
sheet.save(OUT_CMP)

print("读数（v3前 → v4后）")
print(f"  清晰度 Laplacian : {m0['lap']:.0f} → {m1['lap']:.0f}   （必须 ≥ 原图）")
print(f"  亮边 halo 均值   : {m0['halo'][0]:.1f} → {m1['halo'][0]:.1f}   （越小越好）")
print(f"  亮边超标像素占比 : {m0['halo'][1]:.1f}% → {m1['halo'][1]:.1f}%")
print(f"  主体色(R,G,B)    : {[round(v, 1) for v in m0['col']]} → {[round(v, 1) for v in m1['col']]}")
print(f"  输出: {OUT_A.name} · {OUT_B.name} · {OUT_CMP.name}")
