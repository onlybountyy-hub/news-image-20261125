#!/usr/bin/env python3
"""THE WORLD TODAY - v2.

Sums up Wednesday 25 November 2026 world news in one image (1200x675).
Pure Python standard library only. Draws the image itself with its own
bitmap font and writes its own PNG bytes (zlib + struct, no PIL).

Layout: slim masthead naming the day, one dominant hero panel for the
lead story (two oil tankers ablaze in the Strait of Hormuz), and a lower
band with three compact story cards.

Stories (all reported on Wednesday 25 November 2026):
  HERO   - Two oil tankers struck naval mines and caught fire in the
           Strait of Hormuz, Iran's Revolutionary Guard said.
  CARD 1 - A US jury convicted Huawei of trade-secret theft and bank
           fraud; cleared of racketeering.
  CARD 2 - Australia and Solomon Islands signed a treaty barring any
           foreign military base on the islands.
  CARD 3 - Ukrainian drones set two Rosneft refineries ablaze overnight
           in Russia's Samara region.
"""

import math
import os
import struct
import zlib

W, H = 1200, 675

# ---------------------------------------------------------------- palette
PAPER = (247, 241, 227)   # warm paper
CARD = (255, 253, 247)    # card paper
INK = (26, 26, 34)        # dark ink
RED = (179, 38, 30)       # the one accent colour
GREY = (110, 105, 95)     # muted grey
SKY = (238, 228, 205)     # pale sky in the hero scene
SEA = (36, 68, 96)        # deep sea
SEA_LT = (74, 110, 138)   # lighter sea / waves
HULL = (30, 32, 40)       # tanker hull
FLAME = (230, 120, 30)    # flame orange
FLAME_Y = (245, 180, 40)  # flame core
SMOKE = (120, 115, 105)   # smoke grey
SMOKE_D = (88, 84, 78)    # dark smoke

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits. Uppercase newspaper face, drawn fresh.
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
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def text_width(s, scale):
    """Pixel width of s at the given scale (6 units per char, minus 1)."""
    return len(s) * 6 * scale - scale


