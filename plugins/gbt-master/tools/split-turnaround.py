# -*- coding: utf-8 -*-
"""把 Owner 给的三视图转面图切成 正/侧/背 三张，各自去背 + 只留最大连通块 + 居中 1024²。

判据（与 clean-samples.py 同口径）：
  · 分隔线自动探测（整列近似同色 ⇒ 判为分隔）
  · floodfill 从四角灌键色 → 反选得前景 → 只留最大连通块（人）
  · 紧贴 bbox → 正方画布 6% 边距 → 1024²
输出：samples/Owner-三视图-{正面,侧面,背面}.png + 对照图
"""
import pathlib
from collections import deque
from PIL import Image, ImageDraw
import numpy as np

WS = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
DST = WS / "holo_pet/assets/digital-human/samples"
SRC = DST / "Owner-三视图-原图.png"
TAGS = ["正面", "侧面", "背面"]


def largest_component(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best, best_size = None, 0
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            q = deque([(sy, sx)])
            seen[sy, sx] = True
            comp = []
            while q:
                y, x = q.popleft()
                comp.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if len(comp) > best_size:
                best_size, best = len(comp), comp
    out = np.zeros_like(mask, dtype=bool)
    if best:
        ys = np.array([p[0] for p in best])
        xs = np.array([p[1] for p in best])
        out[ys, xs] = True
    return out


def find_separators(arr):
    """找整列方差极小的列（分隔线）；返回分割边界列表。"""
    h, w, _ = arr.shape
    colstd = arr.reshape(h, w, 3).std(axis=(0, 2))
    is_sep = colstd < 6.0
    # 连续 True 段取中心
    spans, start = [], None
    for x in range(w):
        if is_sep[x] and start is None:
            start = x
        elif not is_sep[x] and start is not None:
            spans.append((start, x - 1))
            start = None
    if start is not None:
        spans.append((start, w - 1))
    # 只保留内部、宽度 < 8% 画宽的分隔
    return [(a + b) // 2 for a, b in spans if (b - a) < w * 0.08 and a > 0 and b < w - 1]


def drop_platform(mask):
    """砍掉底部的**展示台**。

    🔴 实测教训（2026-09-25）：原图的模特踩在一块展示台上，台子与脚**连通**
    ⇒ 「只留最大连通块」照样把它留下 ⇒ 三视图一起喂给 Tripo 后，重建结果里
    长出一个**白色台子 + 几根游离灰柱**（毛坯，不能进管线）。
    判据：从底部往上扫，某一行前景宽度**突然**超过其上方基准行宽度的 1.6 倍 ⇒ 台子起点。
    """
    h, w = mask.shape
    widths = mask.sum(axis=1)
    body = widths[widths > 0]
    if body.size == 0:
        return mask, 0
    ref_rows = widths[int(h * 0.60):int(h * 0.85)]
    ref = float(np.median(ref_rows[ref_rows > 0])) if (ref_rows > 0).any() else 0.0
    if ref <= 0:
        return mask, 0
    cut = None
    for y in range(h - 1, int(h * 0.85), -1):
        if widths[y] > ref * 1.6:
            cut = y
    if cut is None:
        return mask, 0
    out = mask.copy()
    out[cut:, :] = False
    return out, int(h - cut)


def fill_holes(mask):
    """填掉被前景**完全包住**的洞（高光过曝处会被误判成背景）。

    做法：从画布四边对「反掩码」做一次连通标记，标记不到的反掩码像素 = 洞。
    """
    h, w = mask.shape
    inv = ~mask
    reach = np.zeros_like(inv, dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if inv[y, x] and not reach[y, x]:
                reach[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if inv[y, x] and not reach[y, x]:
                reach[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and inv[ny, nx] and not reach[ny, nx]:
                reach[ny, nx] = True
                q.append((ny, nx))
    return mask | (inv & ~reach)


def background_mask(arr):
    """判「背景样」像素：**低色度 + 够亮**。

    🔴 为什么不用四角泛洪（2026-09-25 实测教训）：
      原图里模特踩着一块**浅灰展示台**，台面被它自己的深色边圈**封闭** ⇒ 从画布四角
      泛洪**永远进不去**，整块台子被当成"人"留在前景，一路喂给 Tripo，重建结果里就长出
      白台子 + 游离灰柱（毛坯）。泛洪这条路治不了封闭区域，改判**颜色**：
        · 灰底、灰台、灰影 —— 色度极低（R≈G≈B）且不暗  ⇒ 判背景
        · 皮肤（暖色，色度大）/ 黑衣黑鞋（很暗）/ 头发（暗棕） ⇒ 判前景
      高光过曝处会被误判成背景，但那属于**封闭洞**，用 fill_holes 补回来。
    """
    a = arr.astype(np.int16)
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    chroma = mx - mn
    lum = a.mean(axis=2)
    return (chroma < 24) & (lum > 85)


def clean_view(crop, tag):
    arr = np.asarray(crop)
    m = ~background_mask(arr)
    m = fill_holes(m)
    m = largest_component(m)
    m, cut_px = drop_platform(m)

    rgba = np.dstack([arr, (m * 255).astype(np.uint8)])
    out = Image.fromarray(rgba, "RGBA")
    bbox = out.getchannel("A").getbbox()
    if bbox is None:
        print(f"{tag}: 🔴 全空，跳过")
        return None
    out = out.crop(bbox)

    side = int(max(out.size) * 1.12)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(out, ((side - out.width) // 2, (side - out.height) // 2), out)
    final = canvas.resize((1024, 1024), Image.LANCZOS)

    fa = np.asarray(final)[:, :, 3]
    ys, xs = np.where(fa > 8)
    print(f"{tag}: 砍台 {cut_px} 行 · 主体 {out.size} "
          f"· 高度占 {(ys.max()-ys.min())/1024*100:.0f}% · 宽度占 {(xs.max()-xs.min())/1024*100:.0f}%")
    return final


im = Image.open(SRC).convert("RGB")
arr = np.asarray(im)
seps = find_separators(arr)
print(f"画布 {im.size} · 探测到分隔列 x = {seps}")

edges = [0] + seps + [im.width]
views = []
for i in range(min(3, len(edges) - 1)):
    x0, x1 = edges[i], edges[i + 1]
    x0 = x0 + 4 if i > 0 else x0
    x1 = x1 - 4 if i < len(edges) - 2 else x1
    views.append((TAGS[i], im.crop((x0, 0, x1, im.height))))
if len(views) < 3:
    # 兜底：均分三份
    print("🔴 分隔探测不足 3 段，改均分")
    views = [(TAGS[i], im.crop((im.width * i // 3, 0, im.width * (i + 1) // 3, im.height))) for i in range(3)]

finals = []
for tag, crop in views:
    f = clean_view(crop, tag)
    if f is None:
        continue
    p = DST / f"Owner-三视图-{tag}.png"
    f.save(p)
    finals.append((tag, crop, f, p))
    print("  →", p.name)

# 对照图：上排裁切原图，下排清后
if finals:
    hw = 340
    rows = []
    top = Image.new("RGB", (hw * len(finals), hw), (18, 22, 34))
    bot = Image.new("RGB", (hw * len(finals), hw), (18, 22, 34))
    for i, (tag, crop, f, _) in enumerate(finals):
        t = crop.resize((hw, int(crop.height * hw / crop.width)), Image.LANCZOS)
        top.paste(t.crop((0, 0, hw, min(hw, t.height))), (i * hw, 0))
        bot.paste(f.resize((hw, hw), Image.LANCZOS), (i * hw, 0))
    sheet = Image.new("RGB", (hw * len(finals), hw * 2 + 30), (18, 22, 34))
    sheet.paste(top, (0, 24))
    sheet.paste(bot, (0, hw + 30))
    d = ImageDraw.Draw(sheet)
    d.text((8, 6), "上：原图裁切", fill=(232, 236, 248))
    d.text((8, hw + 12), "下：去背 · 只留主体 · 居中 1024²", fill=(0, 229, 255))
    sheet.save(DST / "Owner-三视图-对照.png")
    print("\n对照图 →", (DST / "Owner-三视图-对照.png").name)
