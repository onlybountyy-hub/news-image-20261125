#!/usr/bin/env python3
"""news-image-20261125 v6 -- "THE WORLD TODAY", Wednesday 25 November 2026.

One 1024x1024 PNG summing up the day's world news, drawn from scratch with
pure Python standard library only (no PIL, no network, no third-party code).

Layout (editorial broadsheet, light paper throughout):
  masthead  "THE WORLD TODAY" + red rule
  date band red field: "WEDNESDAY - 25 NOVEMBER 2026"
  hero      giant red "2" + "TANKERS HIT MINES, / BURN IN HORMUZ",
            subline "STRAIT OF HORMUZ", chip MIDDLE EAST, source REUTERS,
            flat sea scene: two tankers, flames, naval mines
  grid 2x2  Huawei convicted (EAST ASIA) / Pacific security pact (PACIFIC) /
            Ukraine strikes Russian energy sites (EUROPE) /
            Pakistan's first astronaut reaches Tiangong (SOUTH ASIA)

The program writes its own PNG bytes and draws text with its own stroke
letterforms. Output: $MAKEFUN_OUTPUT_DIR/entry.png, exactly 1024x1024,
deterministic (two runs are byte-identical).
"""

import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)
INK = (20, 20, 20)
RED = (193, 18, 31)
TEAL = (15, 76, 92)
OCHRE = (217, 164, 65)

# Horizontal condensation of the stroke font (glyphs are drawn in a 0..10
# x-space, then squeezed by this factor so long headlines fit their columns).
FX = 0.85


class Canvas(object):
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0))
        y0 = max(0, int(y0))
        x1 = min(self.w, int(x1))
        y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        c3 = bytes(color)
        span = (x1 - x0) * 3
        row = c3 * (x1 - x0)
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            self.buf[base:base + span] = row

    def fill_circle(self, cx, cy, r, color):
        r = int(round(r))
        if r <= 0:
            return
        cx = int(round(cx))
        cy = int(round(cy))
        c3 = bytes(color)
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            y = cy + dy
            if 0 <= y < self.h:
                x0 = max(0, cx - dx)
                x1 = min(self.w, cx + dx + 1)
                if x1 > x0:
                    base = (y * self.w + x0) * 3
                    self.buf[base:base + (x1 - x0) * 3] = c3 * (x1 - x0)

    def ring(self, cx, cy, r_out, r_in, color):
        self.fill_circle(cx, cy, r_out, color)
        self.fill_circle(cx, cy, r_in, PAPER)

    def fill_polygon(self, pts, color):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        top = max(0, int(math.floor(min(ys))))
        bot = min(self.h, int(math.ceil(max(ys))))
        n = len(pts)
        c3 = bytes(color)
        for y in range(top, bot):
            yc = y + 0.5
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    t = (yc - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa = max(0, int(math.ceil(xs[j])))
                xb = min(self.w, int(math.floor(xs[j + 1])))
                if xb > xa:
                    base = (y * self.w + xa) * 3
                    self.buf[base:base + (xb - xa) * 3] = c3 * (xb - xa)

    def thick_line(self, x0, y0, x1, y1, w, color):
        dx = x1 - x0
        dy = y1 - y0
        leng = math.hypot(dx, dy)
        if leng < 0.001:
            self.fill_circle(x0, y0, w / 2.0, color)
            return
        nx = -dy / leng * w / 2.0
        ny = dx / leng * w / 2.0
        self.fill_polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                           (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], color)

    def polyline(self, pts, w, color):
        for i in range(len(pts) - 1):
            self.thick_line(pts[i][0], pts[i][1],
                            pts[i + 1][0], pts[i + 1][1], w, color)
        for (x, y) in pts:
            self.fill_circle(x, y, w / 2.0, color)


def png_bytes(canvas):
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.buf[y * canvas.w * 3:(y + 1) * canvas.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))

