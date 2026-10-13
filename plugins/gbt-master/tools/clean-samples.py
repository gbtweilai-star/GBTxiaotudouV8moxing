# -*- coding: utf-8 -*-
"""Phase 1 前置 v2：去背 + **只留最大连通块（人）** + 紧贴居中 1024²。
v1 的问题：虚线/标签框残留把包围盒撑大，人物只占 13% —— 不合格，重做。"""
import pathlib
import shutil
from collections import deque
from PIL import Image, ImageDraw
import numpy as np

WS = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
ATT = pathlib.Path(r"C:\Users\ADMIN\.dsh\attachments\v1\objects")
DST = WS / "holo_pet/assets/digital-human/samples"
DST.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    ("Day2-JK黑白甜酷", ATT / "d7/d76132dbba68bc3f147268b56650e0e13682445922324b457f7a35f8a9efa518", (0.30, 0.06, 0.72, 0.88)),
    ("Day4-JK海军蓝",   ATT / "0c/0c6b65ed117dd7a5ccb6b0014e76479dca8c95d0673c73cc207ca52dd6fa0e77", (0.30, 0.06, 0.72, 0.92)),
    ("OL四套职场",      ATT / "01/01b96cd30c541598c1f248dd1503513b424ce9aa12ee90e939d899f78efa2a1d", (0.00, 0.05, 0.30, 0.95)),
]


def largest_component(mask):
    """4 连通标记，返回只含最大连通块的掩码。"""
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


def clean(src, frac, out_png, out_cmp, tag):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    box = (int(W * frac[0]), int(H * frac[1]), int(W * frac[2]), int(H * frac[3]))
    crop = im.crop(box)

    work = crop.copy()
    ImageDraw.Draw(work)
    key = (255, 0, 255)
    for xy in [(0, 0), (work.width - 1, 0), (0, work.height - 1), (work.width - 1, work.height - 1)]:
        ImageDraw.floodfill(work, xy, key, thresh=42)

    a = np.asarray(work).astype(np.int16)
    is_key = (a[:, :, 0] > 220) & (a[:, :, 1] < 60) & (a[:, :, 2] > 220)
    keep = ~is_key
    keep = largest_component(keep)                     # ← v2 关键：只留最大块
    dropped = int((~is_key).sum() - keep.sum())

    rgba = np.dstack([np.asarray(crop), (keep * 255).astype(np.uint8)])
    out = Image.fromarray(rgba, "RGBA")
    bbox = out.getchannel("A").getbbox()
    out = out.crop(bbox)

    side = int(max(out.size) * 1.12)                   # 6% 边距
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(out, ((side - out.width) // 2, (side - out.height) // 2), out)
    final = canvas.resize((1024, 1024), Image.LANCZOS)
    final.save(out_png)

    fa = np.asarray(final)[:, :, 3]
    solid = int((fa > 8).sum())
    ys, xs = np.where(fa > 8)
    print(f"{tag}: 清掉碎块 {dropped} px · 主体 {out.size} · 占画面 {solid/(1024*1024)*100:.1f}% "
          f"· 高度占 {(ys.max()-ys.min())/1024*100:.0f}% · 宽度占 {(xs.max()-xs.min())/1024*100:.0f}%")

    # 对照图：左=裁切原图；右=清后（棋盘底）
    hw = 512
    left = crop.resize((hw, int(crop.height * hw / crop.width)), Image.LANCZOS)
    right = final.resize((hw, hw), Image.LANCZOS)
    sheet = Image.new("RGB", (hw * 2, max(left.height, hw) + 44), (18, 22, 34))
    dd = ImageDraw.Draw(sheet)
    for yy in range(44, sheet.height, 24):
        for xx in range(hw, hw * 2, 24):
            if ((xx // 24) + (yy // 24)) % 2 == 0:
                dd.rectangle([xx, yy, xx + 23, yy + 23], fill=(28, 34, 50))
    sheet.paste(left, (0, 44))
    sheet.paste(right, (hw, 44), right)
    dd.text((8, 14), tag + " · 左：裁切原图", fill=(232, 236, 248))
    dd.text((hw + 8, 14), "右：清后（只留主体 · 居中 1024²）", fill=(0, 229, 255))
    sheet.save(out_cmp)


for tag, src, frac in SAMPLES:
    if not src.exists():
        print("缺素材:", tag)
        continue
    shutil.copyfile(src, DST / (tag + "-原图.png"))
    clean(src, frac, DST / (tag + "-清图.png"), DST / (tag + "-对照.png"), tag)
print("\n输出:", DST)
