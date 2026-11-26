#!/usr/bin/env python3
"""news-image-20261125 v4 — "THE WORLD TODAY".

One 1024x1024 PNG summing up Wednesday 25 November 2026's world news,
drawn from scratch in pure Python standard library (no PIL, no network,
no image assets). Every glyph is a vector/pixel letterform defined below;
the PNG encoder is written by hand.

Design (thumbnail-first, from the DeepAI critique of v3):
  * bright high-key page, flat editorial pictograms, 5-colour palette
  * two-tier typography: nothing below 32px cap height
  * hero: two tankers hit mines and burn in the Strait of Hormuz
  * four cards, one per region: East Asia, Pacific, Europe, South Asia

Stories (verified, Wednesday 25 November 2026 only):
  1. Two oil tankers hit sea mines and caught fire in the Strait of
     Hormuz (Reuters, Dubai, 25 Nov).
  2. Huawei convicted in a major US criminal trial over Iran business
     (Reuters, 25 Nov 10:58).
  3. Australia and Solomon Islands sign a major Pacific security pact
     (reported 25 Nov).
  4. Ukraine strikes Russian energy infrastructure amid peace-framework
     diplomacy (reported 25 Nov).
  5. China's Shenzhou-24 docks at Tiangong with Pakistan's first
     astronaut aboard — the first foreign astronaut on the station
     (Reuters, 25 Nov 17:47).

Run:  MAKEFUN_OUTPUT_DIR=<dir> python3 -P -s main.py
Writes <dir>/entry.png (1024x1024, <= 1 MiB, deterministic).
"""

import math
import os
import struct
import sys
import zlib

W = H = 1024

# --- palette (5 colours max) ---------------------------------------------
PAPER = (247, 243, 232)   # off-white paper
INK = (20, 20, 20)        # near-black ink
RED = (193, 18, 31)       # accent red
TEAL = (15, 76, 92)       # sea teal
OCHRE = (217, 164, 65)    # flame ochre
WHITE = (255, 255, 255)   # wave highlights only (paper-light variant)

# --- canvas ----------------------------------------------------------------
_rows = None


def new_canvas():
    global _rows
    fill = bytes(PAPER) * W
    _rows = [bytearray(fill) for _ in range(H)]