# ---------------------------------------------------------------------------
# Stroke letterforms. Each glyph: (advance, [stroke, ...]) where a stroke is
# a polyline in a 0..10 (x) by 0..14 (y, up from the baseline) grid. Cap
# height is 14 units; commas descend to -3. Dots (middle dot, period) are
# handled separately in DOTS as (dx, dy, radius) in glyph units.
# ---------------------------------------------------------------------------
FONT = {
    "A": (9.5, [[(1, 0), (5, 14), (9, 0)], [(3.2, 5.5), (6.8, 5.5)]]),
    "B": (9, [[(1, 0), (1, 14), (7, 14), (9, 12), (9, 10), (7, 8), (1, 8)],
              [(7, 8), (9, 6), (9, 2), (7, 0), (1, 0)]]),
    "C": (9, [[(9, 12), (7, 14), (3, 14), (1, 12), (1, 2), (3, 0), (7, 0), (9, 2)]]),
    "D": (9.5, [[(1, 0), (1, 14), (6.5, 14), (9, 12), (9, 2), (6.5, 0), (1, 0)]]),
    "E": (8, [[(9, 14), (1, 14), (1, 0), (9, 0)], [(1, 7), (6.5, 7)]]),
    "F": (8, [[(1, 0), (1, 14), (9, 14)], [(1, 7), (6.5, 7)]]),
    "G": (9.5, [[(9, 12), (7, 14), (3, 14), (1, 12), (1, 2), (3, 0), (7, 0),
                 (9, 2), (9, 6), (6, 6)]]),
    "H": (9.5, [[(1, 0), (1, 14)], [(9, 0), (9, 14)], [(1, 7), (9, 7)]]),
    "I": (4.5, [[(2.25, 0), (2.25, 14)], [(0.5, 14), (4, 14)], [(0.5, 0), (4, 0)]]),
    "J": (7, [[(6.5, 14), (6.5, 2), (4.5, 0), (2, 0.5), (1, 2.5)]]),
    "K": (9, [[(1, 0), (1, 14)], [(9, 14), (1, 7), (9, 0)]]),
    "L": (8.5, [[(1, 14), (1, 0), (8, 0)]]),
    "M": (10, [[(1, 0), (1, 14), (5, 6), (9, 14), (9, 0)]]),
    "N": (9.5, [[(1, 0), (1, 14), (9, 0), (9, 14)]]),
    "O": (9.5, [[(3, 14), (7, 14), (9, 12), (9, 2), (7, 0), (3, 0), (1, 2),
                 (1, 12), (3, 14)]]),
    "P": (8.5, [[(1, 0), (1, 14), (7, 14), (9, 12), (9, 9), (7, 7), (1, 7)]]),
    "Q": (9.5, [[(3, 14), (7, 14), (9, 12), (9, 2), (7, 0), (3, 0), (1, 2),
                 (1, 12), (3, 14)], [(6, 4), (9, 0)]]),
    "R": (8.5, [[(1, 0), (1, 14), (7, 14), (9, 12), (9, 9), (7, 7), (1, 7)],
                [(5.5, 7), (9, 0)]]),
    "S": (8.5, [[(9, 12), (7, 14), (3, 14), (1, 12), (1, 9), (3, 7), (6.5, 7),
                 (8.5, 5), (8.5, 2), (6.5, 0), (3, 0), (1, 2)]]),
    "T": (7.5, [[(0.5, 14), (7, 14)], [(3.75, 0), (3.75, 14)]]),
    "U": (9.5, [[(1, 14), (1, 2), (3, 0), (7, 0), (9, 2), (9, 14)]]),
    "V": (9.5, [[(1, 14), (5, 0), (9, 14)]]),
    "W": (11, [[(1, 14), (3, 0), (5, 7), (7, 0), (9, 14)]]),
    "X": (9.5, [[(1, 0), (9, 14)], [(9, 0), (1, 14)]]),
    "Y": (8.5, [[(0.5, 14), (4.25, 7), (8, 14)], [(4.25, 7), (4.25, 0)]]),
    "Z": (8.5, [[(0.5, 14), (8.5, 14), (0.5, 0), (8.5, 0)]]),
    "0": (9.5, [[(3, 14), (7, 14), (9, 12), (9, 2), (7, 0), (3, 0), (1, 2),
                 (1, 12), (3, 14)]]),
    "1": (5, [[(1.5, 12), (3, 14), (3, 0)], [(0.5, 0), (4.5, 0)]]),
    "2": (9, [[(1, 12), (3, 14), (7, 14), (9, 12), (9, 9), (1, 0), (9, 0)]]),
    "3": (9, [[(1, 14), (7, 14), (9, 12), (9, 10), (7, 8), (5, 7)],
              [(5, 7), (7, 7), (9, 5), (9, 2), (7, 0), (1, 0)]]),
    "4": (9.5, [[(8, 14), (1, 5), (9, 5)], [(7, 0), (7, 14)]]),
    "5": (9, [[(9, 14), (1, 14), (1, 8), (7, 8), (9, 6), (9, 2), (7, 0), (1, 0)]]),
    "6": (9.5, [[(9, 12), (7, 14), (3, 14), (1, 12), (1, 2), (3, 0), (7, 0),
                 (9, 2), (9, 6), (7, 8), (3, 8), (1, 6)]]),
    "7": (9, [[(1, 14), (9, 14), (4, 0)]]),
    "8": (9.5, [[(5, 14), (7.5, 12), (7.5, 10), (5, 8), (2.5, 10), (2.5, 12),
                 (5, 14)],
                [(5, 8), (7.5, 6), (7.5, 2), (5, 0), (2.5, 2), (2.5, 6), (5, 8)]]),
    "9": (9.5, [[(1, 2), (3, 0), (7, 0), (9, 2), (9, 12), (7, 14), (3, 14),
                 (1, 12), (1, 8), (3, 6), (7, 6), (9, 8)]]),
    ",": (4.5, [[(2.5, 2), (2, 0), (1, -3)]]),
    "'": (4, [[(2.5, 14), (2, 10)]]),
    "-": (7, [[(0.5, 7), (6.5, 7)]]),
}

