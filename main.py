#!/usr/bin/env python3
"""news-image-20261125 v5: one image summing up Wednesday 25 November 2026.

Pure Python standard library only. Draws a 1024x1024 editorial front page
with five verified stories of the day and writes it to entry.png.
Deterministic: two runs produce byte-identical PNGs.
"""
import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# --- restrained palette: paper, ink, slate + one accent (hero only) ---
PAPER = (245, 239, 224)
CARD = (255, 255, 255)
INK = (22, 35, 61)
SEA = (46, 74, 107)
SLATE = (92, 107, 128)
ACCENT = (192, 57, 43)
SHADOW = (226, 219, 198)
GRAIN = (214, 205, 180)

# --- 5x7 pixel font (caps, digits, space, hyphen, dollar) ---
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return (self.px[i], self.px[i + 1], self.px[i + 2])

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def outline(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            for xx in (cx - dx, cx + dx - t + 1):
                self.rect(xx, cy + dy, t, 1, c)
        for dx in range(-r, r + 1):
            dy = int(math.sqrt(max(0, r * r - dx * dx)))
            for yy in (cy - dy, cy + dy - t + 1):
                self.rect(cx + dx, yy, 1, t, c)

    def poly(self, pts, c):
        # scanline fill of a simple polygon
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(math.ceil(xs[i])), y,
                          int(math.floor(xs[i + 1])) - int(math.ceil(xs[i])) + 1, 1, c)

    def line(self, x1, y1, x2, y2, c, t=1):
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            x = x1 + dx * i // steps
            y = y1 + dy * i // steps
            self.rect(x - t // 2, y - t // 2, t, t, c)

    def text(self, x, y, s, scale, c, adv=None):
        if adv is None:
            adv = 5 * scale + scale
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == "1":
                        self.rect(cx + col * scale, y + r * scale, scale, scale, c)
            cx += adv
        return cx - x

    def text_w(self, s, scale, adv=None):
        if adv is None:
            adv = 5 * scale + scale
        if not s:
            return 0
        return (len(s) - 1) * adv + 5 * scale


def chip(cv, x, y, s, scale=5, adv=25, fill=None, fg=None, border=None):
    """A labelled chip; text height 35px (>=31px floor)."""
    pad_x = 7
    w = cv.text_w(s, scale, adv) + pad_x * 2
    h = 40
    if fill is not None:
        cv.rect(x, y, w, h, fill)
    if border is not None:
        cv.outline(x, y, w, h, border, 2)
    ty = y + (h - 7 * scale) // 2
    cv.text(x + pad_x, ty, s, scale, fg, adv)
    return w


def grain(cv):
    # deterministic paper grain: fixed-seed LCG, sparse speckles
    state = 1234567
    for _ in range(3600):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        x = state % W
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        y = state % H
        if cv.get(x, y) == PAPER:
            cv.set(x, y, GRAIN)


# ---------- flat silhouette scenes (one per module) ----------

def scene_hormuz(cv, x0, y0, w, h):
    """Narrow strait / chokepoint: two land masses, two tankers, mines."""
    cv.rect(x0, y0, w, h, SEA)
    # north shore (paper) sloping down to the channel
    cv.poly([(x0, y0), (x0 + 616, y0), (x0 + 536, y0 + 24),
             (x0 + 376, y0 + 32), (x0, y0 + 32)], PAPER)
    # south shore (paper) rising from the bottom
    cv.poly([(x0 + 396, y0 + h), (x0 + 536, y0 + 60), (x0 + 736, y0 + 52),
             (x0 + w, y0 + 44), (x0 + w, y0 + h)], PAPER)
    # mines: spiked circles in the channel (clear of the sub-line)
    for mx, my in ((x0 + 560, y0 + 42), (x0 + 604, y0 + 50)):
        cv.circle(mx, my, 6, INK)
        for dx, dy in ((-9, 0), (9, 0), (0, -9), (0, 9), (-6, -6), (6, -6),
                       (-6, 6), (6, 6)):
            cv.line(mx, my, mx + dx, my + dy, INK, 2)
    # tanker 1
    tx, ty = x0 + 276, y0 + 32
    cv.rect(tx, ty, 110, 12, PAPER)
    cv.poly([(tx + 110, ty), (tx + 124, ty + 6), (tx + 110, ty + 12)], PAPER)
    cv.rect(tx + 18, ty - 10, 16, 10, PAPER)
    cv.rect(tx + 78, ty - 7, 8, 7, PAPER)
    # flame 1 (accent, hero only)
    cv.poly([(tx + 44, ty - 8), (tx + 56, ty - 30), (tx + 68, ty - 8)], ACCENT)
    cv.poly([(tx + 50, ty - 8), (tx + 56, ty - 20), (tx + 62, ty - 8)], PAPER)
    # tanker 2
    tx, ty = x0 + 430, y0 + 40
    cv.rect(tx, ty, 96, 12, PAPER)
    cv.poly([(tx + 96, ty), (tx + 108, ty + 6), (tx + 96, ty + 12)], PAPER)
    cv.rect(tx + 14, ty - 9, 14, 9, PAPER)
    cv.rect(tx + 66, ty - 6, 7, 6, PAPER)
    cv.poly([(tx + 36, ty - 7), (tx + 47, ty - 26), (tx + 58, ty - 7)], ACCENT)
    cv.poly([(tx + 41, ty - 7), (tx + 47, ty - 18), (tx + 53, ty - 7)], PAPER)
    # smoke puffs
    for sx, sy, r in ((x0 + 332, y0 + 8, 5), (x0 + 348, y0 + 2, 4),
                      (x0 + 477, y0 + 12, 5), (x0 + 491, y0 + 5, 4)):
        cv.circle(sx, sy, r, SLATE)


def scene_court(cv, x0, y0, w, h):
    """Courthouse facade: pediment, columns, steps."""
    base = y0 + h - 4
    cv.poly([(x0 + 150, y0 + 2), (x0 + 294, y0 + 2), (x0 + 222, y0 + 16)], INK)
    cv.rect(x0 + 156, y0 + 16, 132, 3, INK)
    for cx in (x0 + 166, x0 + 198, x0 + 230, x0 + 262):
        cv.rect(cx, y0 + 19, 9, h - 26, INK)
    cv.rect(x0 + 150, base - 3, 144, 3, INK)
    cv.rect(x0 + 142, base, 160, 3, SLATE)


def scene_palm(cv, x0, y0, w, h):
    """Palm tree + signed treaty document."""
    # palm
    cv.line(x0 + 60, y0 + h - 2, x0 + 72, y0 + 8, INK, 4)
    for fx, fy, tx, ty in ((72, 10, 40, 2), (72, 10, 52, 0), (72, 10, 96, 0),
                           (72, 10, 106, 6), (72, 10, 88, 16)):
        cv.line(x0 + fx, y0 + fy, x0 + tx, y0 + ty, INK, 3)
    cv.circle(x0 + 66, y0 + 12, 3, INK)
    cv.circle(x0 + 74, y0 + 13, 3, INK)
    # document with seal
    dx = x0 + 250
    cv.rect(dx, y0 + 4, 130, h - 8, CARD)
    cv.outline(dx, y0 + 4, 130, h - 8, INK, 2)
    for i, ly in enumerate((12, 20, 28)):
        cv.rect(dx + 10, y0 + ly, 86 - i * 18, 2, SLATE)
    cv.circle(dx + 104, y0 + h - 14, 8, INK)
    cv.circle(dx + 104, y0 + h - 14, 4, CARD)


def scene_rocket(cv, x0, y0, w, h):
    """Rocket climbing past stars toward a ringed planet."""
    for sx, sy in ((x0 + 30, y0 + 8), (x0 + 390, y0 + 6), (x0 + 420, y0 + 26),
                   (x0 + 60, y0 + 30), (x0 + 350, y0 + 34)):
        cv.rect(sx, sy, 3, 3, INK)
        cv.rect(sx + 1, sy - 2, 1, 7, INK)
        cv.rect(sx - 2, sy + 1, 7, 1, INK)
    # ringed planet
    cv.circle(x0 + 398, y0 + 16, 9, SLATE)
    cv.line(x0 + 382, y0 + 22, x0 + 414, y0 + 10, INK, 2)
    # rocket body (diagonal)
    cv.poly([(x0 + 196, y0 + 30), (x0 + 210, y0 + 22), (x0 + 232, y0 + 4),
             (x0 + 240, y0 + 10), (x0 + 218, y0 + 30), (x0 + 206, y0 + 38)],
            INK)
    cv.poly([(x0 + 196, y0 + 30), (x0 + 188, y0 + 34), (x0 + 200, y0 + 40)],
            INK)
    cv.poly([(x0 + 206, y0 + 38), (x0 + 212, y0 + 46), (x0 + 218, y0 + 38)],
            INK)
    # exhaust flame (ink/slate: accent stays in the hero)
    cv.poly([(x0 + 196, y0 + 34), (x0 + 186, y0 + 40), (x0 + 198, y0 + 40)],
            SEA)
    cv.circle(x0 + 214, y0 + 30, 3, CARD)


def scene_refinery(cv, x0, y0, w, h):
    """Refinery columns + chimney flame + rising oil line."""
    base = y0 + h - 2
    for cx, cw, ch in ((x0 + 30, 26, 22), (x0 + 66, 20, 30),
                       (x0 + 96, 30, 18), (x0 + 136, 16, 26)):
        cv.rect(cx, base - ch, cw, ch, INK)
    cv.rect(x0 + 170, base - 34, 10, 34, INK)
    cv.poly([(x0 + 168, base - 34), (x0 + 175, base - 42),
             (x0 + 182, base - 34)], SEA)
    cv.rect(x0 + 20, base - 2, 170, 2, SLATE)
    # rising chart line with arrow
    pts = [(x0 + 230, base - 4), (x0 + 270, base - 14), (x0 + 310, base - 10),
           (x0 + 350, base - 24), (x0 + 390, base - 32)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], INK, 3)
    cv.poly([(x0 + 390, base - 32), (x0 + 378, base - 30),
             (x0 + 388, base - 40)], INK)
    for px, py in pts:
        cv.circle(px, py, 3, INK)


