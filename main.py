#!/usr/bin/env python3
"""THE WORLD TODAY - news-image-20261125 entry.

Pure Python standard library only: hand-written PNG encoder (zlib) and a
tiny 5x7 bitmap font. No third-party imports, no network, no external assets.
Deterministic: no timestamps, no unseeded randomness (seeded RNG only).
Writes entry.png into $MAKEFUN_OUTPUT_DIR (default "out").
"""
import math
import os
import random
import struct
import zlib

W = 1024
H = 1024

# ---------------- palette ----------------
NAVY = (11, 26, 44)        # page background
PANEL = (14, 32, 54)       # hero panel background
CARD = (19, 42, 68)        # grid card background
BAND = (8, 21, 36)         # hero headline band
SCREEN = (10, 26, 46)      # monitor face
WHITE = (245, 247, 250)
MIST = (143, 184, 222)     # secondary text
GOLD = (232, 184, 75)
CYAN = (55, 200, 217)
GREEN = (74, 222, 128)
RED = (229, 72, 77)
YELLOW = (255, 197, 49)
ORANGE = (240, 138, 60)
DIMLINE = (40, 110, 150)   # network links
BORDER = (50, 80, 110)     # thin outlines

# ---------------- framebuffer ----------------
buf = bytearray(W * H * 3)


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        buf[i:i + len(row)] = row


def rect_outline(x, y, w, h, c, t=1):
    fill_rect(x, y, w, t, c)
    fill_rect(x, y + h - t, w, t, c)
    fill_rect(x, y, t, h, c)
    fill_rect(x + w - t, y, t, h, c)