# Dots: char -> (advance, dx, dy, radius) in glyph units.
DOTS = {
    "\u00b7": (4.5, 2.25, 7, 1.2),   # middle dot (date band separator)
    ".": (4.5, 2.25, 1, 1.2),
}

SPACE_ADV = 4.5


def text_width(s, cap):
    scale = cap / 14.0
    total = 0.0
    for ch in s:
        if ch in FONT:
            total += FONT[ch][0]
        elif ch in DOTS:
            total += DOTS[ch][0]
        else:
            total += SPACE_ADV
    return total * FX * scale


def draw_text(cv, x, baseline, s, cap, color, align="left"):
    """Draw text with its baseline at y=baseline. Returns width in px."""
    scale = cap / 14.0
    w = text_width(s, cap)
    if align == "center":
        x = x - w / 2.0
    elif align == "right":
        x = x - w
    sw = max(2, int(round(cap * 0.11)))
    cx = x
    for ch in s:
        if ch in DOTS:
            adv, dx, dy, r = DOTS[ch]
            cv.fill_circle(cx + dx * FX * scale, baseline - dy * scale,
                           r * scale, color)
            cx += adv * FX * scale
            continue
        g = FONT.get(ch)
        if g is None:
            cx += SPACE_ADV * FX * scale
            continue
        adv, strokes = g
        for stroke in strokes:
            pts = [(cx + px * FX * scale, baseline - py * scale)
                   for (px, py) in stroke]
            cv.polyline(pts, sw, color)
        cx += adv * FX * scale
    return w


def chip(cv, x, y_top, label, cap, color, border=3, pad=14):
    """Outlined region chip; returns its right edge x."""
    w = text_width(label, cap) + 2 * pad
    h = cap + 6
    cv.fill_rect(x, y_top, x + w, y_top + border, color)
    cv.fill_rect(x, y_top + h - border, x + w, y_top + h, color)
    cv.fill_rect(x, y_top, x + border, y_top + h, color)
    cv.fill_rect(x + w - border, y_top, x + w, y_top + h, color)
    draw_text(cv, x + pad, y_top + h - 4, label, cap, color)
    return x + w


# ---------------------------------------------------------------------------
# Flat pictorial shapes (all in the 5-colour palette).
# ---------------------------------------------------------------------------

def flame(cv, cx, base_y, h, w):
    """Flat stylised flame tongue, red with an ochre inner flame."""
    pts = [(cx - w / 2.0, base_y),
           (cx - w / 2.0, base_y - h * 0.38),
           (cx - w * 0.28, base_y - h * 0.55),
           (cx - w * 0.10, base_y - h * 0.72),
           (cx, base_y - h),
           (cx + w * 0.12, base_y - h * 0.68),
           (cx + w * 0.30, base_y - h * 0.55),
           (cx + w / 2.0, base_y - h * 0.35),
           (cx + w / 2.0, base_y)]
    cv.fill_polygon(pts, RED)
    w2 = w * 0.55
    h2 = h * 0.58
    pts2 = [(cx - w2 / 2.0, base_y),
            (cx - w2 / 2.0, base_y - h2 * 0.4),
            (cx - w2 * 0.2, base_y - h2 * 0.6),
            (cx, base_y - h2),
            (cx + w2 * 0.25, base_y - h2 * 0.55),
            (cx + w2 / 2.0, base_y - h2 * 0.35),
            (cx + w2 / 2.0, base_y)]
    cv.fill_polygon(pts2, OCHRE)