def clip(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def fill_rect(x, y, w, h, color):
    """Fill an axis-aligned rectangle (floats allowed; clipped)."""
    x0 = int(round(x))
    y0 = int(round(y))
    x1 = int(round(x + w))
    y1 = int(round(y + h))
    x0 = clip(x0, 0, W)
    y0 = clip(y0, 0, H)
    x1 = clip(x1, 0, W)
    y1 = clip(y1, 0, H)
    if x1 <= x0 or y1 <= y0:
        return
    r, g, b = color
    span = bytes((r, g, b)) * (x1 - x0)
    for yy in range(y0, y1):
        row = _rows[yy]
        row[x0 * 3:x1 * 3] = span


def fill_circle(cx, cy, r, color):
    """Filled circle, centre (cx, cy), radius r."""
    x0 = int(math.floor(cx - r))
    x1 = int(math.ceil(cx + r))
    y0 = int(math.floor(cy - r))
    y1 = int(math.ceil(cy + r))
    r2 = r * r
    for yy in range(max(0, y0), min(H, y1 + 1)):
        dy = yy + 0.5 - cy
        dx = math.sqrt(max(0.0, r2 - dy * dy))
        fill_rect(cx - dx, yy, dx * 2, 1, color)


def ring(cx, cy, r_out, r_in, color):
    """Circle outline (filled ring)."""
    fill_circle(cx, cy, r_out, color)
    fill_circle(cx, cy, r_in, PAPER)


def fill_ellipse(cx, cy, rx, ry, color):
    x0 = int(math.floor(cx - rx))
    x1 = int(math.ceil(cx + rx))
    y0 = int(math.floor(cy - ry))
    y1 = int(math.ceil(cy + ry))
    for yy in range(max(0, y0), min(H, y1 + 1)):
        dy = (yy + 0.5 - cy) / ry
        if abs(dy) > 1.0:
            continue
        dx = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
        fill_rect(cx - dx, yy, dx * 2, 1, color)


def fill_polygon(points, color):
    """Scanline fill of a simple polygon (even-odd)."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0 = int(math.floor(min(ys)))
    y1 = int(math.ceil(max(ys)))
    n = len(points)
    for yy in range(max(0, y0), min(H, y1 + 1)):
        y = yy + 0.5
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                t = (y - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            fill_rect(xs[k], yy, xs[k + 1] - xs[k], 1, color)


def thick_line(x0, y0, x1, y1, width, color):
    """Line drawn as a chain of filled discs (deterministic)."""
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    steps = max(1, int(length / max(1.0, width * 0.4)))
    r = width / 2.0
    for i in range(steps + 1):
        t = i / steps
        fill_circle(x0 + dx * t, y0 + dy * t, r, color)


def dashed_line(x0, y0, x1, y1, dash, gap, width, color):
    """Dashed straight line."""
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        thick_line(x0 + ux * pos, y0 + uy * pos,
                   x0 + ux * end, y0 + uy * end, width, color)
        pos = end + gap


# --- pixel font (5x7 grid, proportional widths) ---------------------------
# Each glyph: 7 rows; row length = glyph width in grid cells.
# Cap height = 7 units; advance = (width + 0.5) units.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("1111", "1000", "1000", "1110", "1000", "1000", "1000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "J": ("0111", "0001", "0001", "0001", "0001", "1001", "0110"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("1000", "1000", "1000", "1000", "1000", "1000", "1111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("1111", "0100", "0100", "0100", "0100", "0100", "0100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("010", "110", "010", "010", "010", "010", "111"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00", "00", "00", "00", "00", "00", "00"),
    ".": ("00", "00", "00", "00", "00", "00", "11"),
    ",": ("00", "00", "00", "00", "00", "11", "10"),
    "'": ("11", "11", "10", "00", "00", "00", "00"),
    "\u00b7": ("000", "000", "000", "010", "000", "000", "000"),
    "-": ("0000", "0000", "0000", "1111", "0000", "0000", "0000"),
    ":": ("00", "00", "11", "00", "00", "11", "00"),
    "/": ("0001", "0001", "0010", "0010", "0100", "0100", "1000"),
    "(": ("001", "010", "100", "100", "100", "010", "001"),
    ")": ("100", "010", "001", "001", "001", "010", "100"),
}

SPACING = 0.5  # grid units between glyphs


def glyph_width(ch):
    return len(FONT[ch][0])


def text_width(text, cap):
    """Width in px of `text` at cap height `cap`."""
    unit = cap / 7.0
    total = 0.0
    for ch in text:
        total += (glyph_width(ch) + SPACING) * unit
    return total - SPACING * unit


def draw_text(x, y, text, cap, color, halo=None):
    """Draw text with top-left at (x, y). `halo` (px) draws a paper-colour
    bleed behind the glyphs first (for text sitting on the teal sea)."""
    unit = cap / 7.0
    if halo is not None:
        cx = x
        for ch in text:
            g = FONT[ch]
            w = len(g[0])
            for r in range(7):
                for c in range(w):
                    if g[r][c] == "1":
                        fill_rect(cx + c * unit - halo, y + r * unit - halo,
                                  unit + 2 * halo, unit + 2 * halo, PAPER)
            cx += (w + SPACING) * unit
    cx = x
    for ch in text:
        g = FONT[ch]
        w = len(g[0])
        for r in range(7):
            for c in range(w):
                if g[r][c] == "1":
                    # slight overlap so scaled cells never leave hairline gaps
                    fill_rect(cx + c * unit, y + r * unit,
                              unit + 0.8, unit + 0.8, color)
        cx += (w + SPACING) * unit


def draw_text_centred(cx, y, text, cap, color, halo=None):
    draw_text(cx - text_width(text, cap) / 2.0, y, text, cap, color, halo)


def draw_text_right(x1, y, text, cap, color, halo=None):
    draw_text(x1 - text_width(text, cap), y, text, cap, color, halo)


def wrap_text(text, cap, max_width, max_lines):
    """Greedy word wrap; returns list of lines (<= max_lines, or best
    effort with the last line allowed to stand alone)."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, cap) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines[:max_lines]


# --- PNG encoder (filter 0, RGB8, deterministic) ---------------------------
def png_bytes():
    raw = bytearray()
    for row in _rows:
        raw.append(0)  # filter: none
        raw.extend(row)
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        out = struct.pack(">I", len(data)) + ctype + data
        out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp)
            + chunk(b"IEND", b""))