def wrap(text, max_width, scale):
    """Greedy word wrap; returns a list of lines (already uppercased)."""
    words = text.upper().split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            n = x1 - x0
            self.px[i:i + n * 3] = bytes(c) * n

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def border(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(r * r - dy * dy, 0)))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def poly(self, pts, c):
        """Scanline fill of a polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == "1":
                        self.rect(x + col * scale, y + r * scale,
                                  scale, scale, c)
            x += 6 * scale
        return x

    def text_c(self, cx, y, s, scale, c):
        x = cx - text_width(s.upper(), scale) // 2
        return self.text(x, y, s, scale, c)

    def para(self, x, y, lines, scale, c, leading):
        for ln in lines:
            self.text(x, y, ln, scale, c)
            y += leading
        return y


# ------------------------------------------------------------- hero drawing
def draw_tanker(cv, x, y, w, hull_h, big):
    """A burning oil tanker: hull, bridge tower, funnel, flame, smoke."""
    deck = y
    # smoke column rising from midship, drifting left
    sx = x + int(w * 0.45)
    sy = deck - 6
    r = 26 if big else 18
    for i, (dx, dy, rr, col) in enumerate([
            (0, 0, r, SMOKE_D), (-8, -20, r - 3, SMOKE),
            (-16, -40, r - 6, SMOKE), (-24, -58, r - 9, SMOKE_D),
            (-30, -74, r - 12, SMOKE)]):
        cv.disc(sx + dx, sy + dy, max(rr, 6), col)
    # flame licking from the deck
    fx = x + int(w * 0.45)
    fh = 46 if big else 34
    fw = 34 if big else 24
    cv.poly([(fx - fw // 2, deck), (fx, deck - fh),
             (fx + fw // 2, deck)], FLAME)
    cv.poly([(fx - fw // 4, deck), (fx, deck - fh // 2),
             (fx + fw // 4, deck)], FLAME_Y)
    # hull
    cv.rect(x, deck, w, hull_h, HULL)
    cv.rect(x, deck, w, 4, INK)
    # bridge tower at the stern (right end)
    bx = x + w - (52 if big else 38)
    bw = 52 if big else 38
    bh = 44 if big else 32
    cv.rect(bx, deck - bh, bw, bh, HULL)
    cv.rect(bx, deck - bh, bw, 5, INK)
    for wy in range(deck - bh + 10, deck - 4, 12):
        cv.rect(bx + 6, wy, bw - 12, 4, PAPER)
    # funnel with red band
    fx0 = x + int(w * 0.72)
    cv.rect(fx0, deck - 26, 16, 26, HULL)
    cv.rect(fx0, deck - 26, 16, 7, RED)
    # deck pipes
    cv.rect(x + 12, deck - 8, int(w * 0.3), 4, SEA_LT)


def draw_scene(cv, x0, y0, x1, y1):
    """Sea, sky, two burning tankers in the Strait of Hormuz."""
    cv.rect(x0, y0, x1 - x0, y1 - y0, SKY)
    horizon = y0 + 168
    cv.rect(x0, horizon, x1 - x0, y1 - horizon, SEA)
    cv.hline(x0, horizon, x1 - x0, INK)
    # distant coastline silhouette
    cv.poly([(x0, horizon), (x0 + 90, horizon - 26),
             (x0 + 190, horizon - 8), (x0 + 300, horizon - 30),
             (x0 + 430, horizon - 10), (x1, horizon - 18),
             (x1, horizon)], (96, 92, 82))
    # waves
    for wy, wx, ww in [(horizon + 34, x0 + 24, 90), (horizon + 62, x0 + 150, 120),
                       (horizon + 96, x0 + 40, 80), (horizon + 128, x0 + 260, 140),
                       (horizon + 52, x0 + 380, 70), (horizon + 110, x0 + 330, 90)]:
        cv.rect(wx, wy, ww, 2, SEA_LT)
    # tankers: near one big, far one small
    draw_tanker(cv, x0 + 52, horizon + 58, 250, 40, big=True)
    draw_tanker(cv, x0 + 330, horizon + 78, 165, 30, big=False)
    # foam at the waterline
    cv.rect(x0 + 52, horizon + 98, 250, 2, PAPER)
    cv.rect(x0 + 330, horizon + 108, 165, 2, PAPER)
    # caption tag inside the scene
    tag = "STRAIT OF HORMUZ"
    tw = text_width(tag, 2) + 24
    cv.rect(x0 + 16, y1 - 44, tw, 28, RED)
    cv.text(x0 + 28, y1 - 37, tag, 2, PAPER)


# ------------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)
    # double outer frame
    cv.border(12, 12, W - 24, H - 24, INK, 3)
    cv.border(20, 20, W - 40, H - 40, INK, 1)

    # ---- masthead
    cv.text_c(W // 2, 34, "THE WORLD TODAY", 8, INK)
    cv.rect(40, 100, 300, 3, RED)
    cv.rect(W - 340, 100, 300, 3, RED)
    cv.text_c(W // 2, 96, "WEDNESDAY 25 NOVEMBER 2026", 3, INK)

    # ---- hero panel (dominant, ~60% of the canvas)
    hx0, hy0, hx1, hy1 = 40, 132, 1160, 494
    cv.rect(hx0, hy0, hx1 - hx0, hy1 - hy0, CARD)
    cv.border(hx0, hy0, hx1 - hx0, hy1 - hy0, INK, 2)
    # scene on the left
    sx0, sy0, sx1, sy1 = hx0 + 2, hy0 + 2, 560, hy1 - 2
    draw_scene(cv, sx0, sy0, sx1, sy1)
    cv.vline(sx1, hy0, hy1 - hy0, INK)
    # hero text on the right
    tx, tw = 584, 1160 - 24 - 584
    cv.text(tx, 152, "MIDDLE EAST - LEAD STORY", 3, RED)
    y = 186
    for ln in wrap("TANKERS ABLAZE IN THE STRAIT OF HORMUZ", tw, 5):
        cv.text(tx, y, ln, 5, INK)
        y += 36
    cv.rect(tx, y + 2, tw, 3, RED)
    y += 18
    body1 = wrap("Two oil tankers struck naval mines and caught fire "
                 "in the Strait of Hormuz, Iran's Revolutionary Guard said.",
                 tw, 3)
    body2 = wrap("The blasts raise fears for shipping through a waterway "
                 "carrying a fifth of world oil.", tw, 3)
    y = cv.para(tx, y, body1, 3, INK, 24)
    y += 8
    cv.para(tx, y, body2, 3, INK, 24)

    # ---- lower band: three compact story cards
    cards = [
        ("TECH - UNITED STATES",
         "HUAWEI FOUND GUILTY",
         "A U.S. jury convicts the Chinese tech giant of trade-secret "
         "theft."),
        ("PACIFIC",
         "PACIFIC SECURITY PACT",
         "Australia and the Solomons sign a treaty barring any foreign "
         "military base."),
        ("EUROPE",
         "UKRAINE HITS REFINERIES",
         "Drones set two Rosneft plants ablaze overnight in Russia's "
         "Samara region."),
    ]
    cw, gap = 360, 20
    for i, (kick, head, summ) in enumerate(cards):
        cx0 = 40 + i * (cw + gap)
        cy0, cy1 = 510, 646
        cv.rect(cx0, cy0, cw, cy1 - cy0, CARD)
        cv.border(cx0, cy0, cw, cy1 - cy0, INK, 1)
        cv.rect(cx0, cy0, cw, 5, RED)
        cv.text(cx0 + 16, cy0 + 12, kick, 2, RED)
        y = cy0 + 32
        for ln in wrap(head, cw - 32, 3):
            cv.text(cx0 + 16, y, ln, 3, INK)
            y += 22
        y += 4
        cv.para(cx0 + 16, y, wrap(summ, cw - 32, 2), 2, INK, 16)
    return cv


# ---------------------------------------------------------------------- PNG
def png_bytes(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        i = y * cv.w * 3
        raw += cv.px[i:i + cv.w * 3]

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(build())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path}: {len(data)} bytes, {W}x{H}")


if __name__ == "__main__":
    main()