def mine(cv, cx, cy, r):
    """Naval mine: ink disc with eight spikes and a paper centre dot."""
    cv.fill_circle(cx, cy, r, INK)
    for k in range(8):
        a = math.radians(k * 45)
        x0 = cx + math.cos(a) * r * 0.75
        y0 = cy + math.sin(a) * r * 0.75
        x1 = cx + math.cos(a) * (r + 8)
        y1 = cy + math.sin(a) * (r + 8)
        cv.thick_line(x0, y0, x1, y1, 4, INK)
    cv.fill_circle(cx, cy, 3, PAPER)


def tanker(cv, x0, x1, y_top, y_bot, deck, funnel, flame_cx):
    """Flat black tanker silhouette with a flame above its deckhouse.
    deck/funnel are (x0, x1) pairs; the flame rises above the deckhouse."""
    # Hull + bow.
    cv.fill_rect(x0, y_top, x1, y_bot, INK)
    cv.fill_polygon([(x1, y_top), (x1 + 26, (y_top + y_bot) / 2.0),
                     (x1, y_bot)], INK)
    # Deckhouse with two paper windows.
    cv.fill_rect(deck[0], y_top - 28, deck[1], y_top, INK)
    cv.fill_rect(deck[0] + 6, y_top - 20, deck[0] + 16, y_top - 10, PAPER)
    cv.fill_rect(deck[0] + 22, y_top - 20, deck[0] + 32, y_top - 10, PAPER)
    # Funnel with a red cap band.
    cv.fill_rect(funnel[0], y_top - 34, funnel[1], y_top, INK)
    cv.fill_rect(funnel[0], y_top - 34, funnel[1], y_top - 26, RED)
    # Flame above the deckhouse (tip stays clear of the subline row above).
    flame(cv, flame_cx, y_top - 28, 34, 28)


# ---------------------------------------------------------------------------
# Page layout.
# ---------------------------------------------------------------------------

def draw_masthead(cv):
    draw_text(cv, W / 2.0, 68, "THE WORLD TODAY", 60, INK, align="center")
    cv.fill_rect(32, 86, 992, 92, RED)


def draw_date_band(cv):
    cv.fill_rect(0, 96, W, 160, RED)
    draw_text(cv, W / 2.0, 150, "WEDNESDAY \u00b7 25 NOVEMBER 2026",
              44, PAPER, align="center")


def draw_hero(cv):
    # Giant red "2" on the left.
    draw_text(cv, 36, 342, "2", 150, RED)
    # Headline, two lines, right of the number.
    draw_text(cv, 196, 270, "TANKERS HIT MINES,", 84, INK)
    draw_text(cv, 196, 362, "BURN IN HORMUZ", 84, INK)
    # Subline + region chip + source.
    draw_text(cv, 196, 400, "STRAIT OF HORMUZ", 32, INK)
    right = chip(cv, 470, 366, "MIDDLE EAST", 32, RED)
    draw_text(cv, right + 20, 400, "REUTERS", 32, INK)
    # Flat sea scene at the foot of the hero.
    cv.fill_rect(0, 495, W, 540, TEAL)
    cv.fill_rect(60, 518, 110, 522, PAPER)
    cv.fill_rect(480, 532, 540, 536, PAPER)
    cv.fill_rect(850, 518, 900, 522, PAPER)
    tanker(cv, 240, 460, 478, 514, (290, 350), (395, 425), 320)
    tanker(cv, 590, 820, 478, 514, (630, 690), (735, 765), 660)
    mine(cv, 505, 528, 13)
    mine(cv, 895, 526, 12)


# ---------------------------------------------------------------------------
# Grid cards. Each card is 488x230: red top rule, flat pictogram on the left,
# headline (2 lines; card 4 needs 3 lines at a slightly smaller cap because
# its headline is the longest), region chip + source line.
# ---------------------------------------------------------------------------

def picto_phone(cv, px, py):
    # Huawei: phone handset with a chip on its screen. Box is 88x60.
    cv.fill_rect(px + 22, py + 2, px + 66, py + 58, INK)
    cv.fill_rect(px + 27, py + 8, px + 61, py + 48, TEAL)
    cv.fill_rect(px + 38, py + 4, px + 50, py + 6, PAPER)
    cv.fill_rect(px + 32, py + 18, px + 56, py + 40, OCHRE)
    cv.fill_rect(px + 38, py + 24, px + 50, py + 34, INK)
    cv.fill_rect(px + 38, py + 51, px + 50, py + 54, PAPER)


def picto_pact(cv, px, py):
    # Pacific pact: two islands, an ochre sun, a dashed red treaty line.
    cv.fill_circle(px + 44, py + 8, 5, OCHRE)
    for dx in range(0, 26, 7):
        cv.fill_rect(px + 32 + dx, py + 20, px + 37 + dx, py + 24, RED)
    cv.fill_polygon([(px + 8, py + 58), (px + 14, py + 40), (px + 28, py + 32),
                     (px + 42, py + 42), (px + 38, py + 58)], TEAL)
    cv.fill_polygon([(px + 54, py + 56), (px + 60, py + 38), (px + 74, py + 34),
                     (px + 82, py + 46), (px + 78, py + 56)], TEAL)


