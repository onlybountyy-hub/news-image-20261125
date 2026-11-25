#!/usr/bin/env python3
"""news-image-20261125 v3 — one-day world news image, drawn from scratch.

Pure Python standard library only. Draws a 1024x1024 newspaper front page
for Wednesday 25 November 2026: masthead, hero scene of tankers burning in
the Strait of Hormuz, and three story cards (Huawei, Pacific Pact, Ukraine
refineries), each with its own picture. Writes entry.png into
$MAKEFUN_OUTPUT_DIR. Deterministic: same bytes every run.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette ---
PAPER = (247, 239, 223)   # warm paper
INK = (26, 26, 38)        # dark ink
CARD = (255, 253, 246)    # card paper
ACCENT = (196, 48, 32)    # brick red
GOLD = (212, 160, 32)     # date gold
SKY1 = (228, 87, 46)      # dusk orange top
SKY2 = (240, 138, 60)
SKY3 = (247, 178, 103)
SKY4 = (249, 217, 118)    # horizon pale
SEA = (15, 59, 76)        # deep sea
SEA2 = (30, 107, 122)     # wave light
HULL = (31, 42, 51)       # tanker hull
HULLRED = (150, 40, 28)   # hull waterline stripe
SUPER = (238, 234, 222)   # superstructure
FLAME_Y = (255, 210, 63)
FLAME_O = (255, 122, 26)
FLAME_R = (215, 38, 61)
SMOKE = (90, 90, 92)
SMOKE2 = (120, 120, 122)
SUN = (255, 243, 196)
NAVY = (18, 38, 66)      # card 1 background
CHIP = (212, 160, 32)
PHONE = (38, 44, 58)
OCEAN = (44, 125, 160)   # card 2 background
ISLAND = (74, 140, 74)
DUSK = (52, 44, 74)      # card 3 background
STEEL = (70, 76, 92)
WHITE = (255, 255, 255)

# ------------------------------------------------------------- bitmap font --
# 5x7 uppercase font, drawn from memory. '#' = on.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_chars):
    words = text.split(' ')
    lines, cur = [], ''
    for w in words:
        cand = (cur + ' ' + w).strip()
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ canvas --
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg[0] for _ in range(w * h * 3))
        # fill properly (bytearray above repeats only first channel); redo:
        buf = bytearray(w * h * 3)
        for i in range(w * h):
            buf[i * 3] = bg[0]
            buf[i * 3 + 1] = bg[1]
            buf[i * 3 + 2] = bg[2]
        self.px = buf

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            for x in range(x0, x1):
                i = base + (x - x0) * 3
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def rect_border(self, x0, y0, x1, y1, c, t=2):
        self.fill_rect(x0, y0, x1, y0 + t, c)
        self.fill_rect(x0, y1 - t, x1, y1, c)
        self.fill_rect(x0, y0, x0 + t, y1, c)
        self.fill_rect(x1 - t, y0, x1, y1, c)

    def hline(self, x0, x1, y, c, t=1):
        self.fill_rect(x0, y, x1, y + t, c)

    def vline(self, x, y0, y1, c, t=1):
        self.fill_rect(x, y0, x + t, y1, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - t // 2, y - t // 2, x + t // 2 + 1, y + t // 2 + 1, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r:
                    self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) * (x - cx)) * ry * ry + ((y - cy) * (y - cy)) * rx * rx <= rx * rx * ry * ry:
                    self.set(x, y, c)

    def triangle(self, p0, p1, p2, c):
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]
        ymin, ymax = min(ys), max(ys)
        pts = sorted(zip(xs, ys), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        for y in range(ymin, ymax + 1):
            xa = ax + (cx - ax) * (y - ay) / (cy - ay) if cy != ay else ax
            if y < by:
                xb = ax + (bx - ax) * (y - ay) / (by - ay) if by != ay else ax
            else:
                xb = bx + (cx - bx) * (y - by) / (cy - by) if cy != by else bx
            x0, x1 = int(min(xa, xb)), int(max(xa, xb))
            self.fill_rect(x0, y, x1 + 1, y + 1, c)

    def polygon(self, pts, c):
        ymin = min(p[1] for p in pts)
        ymax = max(p[1] for p in pts)
        n = len(pts)
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[j]), y, int(xs[j + 1]) + 1, y + 1, c)

    def text(self, x, y, s, scale, c):
        for ch in s:
            g = FONT.get(ch.upper(), FONT[' '])
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == '1':
                        self.fill_rect(x + col * scale, y + r * scale,
                                       x + (col + 1) * scale, y + (r + 1) * scale, c)
            x += 6 * scale

    def text_center(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)


# -------------------------------------------------------------- PNG writer --
def chunk(ctype, data):
    out = struct.pack('>I', len(data)) + ctype + data
    out += struct.pack('>I', zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    data = b'\x89PNG\r\n\x1a\n'
    data += chunk(b'IHDR', ihdr)
    data += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    data += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(data)
    return len(data)


# ------------------------------------------------------------------ scenes --
def flame(cv, x, base_y, hgt, wdt):
    """A layered flame tongue rising from (x, base_y)."""
    cv.triangle((x - wdt, base_y), (x + wdt, base_y), (x, base_y - hgt), FLAME_R)
    cv.triangle((x - int(wdt * 0.65), base_y), (x + int(wdt * 0.65), base_y),
                (x, base_y - int(hgt * 0.72)), FLAME_O)
    cv.triangle((x - int(wdt * 0.35), base_y), (x + int(wdt * 0.35), base_y),
                (x, base_y - int(hgt * 0.45)), FLAME_Y)


def smoke_puff(cv, x, y, r, c):
    cv.circle(x, y, r, c)
    cv.circle(x + r // 2, y - r // 3, int(r * 0.7), c)


def draw_hero(cv, x0, y0, x1, y1):
    """Burning tankers in the Strait of Hormuz at dusk. Scene area only."""
    w = x1 - x0
    horizon = y0 + int((y1 - y0) * 0.58)
    # sky bands
    bands = [(SKY1, 0.30), (SKY2, 0.55), (SKY3, 0.80), (SKY4, 1.0)]
    prev = y0
    for col, frac in bands:
        yy = y0 + int((horizon - y0) * frac)
        cv.fill_rect(x0, prev, x1, yy, col)
        prev = yy
    # low sun, right side, half veiled by smoke
    cv.circle(x0 + int(w * 0.82), y0 + 78, 52, SUN)
    cv.circle(x0 + int(w * 0.82), y0 + 78, 38, (255, 248, 220))
    # distant tanker silhouette, left
    cv.fill_rect(x0 + 70, horizon - 26, x0 + 300, horizon - 6, (35, 49, 64))
    cv.fill_rect(x0 + 210, horizon - 52, x0 + 252, horizon - 26, (35, 49, 64))
    cv.fill_rect(x0 + 96, horizon - 40, x0 + 118, horizon - 26, (35, 49, 64))
    # sea
    cv.fill_rect(x0, horizon, x1, y1, SEA)
    # wave strokes
    for i, yy in enumerate(range(horizon + 14, y1 - 8, 22)):
        xoff = (i * 53) % 160
        cv.hline(x0 + 40 + xoff, x0 + 150 + xoff, yy, SEA2, 3)
        cv.hline(x0 + 430 + ((i * 91) % 220), x0 + 560 + ((i * 91) % 220), yy + 10, SEA2, 3)
    # fire glow reflection on the sea under the flames
    for i in range(6):
        cv.hline(x0 + 400 + i * 8, x0 + 620 - i * 8, horizon + 16 + i * 12,
                 (255, 122, 26) if i % 2 == 0 else (255, 178, 60), 4)
    # main tanker: hull with raked bow, red waterline, white superstructure
    deck = horizon + 52
    cv.polygon([(x0 + 170, deck), (x0 + 800, deck), (x0 + 880, deck + 26),
                (x0 + 860, deck + 62), (x0 + 190, deck + 62)], HULL)
    cv.polygon([(x0 + 800, deck), (x0 + 880, deck + 26), (x0 + 860, deck + 62),
                (x0 + 800, deck + 62)], (22, 30, 38))
    cv.fill_rect(x0 + 170, deck + 46, x0 + 866, deck + 62, HULLRED)
    # deck cargo: low tanks and pipes
    cv.fill_rect(x0 + 220, deck - 26, x0 + 330, deck, (52, 62, 76))
    cv.fill_rect(x0 + 620, deck - 22, x0 + 720, deck, (52, 62, 76))
    cv.ellipse(x0 + 275, deck - 26, 52, 12, (70, 82, 96))
    cv.ellipse(x0 + 670, deck - 22, 46, 10, (70, 82, 96))
    # superstructure + funnel
    cv.fill_rect(x0 + 730, deck - 78, x0 + 800, deck, SUPER)
    for wx in (740, 760, 780):
        cv.fill_rect(wx, deck - 70, wx + 12, deck - 54, INK)
    cv.fill_rect(x0 + 756, deck - 24, x0 + 774, deck, INK)
    cv.fill_rect(x0 + 806, deck - 96, x0 + 838, deck - 34, ACCENT)
    cv.fill_rect(x0 + 806, deck - 96, x0 + 838, deck - 80, INK)
    # mast
    cv.vline(x0 + 340, deck - 84, deck, INK, 4)
    cv.hline(x0 + 322, x0 + 358, deck - 84, INK, 4)
    # flames bursting from mid-deck
    flame(cv, x0 + 430, deck, 150, 46)
    flame(cv, x0 + 500, deck, 190, 58)
    flame(cv, x0 + 575, deck, 140, 42)
    flame(cv, x0 + 380, deck, 90, 30)
    flame(cv, x0 + 640, deck, 80, 28)
    # smoke column drifting up and right (kept inside the scene)
    smoke_puff(cv, x0 + 470, deck - 150, 30, SMOKE)
    smoke_puff(cv, x0 + 520, deck - 185, 34, SMOKE2)
    smoke_puff(cv, x0 + 590, deck - 210, 40, SMOKE)
    smoke_puff(cv, x0 + 680, deck - 215, 40, SMOKE2)
    smoke_puff(cv, x0 + 790, deck - 225, 34, SMOKE)
    # birds
    for bx, by in ((x0 + 150, y0 + 60), (x0 + 190, y0 + 84), (x0 + 120, y0 + 100)):
        cv.line(bx - 10, by, bx, by - 7, INK, 3)
        cv.line(bx, by - 7, bx + 10, by, INK, 3)


def draw_card_huawei(cv, x0, y0, x1, y1):
    """A smartphone with a glowing chip — Huawei's chip push."""
    cv.fill_rect(x0, y0, x1, y1, NAVY)
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    # circuit traces
    for tx in (x0 + 24, x1 - 24):
        cv.vline(tx, y0 + 16, y1 - 16, (46, 84, 120), 2)
    cv.hline(x0 + 24, x1 - 24, y0 + 18, (46, 84, 120), 2)
    cv.hline(x0 + 24, x1 - 24, y1 - 18, (46, 84, 120), 2)
    for dx, dy in ((-52, -38), (52, -38), (-52, 38), (52, 38)):
        cv.circle(cx + dx, cy + dy, 4, CHIP)
    # phone body
    pw, ph = 108, 128
    px0, py0 = cx - pw // 2, cy - ph // 2 + 4
    cv.fill_rect(px0, py0, px0 + pw, py0 + ph, PHONE)
    cv.rect_border(px0, py0, px0 + pw, py0 + ph, (120, 132, 150), 2)
    cv.fill_rect(px0 + 8, py0 + 12, px0 + pw - 8, py0 + ph - 14, (16, 24, 40))
    # chip on the screen
    ch = 44
    cv.fill_rect(cx - ch // 2, cy - ch // 2, cx + ch // 2, cy + ch // 2, CHIP)
    cv.rect_border(cx - ch // 2, cy - ch // 2, cx + ch // 2, cy + ch // 2, (140, 100, 10), 2)
    for k in range(5):
        off = -16 + k * 8
        cv.vline(cx + off, cy - ch // 2 - 8, cy - ch // 2, CHIP, 2)
        cv.vline(cx + off, cy + ch // 2, cy + ch // 2 + 8, CHIP, 2)
        cv.hline(cx - ch // 2 - 8, cx - ch // 2, cy + off, CHIP, 2)
        cv.hline(cx + ch // 2, cx + ch // 2 + 8, cy + off, CHIP, 2)
    cv.text_center(cx, cy - 7, 'AI', 2, NAVY)
    # red accent bar + speaker dot
    cv.fill_rect(px0 + 8, py0 + ph - 8, px0 + pw - 8, py0 + ph - 5, ACCENT)
    cv.circle(cx, py0 + 6, 2, (120, 132, 150))


def draw_card_pacific(cv, x0, y0, x1, y1):
    """Pacific islands joined by a dotted route — the Pacific Pact."""
    cv.fill_rect(x0, y0, x1, y1, OCEAN)
    # sun and clouds
    cv.circle(x1 - 44, y0 + 30, 20, SUN)
    cv.ellipse(x0 + 46, y0 + 26, 26, 8, WHITE)
    cv.ellipse(x0 + 66, y0 + 32, 20, 7, WHITE)
    # dotted pact route arc
    cx, cy, r = (x0 + x1) // 2, y1 - 6, 96
    for deg in range(195, 346, 6):
        import math
        a = math.radians(deg)
        cv.circle(int(cx + r * math.cos(a)), int(cy + r * 0.92 * math.sin(a)), 3, WHITE)
    # islands
    islands = [(x0 + 52, y0 + 108, 30, 14), (x0 + 150, y0 + 78, 24, 12),
               (x0 + 236, y0 + 112, 34, 15), (x0 + 120, y0 + 128, 20, 10)]
    for ix, iy, rx, ry in islands:
        cv.ellipse(ix, iy, rx, ry, ISLAND)
        cv.ellipse(ix, iy - 3, int(rx * 0.7), int(ry * 0.6), (96, 168, 96))
    # palm-ish marker on the big island
    bx, by = x0 + 236, y0 + 112
    cv.line(bx, by - 12, bx, by - 30, (30, 80, 30), 3)
    cv.line(bx, by - 30, bx - 12, by - 36, (30, 80, 30), 3)
    cv.line(bx, by - 30, bx + 12, by - 36, (30, 80, 30), 3)
    # small boats
    for sx, sy in ((x0 + 90, y0 + 66), (x0 + 196, y0 + 58)):
        cv.polygon([(sx - 14, sy), (sx + 14, sy), (sx + 8, sy + 8), (sx - 8, sy + 8)], WHITE)
        cv.line(sx, sy, sx, sy - 14, INK, 2)
        cv.triangle((sx, sy - 14), (sx, sy - 2), (sx + 11, sy - 2), ACCENT)
    # wave lines
    for yy in (y1 - 34, y1 - 20):
        for wx in range(x0 + 14, x1 - 30, 46):
            cv.line(wx, yy, wx + 12, yy - 5, (140, 200, 220), 2)
            cv.line(wx + 12, yy - 5, wx + 24, yy, (140, 200, 220), 2)


def draw_card_refinery(cv, x0, y0, x1, y1):
    """Oil refinery towers at dusk, one column on fire — Ukraine."""
    cv.fill_rect(x0, y0, x1, y1, DUSK)
    cv.circle(x1 - 40, y0 + 28, 18, (249, 217, 118))
    # ground
    gy = y1 - 26
    cv.fill_rect(x0, gy, x1, y1, (24, 22, 34))
    # storage tanks
    for tx in (x0 + 34, x0 + 96):
        cv.fill_rect(tx, gy - 34, tx + 46, gy, STEEL)
        cv.ellipse(tx + 23, gy - 34, 23, 7, (96, 102, 120))
        cv.hline(tx, tx + 46, gy - 20, (52, 56, 68), 2)
    # distillation columns (kept inside the scene)
    cols = [(x0 + 168, 66), (x0 + 214, 82), (x0 + 258, 58)]
    for cx0, chh in cols:
        cv.fill_rect(cx0, gy - chh, cx0 + 22, gy, STEEL)
        cv.fill_rect(cx0 - 3, gy - chh, cx0 + 25, gy - chh + 4, (96, 102, 120))
        for py in range(gy - chh + 16, gy - 8, 18):
            cv.hline(cx0 - 4, cx0 + 26, py, (52, 56, 68), 2)
    # pipes between columns
    cv.hline(x0 + 168, x0 + 280, gy - 70, (52, 56, 68), 3)
    cv.hline(x0 + 168, x0 + 280, gy - 44, (52, 56, 68), 3)
    # flame + smoke on the middle column
    flame(cv, x0 + 225, gy - 82, 34, 16)
    flame(cv, x0 + 269, gy - 58, 26, 11)
    smoke_puff(cv, x0 + 225, gy - 104, 11, SMOKE)
    smoke_puff(cv, x0 + 246, gy - 112, 11, SMOKE2)
    # wheat-gold accent strip (Ukraine)
    cv.fill_rect(x0, y1 - 6, x1, y1, GOLD)


# ------------------------------------------------------------------ layout --
def build():
    cv = Canvas(W, H, PAPER)
    # outer frame
    cv.rect_border(0, 0, W, H, INK, 6)
    cv.rect_border(12, 12, W - 12, H - 12, INK, 2)

    # masthead
    cv.text_center(W // 2, 34, 'THE WORLD TODAY', 6, INK)
    cv.hline(120, W - 120, 88, INK, 3)
    cv.text_center(W // 2, 98, 'WEDNESDAY, 25 NOVEMBER 2026', 3, (180, 132, 20))

    # hero panel
    hx0, hy0, hx1, hy1 = 24, 128, 1000, 606
    cv.rect_border(hx0, hy0, hx1, hy1, INK, 3)
    draw_hero(cv, hx0 + 3, hy0 + 3, hx1 - 3, hy1 - 3 - 108)
    strip_y = hy1 - 108
    cv.fill_rect(hx0 + 3, strip_y, hx1 - 3, hy1 - 3, INK)
    cv.text_center(W // 2, strip_y + 10, 'TANKERS ABLAZE', 6, WHITE)
    cv.text_center(W // 2, strip_y + 56, 'IN THE STRAIT OF HORMUZ', 6, (255, 210, 63))

    # three story cards
    cy0, cy1 = 622, 1000
    cw = (976 - 32) // 3  # 314
    cards = [
        ('TECH', ['HUAWEI', 'CHIP PUSH'],
         "Tech giant in the spotlight as the chip race heats up.",
         draw_card_huawei),
        ('DIPLOMACY', ['PACIFIC PACT'],
         "Nations around the Pacific sign a new deal.",
         draw_card_pacific),
        ('ENERGY', ['REFINERIES', 'UNDER FIRE'],
         "Strikes hit Ukraine's fuel plants as winter nears.",
         draw_card_refinery),
    ]
    for i, (kicker, head_lines, sub, scene) in enumerate(cards):
        x0 = 24 + i * (cw + 16)
        x1 = x0 + cw
        cv.fill_rect(x0, cy0, x1, cy1, CARD)
        cv.rect_border(x0, cy0, x1, cy1, INK, 3)
        scene(cv, x0 + 3, cy0 + 3, x1 - 3, cy0 + 153)
        ty = cy0 + 166
        cv.text_center((x0 + x1) // 2, ty, kicker, 2, ACCENT)
        ty += 26
        for line in head_lines:
            cv.text_center((x0 + x1) // 2, ty, line, 4, INK)
            ty += 32
        ty += 8
        for line in wrap_text(sub, 24):
            cv.text_center((x0 + x1) // 2, ty, line, 2, (60, 60, 70))
            ty += 18
    return cv


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', 'out')
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    path = os.path.join(out_dir, 'entry.png')
    size = write_png(cv, path)
    print('wrote %s (%d bytes, %dx%d)' % (path, size, W, H))
    return 0


if __name__ == '__main__':
    sys.exit(main())
