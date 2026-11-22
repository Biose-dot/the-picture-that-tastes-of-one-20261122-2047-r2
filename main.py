#!/usr/bin/env python3
"""One Orange -- a halved orange that fills the frame.

Draws a single 1024x1024 picture with the Python standard library only:
no third-party imports, no network, no file reads, fully deterministic.
The image is rendered with span fills (row slices of a bytearray) and a
hand-rolled PNG encoder (zlib + struct), so it runs in well under a
second on one CPU.

Scene: one big halved orange dominates the frame, ten juicy segments
split by pale pith, juice cells catching the light, water droplets on
the cut face, juice bursting from the peel; a whole porous orange with
two green leaves behind it, a wedge leaning in front, a warm cream wall
and a wooden table, warm vignette.
"""

import math
import os
import random
import struct
import sys
import zlib

W = 1024
H = 1024
SEED = 20261122

# ---------------------------------------------------------------- palette
CREAM_TOP = (250, 238, 205)
CREAM_BOT = (243, 224, 178)
WOOD_TOP = (168, 106, 52)
WOOD_BOT = (122, 72, 32)
WOOD_LINE = (96, 54, 22)
RIND = (206, 110, 8)
RIND_DARK = (178, 88, 4)
RIND_LIGHT = (232, 138, 20)
PITH = (252, 240, 200)
FLESH_A = (255, 158, 26)
FLESH_B = (255, 178, 64)
FLESH_DEEP = (244, 130, 12)
JUICE = (255, 214, 130)
JUICE_HI = (255, 240, 190)
DROP = (255, 246, 220)
LEAF = (46, 122, 52)
LEAF_DARK = (28, 84, 34)
LEAF_LIGHT = (86, 164, 74)
PEEL = (240, 140, 18)
PEEL_DARK = (214, 110, 8)

