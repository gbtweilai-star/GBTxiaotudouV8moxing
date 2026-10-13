# -*- coding: utf-8 -*-
"""把仓库里已有的 3D 数字人做成两档样张：干净裁切 + 暗场柔边合成。"""
import pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
SRC = ROOT / "projects" / "digital-human" / "out" / "frames-v3" / "04_转身" / "hd_f000.png"
OUT = ROOT / "outputs" / "数字人语音助手" / ".qa"

src = Image.open(SRC).convert("RGB")
portrait = src.crop((370, 110, 730, 560))            # 头 + 肩 + 胸
portrait.save(OUT / "avatar-3d-portrait.png")

# ── 暗场柔边合成：椭圆羽化，四边先淡再贴，避免把影棚背景硬边带进来 ──
W, H = 900, 1150
work = portrait.resize((portrait.width * 2, portrait.height * 2), Image.LANCZOS)

mask = Image.new("L", work.size, 0)
d = ImageDraw.Draw(mask)
d.ellipse((work.width * .04, work.height * .03, work.width * .96, work.height * .93), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(70))

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
layer.paste(work.convert("RGBA"), ((W - work.width) // 2, 190), mask)

# 冷调轻微压一点，和 App 的深蓝底靠拢
rgba = layer.split()
rgb = Image.merge("RGB", rgba[:3])
rgb = ImageEnhance.Color(rgb).enhance(.82)
rgb = ImageEnhance.Brightness(rgb).enhance(.92)
layer = Image.merge("RGBA", (*rgb.split(), rgba[3]))

base = Image.new("RGB", (W, H), (11, 17, 32))

glow = Image.new("L", (W, H), 0)
ImageDraw.Draw(glow).ellipse((W * .10, H * .10, W * .90, H * .72), fill=80)
glow = glow.filter(ImageFilter.GaussianBlur(110))
base = Image.composite(Image.new("RGB", (W, H), (0, 80, 118)), base, glow)

base.paste(layer, (0, 0), layer)
base.save(OUT / "avatar-3d-on-dark.png")
print("ok")