def line(x0, y0, x1, y1, c, w=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if w == 1:
            put(x0, y0, c)
        else:
            fill_rect(x0 - w // 2, y0 - w // 2, w, w, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = math.isqrt(r * r - dy * dy)
        fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)


def circle_o(cx, cy, r, c, w=2):
    steps = max(24, int(2 * math.pi * r))
    for i in range(steps):
        a = 2 * math.pi * i / steps
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        fill_rect(x - w // 2, y - w // 2, w, w, c)


def poly(pts, c):
    """Scanline fill of a polygon given as [(x, y), ...]."""
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            a = int(xs[i])
            b = int(xs[i + 1])
            fill_rect(a, y, b - a + 1, 1, c)


def star_pts(cx, cy, r_out, r_in, n=5):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = -math.pi / 2 + i * math.pi / n
        pts.append((int(round(cx + r * math.cos(a))),
                    int(round(cy + r * math.sin(a)))))
    return pts


# ---------------- 5x7 bitmap font ----------------
# Each glyph: 7 rows of 5 bits ('1' = ink).
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
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
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
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '\u2014': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '\u00b7': ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def draw_text(x, y, s, scale, c):
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g:
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == '1':
                        fill_rect(cx + col * scale, y + r * scale,
                                  scale, scale, c)
        cx += 6 * scale


def draw_text_c(cx, y, s, scale, c):
    draw_text(cx - text_w(s, scale) // 2, y, s, scale, c)


def wrap(s, max_w, scale):
    """Greedy word wrap; returns a list of lines that fit max_w px."""
    lines = []
    cur = ''
    for wd in s.split(' '):
        t = wd if not cur else cur + ' ' + wd
        if text_w(t, scale) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ---------------- PNG encoder (stdlib only) ----------------
def _chunk(typ, data):
    out = struct.pack('>I', len(data)) + typ + data
    out += struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def save_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n'
           + _chunk(b'IHDR', ihdr)
           + _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + _chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)

# ---------------- pictograms ----------------
# Each takes a centre (cx, cy) and draws a flat, simple pictogram.


def pic_chip(cx, cy, col):
    # Microchip: square body, pins on all sides, inner die.
    rect_outline(cx - 22, cy - 22, 44, 44, col, 3)
    rect_outline(cx - 11, cy - 11, 22, 22, col, 2)
    for i in range(4):
        off = -15 + i * 10
        fill_rect(cx + off, cy - 31, 4, 9, col)   # top pins
        fill_rect(cx + off, cy + 22, 4, 9, col)   # bottom pins
        fill_rect(cx - 31, cy + off, 9, 4, col)   # left pins
        fill_rect(cx + 22, cy + off, 9, 4, col)   # right pins
    # Gavel tucked at the lower right: head + handle, kept inside the
    # pictogram zone so it never touches the label below.
    line(cx + 16, cy + 30, cx + 30, cy + 16, WHITE, 7)
    line(cx + 23, cy + 23, cx + 34, cy + 32, WHITE, 3)


def pic_ambulance(cx, cy, col):
    # Ambulance body + cab, red cross on the side, two wheels.
    fill_rect(cx - 36, cy - 14, 54, 28, WHITE)
    fill_rect(cx + 18, cy - 6, 20, 20, WHITE)
    fill_rect(cx - 20, cy - 8, 6, 16, RED)       # cross, vertical bar
    fill_rect(cx - 25, cy - 3, 16, 6, RED)       # cross, horizontal bar
    circle(cx - 22, cy + 17, 7, NAVY)
    circle_o(cx - 22, cy + 17, 7, WHITE, 2)
    circle(cx + 26, cy + 17, 7, NAVY)
    circle_o(cx + 26, cy + 17, 7, WHITE, 2)


def pic_tower_drone(cx, cy, col):
    # Tower (trapezoid + antenna + red beacon) with a drone above it.
    # Compact: the whole pictogram stays within cy-34 .. cy+30 so it
    # never crosses the panel's accent bar or the label below.
    poly([(cx - 14, cy + 30), (cx + 14, cy + 30),
          (cx + 7, cy - 2), (cx - 7, cy - 2)], MIST)
    line(cx, cy - 2, cx, cy - 10, MIST, 3)
    circle(cx, cy - 12, 3, RED)
    # Drone: white body + four rotor arms (white, so it stands out
    # against this panel's red accent bar).
    fill_rect(cx - 12, cy - 30, 24, 8, WHITE)
    line(cx - 12, cy - 26, cx - 22, cy - 34, WHITE, 3)
    line(cx + 12, cy - 26, cx + 22, cy - 34, WHITE, 3)
    line(cx - 12, cy - 23, cx - 22, cy - 16, WHITE, 3)
    line(cx + 12, cy - 23, cx + 22, cy - 16, WHITE, 3)
    circle(cx - 22, cy - 34, 3, WHITE)
    circle(cx + 22, cy - 34, 3, WHITE)
    circle(cx - 22, cy - 16, 3, WHITE)
    circle(cx + 22, cy - 16, 3, WHITE)


def pic_medal(cx, cy, col):
    # Ribbon in a V, gold medal with a star.
    poly([(cx - 18, cy - 34), (cx - 2, cy - 34),
          (cx + 4, cy - 2), (cx - 8, cy - 2)], RED)
    poly([(cx + 2, cy - 34), (cx + 18, cy - 34),
          (cx + 8, cy - 2), (cx - 4, cy - 2)], CYAN)
    circle(cx, cy + 12, 19, GOLD)
    circle_o(cx, cy + 12, 19, (190, 140, 40), 2)
    poly(star_pts(cx, cy + 12, 12, 5), WHITE)


def pic_cricket(cx, cy, col):
    # Stumps, angled bat, red ball with a seam.
    for i in range(3):
        fill_rect(cx - 38 + i * 7, cy - 2, 4, 28, GOLD)
    line(cx - 24, cy + 26, cx + 8, cy - 6, (210, 170, 120), 11)  # blade
    line(cx + 8, cy - 6, cx + 24, cy - 22, (210, 170, 120), 5)   # handle
    circle(cx + 32, cy + 16, 10, RED)
    line(cx + 24, cy + 10, cx + 40, cy + 22, WHITE, 2)


# ---------------- page composition ----------------
def draw_masthead():
    fill_rect(24, 44, 110, 4, GOLD)
    fill_rect(890, 44, 110, 4, GOLD)
    draw_text_c(512, 24, "THE WORLD TODAY", 8, WHITE)
    draw_text_c(512, 92, "WEDNESDAY 25 NOVEMBER 2026", 4, GOLD)
    fill_rect(24, 132, 976, 4, GOLD)
    fill_rect(24, 140, 976, 2, BORDER)


def draw_hero():
    fill_rect(24, 150, 976, 420, PANEL)
    rect_outline(24, 150, 976, 420, BORDER, 1)

    # "TOP STORY" tag.
    fill_rect(40, 162, 132, 28, GOLD)
    draw_text_c(106, 169, "TOP STORY", 2, NAVY)

    # Glowing monitors with fake code lines.
    screens = [
        (56, 208, 210, 120, CYAN),
        (290, 200, 240, 140, MIST),
        (556, 212, 170, 110, GREEN),
    ]
    for (sx, sy, sw, sh, oc) in screens:
        fill_rect(sx, sy, sw, sh, SCREEN)
        rect_outline(sx, sy, sw, sh, oc, 2)
        for i in range(5):
            ln = 60 + (i * 37) % (sw - 90)
            lc = GREEN if i % 2 == 0 else CYAN
            fill_rect(sx + 14, sy + 16 + i * 18, ln, 4, lc)

    # Abstract network under attack (seeded, deterministic).
    rng = random.Random(20261125)
    nodes = [(rng.randint(760, 970), rng.randint(180, 420))
             for _ in range(14)]
    for i in range(14):
        line(nodes[i][0], nodes[i][1],
             nodes[(i + 5) % 14][0], nodes[(i + 5) % 14][1], DIMLINE, 1)
        line(nodes[i][0], nodes[i][1],
             nodes[(i + 9) % 14][0], nodes[(i + 9) % 14][1], DIMLINE, 1)
    for (nx, ny) in nodes:
        circle(nx, ny, 5, CYAN)
    # Breach node: red, with thick red links.
    bx, by = nodes[3]
    line(bx, by, nodes[8][0], nodes[8][1], RED, 3)
    line(bx, by, nodes[12][0], nodes[12][1], RED, 3)
    circle(bx, by, 10, RED)
    circle_o(bx, by, 15, RED, 2)

    # Warning triangle, top right of the scene.
    poly([(905, 196), (968, 306), (842, 306)], YELLOW)
    draw_text_c(905, 240, "!", 4, NAVY)

    # Headline band.
    fill_rect(24, 440, 976, 130, BAND)
    fill_rect(24, 440, 976, 3, GOLD)
    draw_text_c(512, 452, "US SPY AGENCIES HIT", 6, WHITE)
    draw_text_c(512, 498, "BY CYBERATTACK", 6, WHITE)
    draw_text_c(512, 548,
                "CNN: CIA AND SPY CHIEF'S OFFICE BREACHED \u2014 "
                "CLASSIFIED DATA AFFECTED", 2, MIST)


def draw_panel(x, y, w, h, accent, pic, label, fact):
    fill_rect(x, y, w, h, CARD)
    rect_outline(x, y, w, h, BORDER, 1)
    fill_rect(x, y, w, 6, accent)
    cx = x + w // 2
    pic(cx, y + 44, accent)
    lines = wrap(label, w - 16, 3)
    ly = y + 80
    for ln in lines:
        draw_text_c(cx, ly, ln, 3, WHITE)
        ly += 25
    flines = wrap(fact, w - 16, 2)
    fy = ly + 8
    for ln in flines:
        draw_text_c(cx, fy, ln, 2, MIST)
        fy += 17


def draw_grid():
    # Row 1: three panels.
    draw_panel(24, 585, 304, 185, GOLD, pic_chip,
               "HUAWEI GUILTY IN US TRIAL",
               "JURY FINDS HUAWEI GUILTY ON 10 OF 12 COUNTS")
    draw_panel(344, 585, 304, 185, GREEN, pic_ambulance,
               "WHO EVACUATES STAFF IN CONGO",
               "5,775 DEATHS OF 11,762 EBOLA CASES IN CONGO")
    draw_panel(664, 585, 304, 185, RED, pic_tower_drone,
               "HOUTHI DRONE HITS RIYADH",
               "ELEVEN PEOPLE INJURED IN RIYADH TOWER ATTACK")
    # Row 2: two wider panels.
    draw_panel(24, 785, 480, 155, CYAN, pic_medal,
               "TRUMP HONOURS GIULIANI",
               "MEDAL OF FREEDOM FOR EX-NYC MAYOR")
    draw_panel(528, 785, 480, 155, ORANGE, pic_cricket,
               "ENGLAND LEVEL T20 SERIES",
               "EIGHT-WICKET WIN OVER AUSTRALIA, CHASING 185")


def draw_footer():
    fill_rect(24, 950, 976, 2, BORDER)
    draw_text_c(512, 962, "25 NOVEMBER 2026 \u00b7 THE WORLD IN ONE IMAGE",
                2, MIST)


def main():
    fill_rect(0, 0, W, H, NAVY)
    draw_masthead()
    draw_hero()
    draw_grid()
    draw_footer()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out, exist_ok=True)
    save_png(os.path.join(out, "entry.png"))


if __name__ == "__main__":
    main()
