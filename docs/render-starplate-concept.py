"""Render the starplate concept preview without changing the live website."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import random


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
LOGO = Image.open(ROOT / "images/brand/datong-logo-emblem.png").convert("RGBA")
BG = Image.open(ROOT / "images/background/bg-1.webp").convert("RGB")


def font(size, chinese=False, bold=False):
    name = "msyhbd.ttc" if chinese and bold else "msyh.ttc" if chinese else "georgiab.ttf" if bold else "georgia.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size)


def cover(image, size):
    w, h = size
    scale = max(w / image.width, h / image.height)
    scaled = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    x = (scaled.width - w) // 2
    y = (scaled.height - h) // 2
    return scaled.crop((x, y, x + w, y + h)).convert("RGBA")


def cloud_layer(size, phase):
    layer = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(layer)
    for bank, direction in ((.22, 1), (.75, -1)):
        for band in range(8):
            pts = []
            for i in range(121):
                t = i / 120
                x = size * (-.12 + 1.24 * t)
                y = size * (bank + direction * (band * .012 + .029 * math.sin(t * 7 + phase + band * .20) + .035 * t))
                pts.append((x, y))
            color = (223, 211, 181, 86 - band * 7) if band % 3 else (144, 174, 181, 62)
            draw.line(pts, fill=color, width=max(2, size // 150), joint="curve")
    return layer.filter(ImageFilter.GaussianBlur(size / 180))


def starplate(size, phase=0, progress=.33):
    s = 4
    n = size * s
    canvas = Image.new("RGBA", (n, n))
    d = ImageDraw.Draw(canvas)
    cx = cy = n / 2
    r = n * .365
    # Ink-blue plate with one restrained antique-gold rim.
    d.ellipse((cx-r-2, cy-r-2, cx+r+2, cy+r+2), fill=(12, 28, 49, 244), outline=(177, 147, 90, 205), width=3*s)
    # Clouds are moving, translucent curves, clipped inside the plate.
    cloud = cloud_layer(n, phase)
    mask = Image.new("L", (n, n))
    ImageDraw.Draw(mask).ellipse((cx-r+8, cy-r+8, cx+r-8, cy+r-8), fill=255)
    cloud.putalpha(Image.composite(cloud.getchannel("A"), Image.new("L", (n, n)), mask))
    canvas.alpha_composite(cloud)
    # The original emblem stays crisp; a thin lower wisp crosses only its edge.
    emblem = LOGO.resize((round(n*.57), round(n*.57)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(emblem, (round(cx-emblem.width/2), round(cy-emblem.height/2)))
    foreground = Image.new("RGBA", (n, n))
    fd = ImageDraw.Draw(foreground)
    for j in range(5):
        points = []
        for k in range(90):
            t = k / 89
            points.append((n*(.10 + .80*t), n*(.70 + j*.015 + .023*math.sin(6*t + phase + j*.28))))
        fd.line(points, fill=(217, 208, 185, 33-j*4), width=max(2, n//150), joint="curve")
    foreground = foreground.filter(ImageFilter.GaussianBlur(n/220))
    canvas.alpha_composite(foreground)
    d = ImageDraw.Draw(canvas)
    ring = n * .435
    d.arc((cx-ring, cy-ring, cx+ring, cy+ring), 0, 360, fill=(218, 218, 206, 69), width=2*s)
    # Existing 24-step starplate rhythm, with four stronger cardinal marks.
    for i in range(24):
        a = math.radians(-90 + i * 15)
        major = i % 6 == 0
        inner = n * (.462 if major else .478)
        outer = n * .493
        p1 = (cx + inner * math.cos(a), cy + inner * math.sin(a))
        p2 = (cx + outer * math.cos(a), cy + outer * math.sin(a))
        d.line((p1, p2), fill=(201, 167, 104, 205) if major else (211, 215, 208, 74), width=2*s if major else s)
    d.arc((cx-ring, cy-ring, cx+ring, cy+ring), -90, -90 + 360*progress, fill=(225, 195, 127, 255), width=3*s)
    a = math.radians(-90 + 360*progress)
    hx, hy = cx+ring*math.cos(a), cy+ring*math.sin(a)
    d.ellipse((hx-2.2*s, hy-2.2*s, hx+2.2*s, hy+2.2*s), fill=(245, 224, 166, 255))
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def full_preview():
    w, h = 1500, 920
    image = cover(BG, (w, h))
    image.alpha_composite(Image.new("RGBA", (w, h), (5, 15, 31, 140)))
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((323, 80, 1390, 848), radius=6, fill=(238, 232, 219, 253), outline=(166, 132, 85, 185), width=2)
    # Quiet paper fibres and warm margins.
    grain = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(grain)
    random.seed(6)
    for _ in range(3000):
        x, y = random.randrange(336, 1380), random.randrange(94, 836)
        gd.point((x, y), fill=(112, 91, 62, random.randrange(3, 12)))
    image.alpha_composite(grain)
    d = ImageDraw.Draw(image)
    d.text((396, 132), "INTRODUCTION", font=font(19), fill=(117, 84, 44))
    d.line((396, 176, 1318, 176), fill=(151, 126, 90), width=2)
    d.text((396, 211), "大同学社", font=font(51, chinese=True, bold=True), fill=(24, 44, 69))
    d.text((398, 285), "Datong Society of China Studies", font=font(29), fill=(34, 55, 80))
    d.text((398, 365), "A student-led community at UC Berkeley", font=font(20), fill=(82, 91, 101))
    d.text((398, 447), "以跨学科的视角，展开关于中国与东亚的对话。", font=font(23, chinese=True), fill=(49, 61, 71))
    d.text((398, 500), "在这里，阅读、讨论与公共交流共同构成我们的日常。", font=font(21, chinese=True), fill=(49, 61, 71))
    d.line((398, 613, 1315, 613), fill=(176, 151, 112), width=1)
    d.text((398, 653), "READING  /  EXCHANGE  /  COMMUNITY", font=font(17), fill=(122, 89, 49))
    d.text((398, 770), "A registered student organization at UC Berkeley", font=font(16), fill=(89, 97, 108))
    image.alpha_composite(starplate(224, phase=.8), (41, 42))
    d = ImageDraw.Draw(image)
    d.text((82, 296), "回到主页  ·  HOME", font=font(17, chinese=True), fill=(239, 229, 207))
    d.text((58, 808), "星盘 · 云气", font=font(20, chinese=True), fill=(230, 214, 177))
    d.text((58, 844), "VISUAL CONCEPT", font=font(16), fill=(218, 210, 194))
    image.convert("RGB").save(OUT / "starplate-cloud-concept.png", optimize=True)


def animated_detail():
    frames = []
    base = cover(BG, (480, 480))
    veil = Image.new("RGBA", (480, 480), (5, 15, 31, 135))
    for i in range(24):
        frame = base.copy()
        frame.alpha_composite(veil)
        frame.alpha_composite(starplate(350, phase=i / 24 * 2*math.pi), (65, 54))
        d = ImageDraw.Draw(frame)
        d.text((150, 420), "流动云气 · 动效示意", font=font(18, chinese=True), fill=(238, 227, 199))
        frames.append(frame.convert("RGB").quantize(colors=128, method=Image.Quantize.FASTOCTREE))
    frames[0].save(OUT / "starplate-cloud-motion.gif", save_all=True, append_images=frames[1:], duration=130, loop=0, optimize=True)


if __name__ == "__main__":
    full_preview()
    animated_detail()
