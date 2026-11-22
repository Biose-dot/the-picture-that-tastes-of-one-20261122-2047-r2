#!/usr/bin/env python3
"""One Orange -- the picture that tastes of one ingredient.

A single halved orange fills the frame, drawn entirely procedurally
with Pillow: no files, no network, no wall clock. Every random draw
comes from a fixed seed, so two runs produce a byte-identical PNG.

Layout (1024x1024 output, rendered at 2x and downscaled):
  * warm cream-to-honey sky above a wooden table
  * a whole orange with dimpled peel behind, left
  * one big halved orange, centre-right, ten juicy segments,
    pale pith ring, droplets and a soft sheen
  * a cut wedge leaning in front, bottom right
  * green leaves sprouting from the top of the fruit
  * an arc of juice beads bursting from the cut face

Run:  python3 main.py
Out:  /output/entry.png  (or $MAKEFUN_OUTPUT_DIR/entry.png)
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

SS = 2                       # supersample factor
W = 1024 * SS                # working canvas (square)
HALF_CX, HALF_CY = 545 * SS, 552 * SS
HALF_R = 338 * SS            # halved orange radius

# ---- palette: one ingredient, warm and juicy ---------------------
SKY_TOP = (255, 246, 220)
SKY_MID = (252, 214, 148)
WOOD = (150, 88, 46)
WOOD_DARK = (120, 64, 30)
PEEL = (240, 138, 16)
PEEL_DEEP = (210, 102, 6)
PEEL_PORE = (222, 112, 10)
PITH = (255, 228, 172)
FLESH_A = (255, 168, 34)
FLESH_B = (255, 126, 6)
VESICLE = (255, 216, 112)
LEAF = (52, 142, 56)
LEAF_SHADE = (30, 98, 40)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def make_background():
    """Cream sky melting into honey, then a wooden table band."""
    grad = Image.new("RGB", (1, W))
    px = grad.load()
    horizon = int(W * 0.66)
    for y in range(W):
        if y < horizon:
            px[0, y] = mix(SKY_TOP, SKY_MID, y / horizon)
        else:
            t = (y - horizon) / (W - horizon)
            px[0, y] = mix(WOOD, WOOD_DARK, t)
    img = grad.resize((W, W))
    d = ImageDraw.Draw(img)
    # faint plank seams on the table
    for yy in (0.74, 0.84, 0.94):
        y = int(W * yy)
        d.line([(0, y), (W, y)], fill=(96, 50, 22), width=2 * SS)
    return img


def soft_shadow(img):
    layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([110 * SS, 836 * SS, 940 * SS, 946 * SS],
              fill=(58, 24, 4, 118))
    layer = layer.filter(ImageFilter.GaussianBlur(16 * SS))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_leaf(d, x, y, length, angle_deg, fill):
    """Curved leaf, stem anchored exactly at (x, y)."""
    a = math.radians(angle_deg)
    tip = (x + length * math.cos(a), y + length * math.sin(a))
    perp = math.radians(angle_deg + 90)
    width = length * 0.24
    pts = []
    for i in range(21):
        t = i / 20
        bulge = math.sin(t * math.pi) * width
        pts.append((x + (tip[0] - x) * t + bulge * math.cos(perp),
                    y + (tip[1] - y) * t + bulge * math.sin(perp)))
    for i in range(20, -1, -1):
        t = i / 20
        bulge = math.sin(t * math.pi) * width
        pts.append((x + (tip[0] - x) * t - bulge * math.cos(perp),
                    y + (tip[1] - y) * t - bulge * math.sin(perp)))
    d.polygon(pts, fill=fill)
    d.line([(x, y), tip], fill=LEAF_SHADE, width=3 * SS)


def whole_orange(img):
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = 208 * SS, 648 * SS, 148 * SS
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PEEL + (255,))
    # dimpled peel pores
    rng = random.Random(20261122)
    for _ in range(240):
        a = rng.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(rng.uniform(0, 0.9))
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        d.ellipse([x - 3 * SS, y - 2 * SS, x + 3 * SS, y + 2 * SS],
                  fill=PEEL_PORE + (88,))
    # small highlight on the peel, kept subtle so it never reads as a hole
    d.ellipse([cx - int(r * 0.42), cy - int(r * 0.55),
               cx - int(r * 0.08), cy - int(r * 0.28)],
              fill=(255, 232, 170, 52))
    return img


def halved_orange(img):
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = HALF_CX, HALF_CY, HALF_R
    # rind -> pith -> flesh rings
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PEEL_DEEP)
    r_pith = int(r * 0.95)
    d.ellipse([cx - r_pith, cy - r_pith, cx + r_pith, cy + r_pith],
              fill=PITH)
    r_flesh = int(r * 0.885)
    d.ellipse([cx - r_flesh, cy - r_flesh, cx + r_flesh, cy + r_flesh],
              fill=FLESH_B)
    # ten segments, pale membranes between them
    n = 10
    for i in range(n):
        a0 = (i / n) * 360.0 + 5.0
        a1 = ((i + 1) / n) * 360.0 - 5.0
        col = FLESH_A if i % 2 == 0 else (255, 150, 22)
        d.pieslice([cx - r_flesh, cy - r_flesh, cx + r_flesh, cy + r_flesh],
                   a0, a1, fill=col)
        # juice vesicles: short radial strokes inside the segment
        rng = random.Random(500 + i)
        for _ in range(44):
            am = math.radians(rng.uniform(a0 + 2, a1 - 2))
            rr0 = rng.uniform(0.20, 0.78) * r_flesh
            rr1 = rr0 + rng.uniform(0.06, 0.14) * r_flesh
            d.line([cx + rr0 * math.cos(am), cy + rr0 * math.sin(am),
                    cx + rr1 * math.cos(am), cy + rr1 * math.sin(am)],
                   fill=VESICLE + (150,), width=int(3 * SS))
    # membrane spokes
    for i in range(n):
        a = math.radians(i * 36.0)
        d.line([cx, cy, cx + r_flesh * math.cos(a),
                cy + r_flesh * math.sin(a)],
               fill=PITH + (210,), width=int(2.5 * SS))
    # pale core star
    d.ellipse([cx - 15 * SS, cy - 15 * SS, cx + 15 * SS, cy + 15 * SS],
              fill=PITH)
    # soft sheen, upper left of the cut face
    sheen = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.ellipse([cx - int(r * 0.62), cy - int(r * 0.74),
                cx - int(r * 0.14), cy - int(r * 0.32)],
               fill=(255, 255, 255, 60))
    sheen = sheen.filter(ImageFilter.GaussianBlur(14 * SS))
    return Image.alpha_composite(img, sheen)


def wedge(img):
    """One cut wedge leaning in front, bottom right."""
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = 806 * SS, 798 * SS, 134 * SS
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 170, 290,
               fill=PEEL_DEEP)
    r2 = int(r * 0.90)
    d.pieslice([cx - r2, cy - r2, cx + r2, cy + r2], 174, 286,
               fill=PITH)
    r3 = int(r * 0.82)
    d.pieslice([cx - r3, cy - r3, cx + r3, cy + r3], 178, 282,
               fill=FLESH_A)
    rng = random.Random(77)
    for _ in range(24):
        am = math.radians(rng.uniform(184, 276))
        rr0 = rng.uniform(0.16, 0.60) * r3
        rr1 = rr0 + rng.uniform(0.08, 0.16) * r3
        d.line([cx + rr0 * math.cos(am), cy + rr0 * math.sin(am),
                cx + rr1 * math.cos(am), cy + rr1 * math.sin(am)],
               fill=VESICLE + (170,), width=int(3 * SS))
    return img


def droplets(img):
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(4242)
    for _ in range(64):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.28, 0.86) * HALF_R
        x = HALF_CX + rr * math.cos(a)
        y = HALF_CY + rr * math.sin(a)
        s = rng.uniform(4, 10) * SS
        d.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8],
                  fill=(255, 238, 184, 165))
        d.ellipse([x - s * 0.4, y - s * 0.5, x + s * 0.1, y - s * 0.05],
                  fill=(255, 255, 255, 210))
    return img


def juice_beads(img):
    """Bright juice beads arcing off the cut face, top right."""
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(9182)
    for i in range(30):
        t = i / 29
        x = HALF_CX + HALF_R * 0.72 + 132 * SS * t + rng.uniform(-8, 8) * SS
        y = (HALF_CY - HALF_R * 0.34 - 96 * SS * math.sin(t * math.pi)
             + rng.uniform(-7, 7) * SS)
        s = rng.uniform(3.5, 8.5) * SS
        d.ellipse([x - s, y - s, x + s, y + s],
                  fill=(255, 176, 44, 220))
        d.ellipse([x - s * 0.45, y - s * 0.55, x, y - s * 0.1],
                  fill=(255, 255, 255, 220))
    # a second, lower trail of finer beads falling back toward the table
    for i in range(12):
        t = i / 11
        x = HALF_CX + HALF_R * 0.86 + 96 * SS * t + rng.uniform(-6, 6) * SS
        y = (HALF_CY - HALF_R * 0.10 + 64 * SS * t
             + rng.uniform(-5, 5) * SS)
        s = rng.uniform(2.5, 5.5) * SS
        d.ellipse([x - s, y - s, x + s, y + s],
                  fill=(255, 186, 60, 200))
        d.ellipse([x - s * 0.4, y - s * 0.5, x, y - s * 0.1],
                  fill=(255, 255, 255, 200))
    return img


def warm_vignette(img):
    mask = Image.new("L", (W, W), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-int(W * 0.20), -int(W * 0.24),
                int(W * 1.20), int(W * 1.16)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(80 * SS))
    dark = Image.new("RGBA", (W, W), (90, 36, 4, 255))
    shaded = Image.blend(img, dark, 0.40)
    return Image.composite(img, shaded, mask)


def main():
    img = make_background()
    img = soft_shadow(img)
    img = whole_orange(img)
    d = ImageDraw.Draw(img, "RGBA")
    draw_leaf(d, 252 * SS, 512 * SS, 146 * SS, -40, LEAF)
    draw_leaf(d, 302 * SS, 528 * SS, 118 * SS, -10, LEAF_SHADE)
    img = halved_orange(img)
    d = ImageDraw.Draw(img, "RGBA")
    draw_leaf(d, HALF_CX - 6 * SS, HALF_CY - HALF_R + 12 * SS,
              126 * SS, -118, LEAF_SHADE)
    draw_leaf(d, HALF_CX + 8 * SS, HALF_CY - HALF_R + 8 * SS,
              146 * SS, -58, LEAF)
    img = wedge(img)
    img = droplets(img)
    img = juice_beads(img)
    img = warm_vignette(img)
    img = img.convert("RGB").resize((1024, 1024), Image.LANCZOS)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")
    except PermissionError:
        out_dir = "output"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")
    img.save(out_path, optimize=True)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