def picto_refinery(cv, px, py):
    # Ukraine: refinery tower with a flat flame and a storage tank.
    flame(cv, px + 44, py + 26, 20, 18)
    cv.fill_polygon([(px + 30, py + 58), (px + 34, py + 26),
                     (px + 54, py + 26), (px + 58, py + 58)], INK)
    cv.fill_rect(px + 36, py + 34, px + 52, py + 37, PAPER)
    cv.fill_rect(px + 36, py + 43, px + 52, py + 46, PAPER)
    cv.fill_rect(px + 36, py + 52, px + 52, py + 55, PAPER)
    cv.fill_rect(px + 62, py + 44, px + 82, py + 58, TEAL)
    cv.fill_rect(px + 62, py + 44, px + 82, py + 47, INK)


def picto_rocket(cv, px, py):
    # Pakistan astronaut: rocket inside an orbit ring, two red stars.
    cv.ring(px + 44, py + 30, 28, 25, INK)
    cv.fill_polygon([(px + 37, py + 40), (px + 29, py + 50), (px + 37, py + 50)], INK)
    cv.fill_polygon([(px + 51, py + 40), (px + 59, py + 50), (px + 51, py + 50)], INK)
    cv.fill_rect(px + 37, py + 18, px + 51, py + 46, TEAL)
    cv.fill_polygon([(px + 37, py + 18), (px + 44, py + 6), (px + 51, py + 18)], RED)
    cv.fill_circle(px + 44, py + 28, 3, PAPER)
    cv.fill_polygon([(px + 39, py + 46), (px + 44, py + 60), (px + 49, py + 46)], OCHRE)
    cv.fill_circle(px + 10, py + 12, 2, RED)
    cv.fill_circle(px + 76, py + 10, 2, RED)


CARDS = [
    # (pictogram, headline lines, region chip, source)
    (picto_phone,
     ["HUAWEI CONVICTED", "IN US TRIAL"], "EAST ASIA", "REUTERS", 44),
    (picto_pact,
     ["AUSTRALIA SIGNS", "PACIFIC SECURITY PACT"], "PACIFIC", "NEWS WIRES", 44),
    (picto_refinery,
     ["UKRAINE STRIKES", "RUSSIAN ENERGY SITES"], "EUROPE", "NEWS WIRES", 44),
    (picto_rocket,
     ["PAKISTAN'S FIRST", "ASTRONAUT REACHES", "TIANGONG"],
     "SOUTH ASIA", "REUTERS", 40),
]


def draw_card(cv, cx, cy, picto, lines, region, source, cap):
    cv.fill_rect(cx, cy, cx + 488, cy + 5, RED)
    if len(lines) == 2:
        # Pictogram box is 88x60 at cy+38..cy+98; line 2 starts at cy+106.
        picto(cv, cx + 14, cy + 38)
        draw_text(cv, cx + 116, cy + 96, lines[0], cap, INK)
        draw_text(cv, cx + 14, cy + 150, lines[1], cap, INK)
        chip_y, src_base = cy + 174, cy + 208
    else:
        # 3-line card: pictogram at cy+24..cy+84; line 2 starts at cy+90.
        picto(cv, cx + 14, cy + 24)
        draw_text(cv, cx + 116, cy + 82, lines[0], cap, INK)
        draw_text(cv, cx + 14, cy + 130, lines[1], cap, INK)
        draw_text(cv, cx + 14, cy + 170, lines[2], cap, INK)
        chip_y, src_base = cy + 180, cy + 214
    right = chip(cv, cx + 14, chip_y, region, 32, RED)
    draw_text(cv, right + 14, src_base, source, 32, INK)


def draw():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_date_band(cv)
    draw_hero(cv)
    # Grid 2x2: rows y 548-778 and 794-1024, cols x 16-504 and 520-1008.
    positions = [(16, 548), (520, 548), (16, 794), (520, 794)]
    for (cx, cy), card in zip(positions, CARDS):
        draw_card(cv, cx, cy, *card)
    return cv


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(out, exist_ok=True)
    cv = draw()
    path = os.path.join(out, "entry.png")
    with open(path, "wb") as f:
        f.write(png_bytes(cv))
    sys.stdout.write("wrote %s\n" % path)


if __name__ == "__main__":
    main()