# --- pictograms --------------------------------------------------------------
# Each draws inside a box (bx, by, bw, bh) with flat 2-3 colour shapes.

def pic_phone(bx, by, bw, bh):
    """Huawei: phone with a chip on its screen."""
    x0, y0 = bx + 52, by + 2
    w, h = 40, 44
    fill_rect(x0, y0, w, h, INK)                    # phone body
    fill_rect(x0 + 4, y0 + 4, w - 8, h - 8, PAPER)  # screen
    # chip: ochre square + pins
    cx, cy = x0 + w // 2, y0 + h // 2 + 1
    fill_rect(cx - 8, cy - 8, 16, 16, OCHRE)
    fill_rect(cx - 4, cy - 4, 8, 8, INK)
    for dy in (-8, -3, 2):
        fill_rect(cx - 12, cy + dy, 4, 2, INK)
        fill_rect(cx + 8, cy + dy, 4, 2, INK)
    for dx in (-8, -3, 2):
        fill_rect(cx + dx, cy - 12, 2, 4, INK)
        fill_rect(cx + dx, cy + 8, 2, 4, INK)
    # earpiece + home bar
    fill_rect(cx - 6, y0 + 7, 12, 2, INK)
    fill_rect(cx - 6, y0 + h - 7, 12, 2, INK)
    # signal bars, top right of the box
    for i, bh2 in enumerate((8, 13, 18)):
        fill_rect(bx + 108 + i * 9, by + 26 - bh2, 6, bh2, TEAL)
    # red "verdict" tick under the bars
    thick_line(bx + 104, by + 36, bx + 112, by + 44, 4, RED)
    thick_line(bx + 112, by + 44, bx + 128, by + 28, 4, RED)


def pic_pact(bx, by, bw, bh):
    """Pacific pact: two islands joined by a dashed agreement line."""
    # islands (teal)
    fill_ellipse(bx + 34, by + 36, 27, 11, TEAL)
    fill_ellipse(bx + 116, by + 32, 23, 10, TEAL)
    # palm dots on the islands
    fill_circle(bx + 30, by + 22, 3, INK)
    fill_circle(bx + 118, by + 19, 3, INK)
    # dashed pact line arcing between them
    dashed_line(bx + 34, by + 18, bx + 116, by + 14, 9, 6, 3, INK)
    # red seal at the middle of the line
    fill_circle(bx + 75, by + 12, 6, RED)
    fill_circle(bx + 75, by + 12, 2, PAPER)
    # sea dashes under the islands
    fill_rect(bx + 12, by + 44, 26, 3, TEAL)
    fill_rect(bx + 100, by + 44, 26, 3, TEAL)
    # ochre sun
    fill_circle(bx + 138, by + 8, 6, OCHRE)


