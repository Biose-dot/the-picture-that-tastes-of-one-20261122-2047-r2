#!/usr/bin/env python3
"""One Orange — a single halved orange that fills the frame.

Procedural picture, drawn from scratch with Pillow only.
Fully deterministic: fixed seed, no clock, no network, no files read.
Writes one image: $MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png,
or ./output/entry.png when neither exists).
"""

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

SEED = 20261122
SS = 2048          # supersample size; downscaled to 1024 at the end
OUT = 1024

# --- palette ---------------------------------------------------------------
WALL_TOP = (255, 243, 210)
WALL_BOT = (252, 228, 178)
TABLE_TOP = (183, 112, 48)
TABLE_BOT = (122, 70, 26)
PLANK = (96, 54, 18)
RIND = (206, 102, 8)
RIND_DARK = (178, 84, 4)
PITH = (255, 233, 182)
FLESH_A = (255, 172, 44)
FLESH_B = (255, 146, 18)
JUICE = (255, 216, 122)
JUICE_HI = (255, 242, 196)
LEAF_A = (52, 130, 52)
LEAF_B = (30, 96, 42)
WHOLE = (244, 138, 20)
PORE = (206, 96, 4)
SHADOW = (60, 30, 8)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def leaf_points(cx, cy, length, width, tilt):
    """A pointed leaf shape as a polygon, built from two arcs."""
    pts = []
    steps = 24
    for i in range(steps + 1):
        t = i / steps
        # spine runs from base (0,0) to tip (0,-length), bulging sideways
        y = -length * t
        w = width * math.sin(math.pi * (t ** 0.8)) * 0.5
        x = w
        xr = x * math.cos(tilt) - y * math.sin(tilt)
        yr = x * math.sin(tilt) + y * math.cos(tilt)
        pts.append((cx + xr, cy + yr))
    for i in range(steps, -1, -1):
        t = i / steps
        y = -length * t
        w = width * math.sin(math.pi * (t ** 0.8)) * 0.5
        x = -w
        xr = x * math.cos(tilt) - y * math.sin(tilt)
        yr = x * math.sin(tilt) + y * math.cos(tilt)
        pts.append((cx + xr, cy + yr))
    return pts