RNG = random.Random(SEED)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def span(self, y, x0, x1, color):
        """Fill [x0, x1) on row y with a solid color."""
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 <= x0:
            return
        r, g, b = color
        base = (y * self.w + x0) * 3
        n = x1 - x0
        self.px[base:base + n * 3] = bytes((r, g, b)) * n

    def blend_span(self, y, x0, x1, color, alpha):
        """Blend a translucent color (alpha 0..255) over [x0, x1) on row y."""
        if y < 0 or y >= self.h or alpha <= 0:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 <= x0:
            return
        r, g, b = color
        inv = 255 - alpha
        px = self.px
        i = (y * self.w + x0) * 3
        for _ in range(x1 - x0):
            px[i] = (px[i] * inv + r * alpha) // 255
            px[i + 1] = (px[i + 1] * inv + g * alpha) // 255
            px[i + 2] = (px[i + 2] * inv + b * alpha) // 255
            i += 3

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            self.span(y, x0, x1, color)

    def hline(self, y, x0, x1, color, alpha=255):
        if alpha >= 255:
            self.span(y, x0, x1, color)
        else:
            self.blend_span(y, x0, x1, color, alpha)

    def disc(self, cx, cy, r, color, alpha=255):
        """Filled circle, integer scanline fill."""
        r = int(r)
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            if alpha >= 255:
                self.span(cy + dy, cx - dx, cx + dx + 1, color)
            else:
                self.blend_span(cy + dy, cx - dx, cx + dx + 1, color, alpha)

    def ring(self, cx, cy, r_out, r_in, color):
        """Filled annulus between r_in and r_out."""
        for dy in range(-int(r_out), int(r_out) + 1):
            y = cy + dy
            if y < 0 or y >= self.h:
                continue
            d2 = r_out * r_out - dy * dy
            if d2 < 0:
                continue
            dxo = int(math.sqrt(d2))
            d2i = r_in * r_in - dy * dy
            if d2i > 0:
                dxi = int(math.sqrt(d2i))
                self.span(y, cx - dxo, cx - dxi, color)
                self.span(y, cx + dxi + 1, cx + dxo + 1, color)
            else:
                self.span(y, cx - dxo, cx + dxo + 1, color)

    def ellipse(self, cx, cy, rx, ry, color, alpha=255):
        for dy in range(-int(ry), int(ry) + 1):
            y = cy + dy
            if y < 0 or y >= self.h:
                continue
            t = 1.0 - (dy * dy) / float(ry * ry)
            if t <= 0:
                continue
            dx = int(rx * math.sqrt(t))
            if alpha >= 255:
                self.span(y, cx - dx, cx + dx + 1, color)
            else:
                self.blend_span(y, cx - dx, cx + dx + 1, color, alpha)

    def poly(self, pts, color, alpha=255):
        """Scanline fill of a simple polygon (list of (x, y))."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = int(min(ys)), int(max(ys))
        n = len(pts)
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            xs = []
            for i in range(n):
                x1, yy1 = pts[i]
                x2, yy2 = pts[(i + 1) % n]
                if yy1 == yy2:
                    continue
                if (yy1 <= y < yy2) or (yy2 <= y < yy1):
                    xs.append(x1 + (y - yy1) * (x2 - x1) / (yy2 - yy1))
            if len(xs) < 2:
                continue
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa, xb = int(xs[k]), int(xs[k + 1]) + 1
                if alpha >= 255:
                    self.span(y, xa, xb, color)
                else:
                    self.blend_span(y, xa, xb, color, alpha)

    def thick_line(self, x0, y0, x1, y1, color, width, alpha=255):
        """Short line drawn as a chain of small discs (cheap DDA)."""
        dx = x1 - x0
        dy = y1 - y0
        steps = int(max(abs(dx), abs(dy))) + 1
        r = max(1, width // 2)
        for s in range(steps + 1):
            t = s / float(steps)
            x = int(x0 + dx * t)
            y = int(y0 + dy * t)
            self.disc(x, y, r, color, alpha)

    def radial_line(self, cx, cy, ang, r0, r1, color, width, alpha=255):
        x0 = int(cx + r0 * math.cos(ang))
        y0 = int(cy + r0 * math.sin(ang))
        x1 = int(cx + r1 * math.cos(ang))
        y1 = int(cy + r1 * math.sin(ang))
        self.thick_line(x0, y0, x1, y1, color, width, alpha)


# ---------------------------------------------------------------- scene
def draw_background(cv):
    # Warm cream wall, gently darker toward the top.
    for y in range(0, 668):
        t = y / 668.0
        cv.span(y, 0, W, mix(CREAM_TOP, CREAM_BOT, t))
    # Wooden table with plank seams.
    for y in range(668, H):
        t = (y - 668) / float(H - 668)
        cv.span(y, 0, W, mix(WOOD_TOP, WOOD_BOT, t))
    for py in (668, 776, 884, 992):
        cv.span(py, 0, W, WOOD_LINE)
        cv.span(py + 1, 0, W, mix(WOOD_LINE, WOOD_TOP, 0.45))
    # Soft shadow where the fruit will sit.
    cv.ellipse(512, 872, 430, 46, (60, 30, 8), alpha=70)
    cv.ellipse(180, 880, 150, 30, (60, 30, 8), alpha=60)


def draw_leaf(cv, tip_x, tip_y, base_x, base_y, lean):
    """A pointed leaf from base to tip, bowed by `lean` pixels."""
    mx = (tip_x + base_x) // 2 + lean
    my = (tip_y + base_y) // 2
    wdt = 52
    # Leaf body: two curved edges approximated by a polygon.
    pts = []
    for s in range(0, 11):
        t = s / 10.0
        x = int(lerp(base_x, tip_x, t))
        y = int(lerp(base_y, tip_y, t))
        off = int(math.sin(t * math.pi) * wdt)
        # perpendicular offset
        px = -math.sin(math.atan2(tip_y - base_y, tip_x - base_x))
        py = math.cos(math.atan2(tip_y - base_y, tip_x - base_x))
        pts.append((x + int(px * off), y + int(py * off)))
    for s in range(10, -1, -1):
        t = s / 10.0
        x = int(lerp(base_x, tip_x, t))
        y = int(lerp(base_y, tip_y, t))
        off = int(math.sin(t * math.pi) * wdt)
        px = -math.sin(math.atan2(tip_y - base_y, tip_x - base_x))
        py = math.cos(math.atan2(tip_y - base_y, tip_x - base_x))
        pts.append((x - int(px * off), y - int(py * off)))
    cv.poly(pts, LEAF)
    # Vein down the middle.
    cv.thick_line(base_x, base_y, tip_x, tip_y, LEAF_DARK, 4)
    # Light catching the upper edge.
    cv.thick_line(base_x, base_y, mx, my, LEAF_LIGHT, 5, alpha=90)


def draw_whole_orange(cv, cx, cy, r):
    """A whole orange with dimpled peel, sitting behind the halved one."""
    # Radial shading: concentric discs, darker at the rim.
    steps = 26
    for i in range(steps, 0, -1):
        t = i / float(steps)
        col = mix(PEEL_DARK, PEEL, t * t)
        cv.disc(cx, cy, int(r * t), col)
    # Warm highlight upper left, kept soft so the peel still reads.
    cv.ellipse(cx - int(r * 0.34), cy - int(r * 0.38), int(r * 0.42),
               int(r * 0.30), (255, 196, 110), alpha=55)
    cv.ellipse(cx - int(r * 0.30), cy - int(r * 0.34), int(r * 0.18),
               int(r * 0.12), (255, 222, 160), alpha=70)
    # Dimples: deterministic speckle of tiny darker pores.
    for _ in range(320):
        ang = RNG.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(RNG.uniform(0.05, 0.97))
        x = int(cx + rr * math.cos(ang))
        y = int(cy + rr * math.sin(ang))
        pr = RNG.choice((1, 1, 2, 2, 3))
        col = PEEL_DARK if RNG.random() < 0.7 else RIND_LIGHT
        cv.disc(x, y, pr, col, alpha=RNG.randint(90, 170))
    # Stem nub.
    cv.disc(cx + 6, cy - r + 4, 7, (122, 84, 40))


def draw_halved_orange(cv, cx, cy, r):
    """The hero: one halved orange filling the frame."""
    # Outer rind with a light rim on the sun side.
    cv.disc(cx, cy, r, RIND)
    cv.ring(cx, cy, r, int(r * 0.985), RIND_LIGHT)
    cv.disc(cx, cy, int(r * 0.965), RIND_DARK)
    # Pale pith ring.
    cv.disc(cx, cy, int(r * 0.90), PITH)
    # Flesh: radial shading, deeper at the rim, glowing near the heart.
    fr = int(r * 0.865)
    steps = 30
    for i in range(steps, 0, -1):
        t = i / float(steps)
        col = mix(FLESH_DEEP, FLESH_A, t)
        if t > 0.55:
            col = mix(FLESH_A, FLESH_B, (t - 0.55) / 0.45)
        cv.disc(cx, cy, int(fr * t), col)
    # Ten segments, split by pale pith spokes.
    nseg = 10
    for k in range(nseg):
        ang = (k / nseg) * 2 * math.pi - math.pi / 2
        cv.radial_line(cx, cy, ang, int(fr * 0.06), fr, PITH, 13)
    # Juice cells: short bright radial streaks inside each segment.
    for k in range(nseg):
        a0 = (k / nseg) * 2 * math.pi - math.pi / 2
        a1 = ((k + 1) / nseg) * 2 * math.pi - math.pi / 2
        for _ in range(64):
            ang = RNG.uniform(a0 + 0.09, a1 - 0.09)
            r0 = RNG.uniform(fr * 0.16, fr * 0.80)
            ln = RNG.uniform(14, 62)
            r1 = min(fr * 0.97, r0 + ln)
            w = RNG.choice((2, 2, 3))
            col = JUICE_HI if RNG.random() < 0.35 else JUICE
            cv.radial_line(cx, cy, ang, int(r0), int(r1), col, w,
                           alpha=RNG.randint(110, 210))
    # A few longer glossy streaks catching the light, upper half.
    for _ in range(26):
        ang = RNG.uniform(-2.6, -0.5)
        r0 = RNG.uniform(fr * 0.2, fr * 0.55)
        cv.radial_line(cx, cy, ang, int(r0), int(r0 + RNG.uniform(60, 120)),
                       JUICE_HI, 3, alpha=200)
    # Pale heart at the centre.
    cv.disc(cx, cy, 16, PITH)
    cv.disc(cx, cy, 9, (255, 248, 225))
    # Water droplets resting on the cut face.
    for _ in range(46):
        ang = RNG.uniform(0, 2 * math.pi)
        rr = fr * math.sqrt(RNG.uniform(0.08, 0.92))
        x = int(cx + rr * math.cos(ang))
        y = int(cy + rr * math.sin(ang))
        dr = RNG.randint(3, 8)
        cv.disc(x, y, dr, DROP, alpha=150)
        cv.disc(x - dr // 3, y - dr // 3, max(1, dr // 3),
                (255, 255, 255), alpha=220)
    # Gloss highlight sweeping the upper-left flesh.
    cv.ellipse(cx - int(fr * 0.42), cy - int(fr * 0.46), int(fr * 0.34),
               int(fr * 0.20), (255, 226, 160), alpha=95)


def draw_wedge(cv, cx, cy, r, tilt):
    """A small wedge leaning in front, cut face up."""
    # Rind arc (half disc, tilted).
    pts = []
    for s in range(0, 25):
        ang = math.pi + s * (math.pi / 24.0) + tilt
        pts.append((int(cx + r * math.cos(ang)),
                    int(cy + r * math.sin(ang))))
    pts.append((cx, cy))
    cv.poly(pts, RIND)
    pts2 = []
    for s in range(0, 25):
        ang = math.pi + s * (math.pi / 24.0) + tilt
        pts2.append((int(cx + int(r * 0.93) * math.cos(ang)),
                     int(cy + int(r * 0.93) * math.sin(ang))))
    pts2.append((cx, cy))
    cv.poly(pts2, PITH)
    pts3 = []
    for s in range(0, 25):
        ang = math.pi + s * (math.pi / 24.0) + tilt
        pts3.append((int(cx + int(r * 0.86) * math.cos(ang)),
                     int(cy + int(r * 0.86) * math.sin(ang))))
    pts3.append((cx, cy))
    cv.poly(pts3, FLESH_A)
    # Segment spokes on the wedge.
    for k in range(1, 6):
        ang = math.pi + (k / 6.0) * math.pi + tilt
        cv.radial_line(cx, cy, ang, 8, int(r * 0.84), PITH, 5)
    # Juice streaks on the wedge.
    for _ in range(40):
        ang = math.pi + RNG.uniform(0.15, math.pi - 0.15) + tilt
        r0 = RNG.uniform(r * 0.2, r * 0.6)
        cv.radial_line(cx, cy, ang, int(r0), int(r0 + RNG.uniform(12, 34)),
                       JUICE, 2, alpha=180)


def draw_juice_spray(cv):
    """Juice bursting from the peel at the right edge."""
    ox, oy = 856, 400
    for i in range(60):
        t = i / 60.0
        ang = -0.45 + t * 1.0
        dist = 24 + t * 118 + RNG.uniform(-6, 6)
        x = int(ox + dist * math.cos(ang) + RNG.uniform(-8, 8))
        y = int(oy + dist * math.sin(ang) * 0.7 + RNG.uniform(-8, 8))
        pr = max(1, int(5 - t * 3))
        cv.disc(x, y, pr, JUICE_HI if i % 3 == 0 else JUICE,
                alpha=RNG.randint(140, 230))
    cv.disc(ox, oy, 7, JUICE_HI, alpha=230)
    cv.disc(ox - 2, oy - 2, 3, (255, 255, 255), alpha=220)


def draw_vignette(cv):
    """Warm darkening toward the corners, in soft blended bands."""
    for i in range(1, 13):
        # Darkest at the outer edge, fading to nothing toward the centre.
        a = max(2, 46 - i * 4)
        inset = i * 9
        col = (74, 40, 8)
        for y in range(inset - 9, inset):
            cv.blend_span(y, inset, W - inset, col, a)
        for y in range(H - inset, H - inset + 9):
            cv.blend_span(y, inset, W - inset, col, a)
        for y in range(inset, H - inset):
            cv.blend_span(y, inset - 9, inset, col, a)
            cv.blend_span(y, W - inset, W - inset + 9, col, a)


def render():
    cv = Canvas(W, H)
    draw_background(cv)
    # Whole orange behind, lower left.
    draw_whole_orange(cv, 168, 742, 168)
    # Two leaves crowning the halved orange.
    draw_leaf(cv, 428, 22, 512, 128, -38)
    draw_leaf(cv, 636, 30, 528, 128, 42)
    # Stem.
    cv.thick_line(516, 118, 522, 140, (122, 84, 40), 7)
    # Hero halved orange.
    draw_halved_orange(cv, 512, 512, 372)
    # Wedge leaning in front, lower right.
    draw_wedge(cv, 812, 884, 118, 0.12)
    # Juice bursting from the peel.
    draw_juice_spray(cv)
    # Warm vignette to pull the eye to the fruit.
    draw_vignette(cv)
    return cv


# ---------------------------------------------------------------- PNG encode
def png_bytes(cv):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: None
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


def out_dir():
    d = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if d:
        return d
    if os.path.isdir("/output"):
        return "/output"
    return os.path.join(".", "output")


def main():
    cv = render()
    data = png_bytes(cv)
    d = out_dir()
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