# ---------- page ----------

def draw():
    cv = Canvas(W, H, PAPER)
    grain(cv)

    # masthead: date anchor x1
    cv.rect(24, 14, 976, 3, INK)
    date = "WEDNESDAY 25 NOVEMBER 2026"
    dw = cv.text_w(date, 5, 30)
    cv.text((W - dw) // 2, 30, date, 5, INK, 30)
    cv.rect(24, 82, 976, 3, INK)
    cv.rect(24, 88, 976, 2, SLATE)

    # hero shadow first, so it never stripes the cards below
    cv.rect(24 + 6, 108 + 6, 976, 388, SHADOW)

    # ---- grid cards (hero panel overlaps their tops: the flourish)
    cards = [
        # (col, row, scene, headline lines, sub, region, field, extra)
        (0, 0, scene_court, ["HUAWEI GUILTY", "IN NEW YORK"], "10 OF 12",
         "USA", "LAW-TECH", "25 NOV"),
        (1, 0, scene_palm, ["SOLOMONS SIGNS", "TREATY WITH", "CANBERRA"],
         "$740M", "PACIFIC", "DIPLOMACY", None),
        (0, 1, scene_rocket, ["PAKISTAN FIRST", "ASTRONAUT", "REACHES TIANGONG"],
         "SHENZHOU-24", "ASIA", "SPACE", None),
        (1, 1, scene_refinery, ["OIL RISES AS", "REFINERIES", "BURN"],
         "2 PLANTS HIT", "EUROPE", "MARKETS", None),
    ]
    for col, row, scene, lines, sub, region, field, extra in cards:
        cx = 24 + col * 500
        cy = 488 + row * 258
        cv.rect(cx + 6, cy + 6, 476, 250, SHADOW)
        cv.rect(cx, cy, 476, 250, CARD)
        cv.outline(cx, cy, 476, 250, INK, 2)
        scene(cv, cx + 16, cy + 6, 444, 40)
        ly = cy + 52
        for ln in lines:
            cv.text(cx + 16, ly, ln, 5, INK, 27)
            ly += 36
        cv.text(cx + 16, cy + 165, sub, 5, SLATE, 29)
        if extra:
            ew = cv.text_w(extra, 5, 25) + 14
            chip(cv, cx + 460 - ew, cy + 163, extra, fill=ACCENT, fg=PAPER)
        chw = chip(cv, cx + 16, cy + 206, region, fill=INK, fg=PAPER)
        chip(cv, cx + 16 + chw + 8, cy + 206, field, fill=None, fg=INK,
             border=INK)

    # ---- hero panel (drawn last so it overlaps the grid top)
    hx, hy, hw, hh = 24, 108, 976, 388
    cv.rect(hx, hy, hw, hh, INK)
    scene_hormuz(cv, hx, hy, hw, 88)
    # hero chips stacked at the right of the strait band
    chip(cv, hx + 624, hy + 4, "MIDDLE EAST", fill=PAPER, fg=INK)
    chip(cv, hx + 624, hy + 48, "CONFLICT", fill=PAPER, fg=INK)
    # sub-line on the sea, bottom-left of the band
    cv.text(hx + 12, hy + 46, "TWO HIT MINES", 5, PAPER, 29)
    # hero headline, 84px tall (8.2% of canvas width)
    hl = ["TANKERS BURN", "IN THE STRAIT", "OF HORMUZ"]
    hyy = hy + 96
    for ln in hl:
        cv.text(hx + 24, hyy, ln, 12, PAPER, 66)
        hyy += 86
    # date plate x2, red chip right of the last headline line
    chip(cv, hx + 628, hy + 280, "25 NOV", fill=ACCENT, fg=PAPER)

    return cv


def write_png(path, cv):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    cv = draw()
    write_png(os.path.join(outdir, "entry.png"), cv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