def pic_refinery(bx, by, bw, bh):
    """Ukraine: refinery tower + chimney with flat flames."""
    # tower
    fill_rect(bx + 18, by + 16, 34, 30, INK)
    fill_rect(bx + 18, by + 24, 34, 3, PAPER)
    fill_rect(bx + 18, by + 33, 34, 3, PAPER)
    # chimney
    fill_rect(bx + 58, by + 24, 12, 22, INK)
    # flat flames: red outer, ochre inner
    fill_polygon([(bx + 22, by + 16), (bx + 48, by + 16),
                  (bx + 35, by + 2)], RED)
    fill_polygon([(bx + 29, by + 16), (bx + 41, by + 16),
                  (bx + 35, by + 7)], OCHRE)
    fill_polygon([(bx + 60, by + 24), (bx + 68, by + 24),
                  (bx + 64, by + 15)], RED)
    # storage tank
    fill_circle(bx + 96, by + 38, 10, TEAL)
    fill_rect(bx + 86, by + 28, 20, 3, TEAL)
    # ochre sun / blast dot
    fill_circle(bx + 128, by + 10, 6, OCHRE)


def pic_rocket(bx, by, bw, bh):
    """Pakistan astronaut: rocket + Tiangong ring station."""
    # rocket body (paper with ink outline)
    fill_rect(bx + 28, by + 12, 18, 28, INK)
    fill_rect(bx + 30, by + 14, 14, 24, PAPER)
    # nose cone (red)
    fill_polygon([(bx + 28, by + 13), (bx + 46, by + 13),
                  (bx + 37, by + 2)], RED)
    # window
    fill_circle(bx + 37, by + 22, 3, TEAL)
    # fins (teal)
    fill_polygon([(bx + 28, by + 32), (bx + 28, by + 42),
                  (bx + 18, by + 44)], TEAL)
    fill_polygon([(bx + 46, by + 32), (bx + 46, by + 42),
                  (bx + 56, by + 44)], TEAL)
    # flat flame (ochre)
    fill_polygon([(bx + 31, by + 40), (bx + 43, by + 40),
                  (bx + 37, by + 47)], OCHRE)
    # station ring (ink ring, paper centre) + module bar
    ring(bx + 108, by + 18, 15, 11, INK)
    fill_rect(bx + 92, by + 15, 32, 6, INK)
    fill_rect(bx + 104, by + 12, 8, 12, TEAL)
    # small red star
    sx, sy = bx + 132, by + 40
    fill_rect(sx - 2, sy - 7, 4, 14, RED)
    fill_rect(sx - 7, sy - 2, 14, 4, RED)


def draw_mine(cx, cy, r):
    """Spiky naval mine: ink disc + spikes + red centre."""
    for k in range(8):
        a = math.pi * k / 4.0
        thick_line(cx + math.cos(a) * r * 0.7, cy + math.sin(a) * r * 0.7,
                   cx + math.cos(a) * (r + 8), cy + math.sin(a) * (r + 8),
                   3, INK)
    fill_circle(cx, cy, r, INK)
    fill_circle(cx, cy, 4, RED)


def draw_tanker(x, y_base, w):
    """Flat tanker silhouette sitting on the sea (y_base = waterline)."""
    top = y_base - 20
    hull = [(x, top), (x + w - 34, top), (x + w, top + 10),
            (x + w - 8, y_base), (x, y_base)]
    fill_polygon(hull, INK)
    # deckhouse (paper) + funnel (ochre) + flat flame
    fill_rect(x + 14, top - 16, 34, 16, PAPER)
    fill_rect(x + 14, top - 16, 34, 3, INK)
    fill_rect(x + 58, top - 24, 16, 24, OCHRE)
    fill_polygon([(x + 55, top - 24), (x + 77, top - 24),
                  (x + 66, top - 48)], RED)
    fill_polygon([(x + 61, top - 24), (x + 71, top - 24),
                  (x + 66, top - 36)], OCHRE)
    # portholes
    for px in (x + 96, x + 122, x + 148):
        fill_circle(px, top + 10, 3, PAPER)
    # bow flag
    fill_rect(x + w - 26, top - 12, 2, 12, INK)
    fill_rect(x + w - 24, top - 12, 12, 7, RED)