def main():
    rng = random.Random(SEED)
    img = Image.new("RGB", (SS, SS))
    d = ImageDraw.Draw(img)

    # --- wall: warm cream vertical gradient -------------------------------
    for y in range(SS):
        t = y / SS
        d.line([(0, y), (SS, y)], fill=lerp(WALL_TOP, WALL_BOT, t))

    table_y = int(SS * 0.68)

    # --- table: warm wood, planks -----------------------------------------
    for y in range(table_y, SS):
        t = (y - table_y) / (SS - table_y)
        d.line([(0, y), (SS, y)], fill=lerp(TABLE_TOP, TABLE_BOT, t))
    for py in (0.74, 0.83, 0.92):
        y = int(SS * py)
        d.line([(0, y), (SS, y)], fill=PLANK, width=5)
        d.line([(0, y + 5), (SS, y + 5)], fill=lerp(TABLE_TOP, TABLE_BOT, 0.4), width=2)

    # soft contact shadow under the fruit
    shadow = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([SS * 0.08, SS * 0.82, SS * 0.94, SS * 0.99], fill=SHADOW + (90,))
    shadow = shadow.filter(ImageFilter.GaussianBlur(38))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)

    cx, cy = SS // 2, int(SS * 0.475)
    R = int(SS * 0.365)

    # --- whole orange behind, left ----------------------------------------
    wx, wy, wr = int(SS * 0.17), int(SS * 0.70), int(SS * 0.155)
    d.ellipse([wx - wr, wy - wr, wx + wr, wy + wr], fill=WHOLE)
    d.ellipse([wx - wr, wy - wr, wx + wr, wy + wr], outline=RIND_DARK, width=6)
    # pores
    for _ in range(260):
        a = rng.uniform(0, 2 * math.pi)
        r = wr * math.sqrt(rng.uniform(0, 0.94))
        px, py = wx + r * math.cos(a), wy + r * math.sin(a)
        rad = rng.uniform(2, 6)
        d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=PORE)
    # glossy highlight on the whole orange: soft, blurred, off-centre
    hi = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.ellipse([wx - wr * 0.55, wy - wr * 0.66, wx - wr * 0.18, wy - wr * 0.40],
               fill=(255, 220, 160, 130))
    hi = hi.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img.convert("RGBA"), hi).convert("RGB")
    d = ImageDraw.Draw(img)
    # little stem scar
    d.ellipse([wx - 26, wy - wr - 4, wx + 26, wy - wr + 30], fill=(250, 226, 170))

    # --- leaves above the halved orange ------------------------------------
    stem_x, stem_y = cx, cy - R - 8
    d.polygon(leaf_points(cx - 62, stem_y + 30, 300, 190, -0.62), fill=LEAF_B)
    d.polygon(leaf_points(cx + 66, stem_y + 30, 330, 200, 0.58), fill=LEAF_A)
    # leaf veins
    for (lx, tilt, ln) in ((cx - 62, -0.62, 300), (cx + 66, 0.58, 330)):
        x0, y0 = lx, stem_y + 30
        x1 = x0 + math.sin(tilt) * ln * 0.92
        y1 = y0 - math.cos(tilt) * ln * 0.92
        d.line([(x0, y0), (x1, y1)], fill=(20, 70, 30), width=7)
    # stem
    d.line([(cx, stem_y + 40), (cx, stem_y - 6)], fill=(120, 70, 20), width=14)

    # --- halved orange: rind, pith, flesh ----------------------------------
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=RIND)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=RIND_DARK, width=8)
    pr = int(R * 0.94)
    d.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=PITH)
    fr = int(R * 0.86)
    d.ellipse([cx - fr, cy - fr, cx + fr, cy + fr], fill=FLESH_A)

    # segments: alternate flesh tones, split by pale pith spokes
    n_seg = 10
    for i in range(n_seg):
        a0 = 2 * math.pi * i / n_seg - math.pi / 2
        a1 = 2 * math.pi * (i + 1) / n_seg - math.pi / 2
        mid = (a0 + a1) / 2
        if i % 2 == 0:
            d.pieslice([cx - fr, cy - fr, cx + fr, cy + fr],
                       math.degrees(a0), math.degrees(a1), fill=FLESH_B)
        # pith spoke: thin wedge from centre to rim
        w = 0.018
        d.polygon([
            (cx + math.cos(a0 - w) * 26, cy + math.sin(a0 - w) * 26),
            (cx + math.cos(a0 - w) * fr, cy + math.sin(a0 - w) * fr),
            (cx + math.cos(a0 + w) * fr, cy + math.sin(a0 + w) * fr),
            (cx + math.cos(a0 + w) * 26, cy + math.sin(a0 + w) * 26),
        ], fill=PITH)

    # juice cells: dense radial streaks inside every segment
    glow = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(n_seg):
        a0 = 2 * math.pi * i / n_seg - math.pi / 2 + 0.06
        a1 = 2 * math.pi * (i + 1) / n_seg - math.pi / 2 - 0.06
        for _ in range(150):
            a = rng.uniform(a0, a1)
            r0 = rng.uniform(fr * 0.18, fr * 0.82)
            ln = rng.uniform(fr * 0.05, fr * 0.16)
            x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
            x1, y1 = cx + (r0 + ln) * math.cos(a), cy + (r0 + ln) * math.sin(a)
            col = JUICE_HI if rng.random() < 0.35 else JUICE
            gd.line([(x0, y0), (x1, y1)], fill=col + (rng.randint(120, 210),),
                    width=rng.randint(3, 7))
    # water droplets on the cut face
    for _ in range(46):
        a = rng.uniform(0, 2 * math.pi)
        r = fr * math.sqrt(rng.uniform(0.05, 0.85))
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        rad = rng.uniform(7, 22)
        gd.ellipse([px - rad, py - rad, px + rad, py + rad],
                   fill=(255, 250, 225, 165))
        gd.ellipse([px - rad * 0.45, py - rad * 0.5, px - rad * 0.05, py - rad * 0.1],
                   fill=(255, 255, 255, 215))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)

    # centre star of the cut face
    d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=PITH)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(255, 246, 214))

    # glossy sheen across the upper-left of the flesh
    sheen = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    shd = ImageDraw.Draw(sheen)
    shd.ellipse([cx - fr * 0.95, cy - fr * 1.05, cx + fr * 0.15, cy - fr * 0.05],
                fill=(255, 255, 255, 46))
    sheen = sheen.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img.convert("RGBA"), sheen).convert("RGB")
    d = ImageDraw.Draw(img)

    # --- juice beads bursting from the right rim ---------------------------
    bead = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bead)
    bx0, by0 = cx + R * 0.99, cy - R * 0.18
    # burst cluster right at the rim where the juice leaves the fruit
    for _ in range(10):
        a = rng.uniform(-1.3, 0.5)
        dist = rng.uniform(4, 42)
        px = bx0 + math.cos(a) * dist
        py = by0 + math.sin(a) * dist
        rad = rng.uniform(7, 15)
        bd.ellipse([px - rad, py - rad, px + rad, py + rad],
                   fill=(255, 176, 40, 235))
        bd.ellipse([px - rad * 0.4, py - rad * 0.45, px, py - rad * 0.05],
                   fill=(255, 240, 190, 235))
    for k in range(44):
        t = k / 43
        # short arc that rises a little, then falls back down under gravity
        ang = -1.05 + t * 0.85
        dist = 30 + t * 175 + rng.uniform(-8, 8)
        px = bx0 + math.cos(ang) * dist
        py = by0 + math.sin(ang) * dist * 0.8 + t * t * 120
        rad = max(2.5, 11 - t * 8 + rng.uniform(-1.5, 1.5))
        bd.ellipse([px - rad, py - rad, px + rad, py + rad],
                   fill=(255, 176, 40, 235))
        bd.ellipse([px - rad * 0.4, py - rad * 0.45, px, py - rad * 0.05],
                   fill=(255, 240, 190, 235))
    img = Image.alpha_composite(img.convert("RGBA"), bead).convert("RGB")
    d = ImageDraw.Draw(img)

    # --- wedge leaning on the front-right ----------------------------------
    # drawn upright on its own layer, then tilted so it leans on the big orange
    wl = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wl)
    wx2, wy2 = int(SS * 0.815), int(SS * 0.845)
    wr2 = int(SS * 0.115)
    wd.pieslice([wx2 - wr2, wy2 - wr2, wx2 + wr2, wy2 + wr2], 180, 360, fill=RIND + (255,))
    wd.pieslice([wx2 - wr2 * 0.9, wy2 - wr2 * 0.9, wx2 + wr2 * 0.9, wy2 + wr2 * 0.9],
                180, 360, fill=PITH + (255,))
    wd.pieslice([wx2 - wr2 * 0.8, wy2 - wr2 * 0.8, wx2 + wr2 * 0.8, wy2 + wr2 * 0.8],
                180, 360, fill=FLESH_A + (255,))
    # spokes inside the wedge, fanning from its flat base
    for s in range(5):
        a = math.radians(180 + 36 * s + 18)
        x1 = wx2 + math.cos(a) * wr2 * 0.78
        y1 = wy2 + math.sin(a) * wr2 * 0.78
        wd.line([(wx2, wy2), (x1, y1)], fill=PITH + (255,), width=7)
    for _ in range(26):
        a = math.radians(rng.uniform(185, 355))
        r = rng.uniform(wr2 * 0.2, wr2 * 0.7)
        px, py = wx2 + r * math.cos(a), wy2 + r * math.sin(a)
        wd.line([(px, py), (px + 24, py + 6)], fill=JUICE + (255,), width=4)
    wl = wl.rotate(24, resample=Image.BICUBIC, center=(wx2, wy2))
    img = Image.alpha_composite(img.convert("RGBA"), wl).convert("RGB")
    d = ImageDraw.Draw(img)

    # --- warm vignette -------------------------------------------------------
    vig = Image.new("L", (SS, SS), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-SS * 0.12, -SS * 0.12, SS * 1.12, SS * 1.12], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (SS, SS), (70, 35, 5, 255))
    inv = vig.point(lambda v: 255 - v)
    overlay = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    overlay.putalpha(inv.point(lambda v: int(v * 0.20)))
    overlay.paste(dark, (0, 0), overlay)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # --- downscale, save ----------------------------------------------------
    img = img.resize((OUT, OUT), Image.LANCZOS)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "output"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    img.save(path, format="PNG", optimize=True)
    print("wrote", path, img.size, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    sys.exit(main())