def draw_chip(x, y, text, cap, fill=False):
    """Region chip: outlined box (or red-filled) with centred text."""
    tw = text_width(text, cap)
    bw = tw + 22
    bh = cap + 8
    if fill:
        fill_rect(x, y, bw, bh, RED)
        draw_text(x + 11, y + 4, text, cap, PAPER)
    else:
        fill_rect(x, y, bw, 3, RED)
        fill_rect(x, y + bh - 3, bw, 3, RED)
        fill_rect(x, y, 3, bh, RED)
        fill_rect(x + bw - 3, y, 3, bh, RED)
        draw_text(x + 11, y + 4, text, cap, RED)
    return bw


# --- layout ------------------------------------------------------------------
def draw_masthead():
    draw_text_centred(W / 2, 16, "THE WORLD TODAY", 64, INK)
    fill_rect(0, 96, W, 6, RED)


def draw_date_band():
    fill_rect(0, 102, W, 64, RED)
    draw_text_centred(W / 2, 112, "WEDNESDAY \u00b7 25 NOVEMBER 2026",
                      44, PAPER)


def draw_hero():
    # headline, two lines, cap 80
    draw_text_centred(W / 2, 178, "TANKERS HIT MINES,", 80, INK)
    draw_text_centred(W / 2, 272, "BURN IN HORMUZ", 80, INK)
    # sea band (drawn BEFORE the giant "2" so the digit sits on top)
    fill_rect(16, 436, W - 32, 62, TEAL)
    # waves
    for wx, wy in ((180, 452), (560, 462), (880, 452),
                   (330, 478), (700, 480), (940, 474)):
        fill_rect(wx, wy, 30, 3, WHITE)
    # mines in the water
    draw_mine(205, 468, 12)
    draw_mine(580, 472, 10)
    draw_mine(955, 466, 12)
    # two tankers
    draw_tanker(260, 498, 300)
    draw_tanker(620, 498, 290)
    # giant "2" (red, paper halo so it reads over the teal sea)
    draw_text(24, 356, "2", 150, RED, halo=7)
    # hero footer: subline / chip / source
    draw_text(24, 510, "STRAIT OF HORMUZ", 32, INK)
    draw_chip(392, 506, "MIDDLE EAST", 32, fill=True)
    draw_text_right(1000, 510, "REUTERS", 32, INK)


CARDS = [
    ("HUAWEI CONVICTED IN US TRIAL", "EAST ASIA", "REUTERS", pic_phone),
    ("AUSTRALIA SIGNS PACIFIC SECURITY PACT", "PACIFIC", "NEWS WIRES",
     pic_pact),
    ("UKRAINE STRIKES RUSSIAN ENERGY SITES", "EUROPE", "NEWS WIRES",
     pic_refinery),
    ("PAKISTAN'S FIRST ASTRONAUT REACHES TIANGONG", "SOUTH ASIA",
     "REUTERS", pic_rocket),
]


def draw_card(x0, y0, headline, region, source, pic):
    w, h = 488, 228
    # border
    fill_rect(x0, y0, w, 3, INK)
    fill_rect(x0, y0 + h - 3, w, 3, INK)
    fill_rect(x0, y0, 3, h, INK)
    fill_rect(x0 + w - 3, y0, 3, h, INK)
    # pictogram band (left) + region chip (right, same band)
    pic(x0 + 14, y0 + 10, 150, 48)
    chip_w = text_width(region, 32) + 22
    draw_chip(x0 + w - 14 - chip_w, y0 + 10, region, 32, fill=False)
    # headline, cap 38, up to 3 lines
    lines = wrap_text(headline, 38, w - 28, 3)
    yy = y0 + 60
    for line in lines:
        draw_text(x0 + 14, yy, line, 38, INK)
        yy += 42
    # source line
    draw_text(x0 + 14, y0 + 190, source, 32, INK)


def draw_cards():
    positions = [(16, 548), (520, 548), (16, 792), (520, 792)]
    for (x0, y0), (headline, region, source, pic) in zip(positions, CARDS):
        draw_card(x0, y0, headline, region, source, pic)


def build():
    new_canvas()
    draw_masthead()
    draw_date_band()
    draw_hero()
    draw_cards()
    return png_bytes()


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    sys.stdout.write("wrote %s (%d bytes)\n" % (path, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
