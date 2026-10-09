#!/usr/bin/env python3
"""
Starter template for building multi-screen Excalidraw wireframes.

Usage:
  1. Edit the `E = []` list below — add your screens using the helpers.
  2. Run: python3 build_wireframe.py
  3. Drag the generated .excalidraw file onto excalidraw.com

For grayscale wireframes, use the GRAYSCALE palette below.
For brand-colored wireframes, swap to the BRAND palette.
For formal/clean look, use FONT_FAMILY=2 (Helvetica) and ROUGHNESS=0.
For hand-drawn/sketch look, use FONT_FAMILY=1 (Virgil) and ROUGHNESS=1.
"""
import json

# === STYLE CONFIG ===

# Font: 1 = Virgil (hand-drawn), 2 = Helvetica (formal/clean)
FONT_FAMILY = 2
# Roughness: 0 = crisp lines, 1 = hand-drawn wobble
ROUGHNESS = 0

# Text-width multiplier: 0.55 for Helvetica, 0.58 for Virgil
CHAR_WIDTH_FACTOR = 0.55 if FONT_FAMILY == 2 else 0.58
# Line height multiplier: 1.3 for Helvetica, 1.4 for Virgil
LINE_HEIGHT_FACTOR = 1.3 if FONT_FAMILY == 2 else 1.4

# === DESIGN SYSTEM — Choose one palette ===

# Grayscale palette (medium-fidelity wireframes)
PRIMARY = '#6B7280'
PRIMARY_LIGHT = '#D1D5DB'
SECONDARY = '#9CA3AF'
BG = '#F9FAFB'
TEXT = '#1F2937'
TEXT_LIGHT = '#6B7280'
BORDER = '#D1D5DB'
WHITE = '#FFFFFF'
LIGHT = '#F3F4F6'
IMG_BG = '#E5E7EB'
IMG_X = '#9CA3AF'
DARK_ACCENT = '#374151'
DARKEST = '#4B5563'

# Brand palette (high-fidelity mockups) — uncomment to use
# PRIMARY = '#E87A2F'
# PRIMARY_LIGHT = '#FDEBD0'
# SECONDARY = '#2FA87A'
# BG = '#FFF8F0'
# TEXT = '#2D2D2D'
# TEXT_LIGHT = '#6C757D'
# BORDER = '#E8E0D8'
# WHITE = '#FFFFFF'
# LIGHT = '#F8F9FA'
# IMG_BG = '#FDEBD0'
# IMG_X = '#E87A2F'
# DARK_ACCENT = '#28A745'
# DARKEST = '#E87A2F'

# === CANVAS GRID ===
SCREEN_W, SCREEN_H = 1280, 900
GAP_X, GAP_Y = 100, 80
MARGIN = 40
COL_GAP = 30

# Admin layout constants
SIDEBAR_W = 260  # matches standard Bootstrap admin layout
CONTENT_W = SCREEN_W - SIDEBAR_W - 40  # = 980
CONTENT_X_OFF = SIDEBAR_W + 20

E = []


def R(id, x, y, w, h, bg='transparent', sc=BORDER, sw=1, rd=0, fill='solid'):
    e = {
        'type': 'rectangle', 'id': id, 'x': x, 'y': y, 'width': w, 'height': h,
        'strokeColor': sc, 'backgroundColor': bg, 'fillStyle': fill,
        'strokeWidth': sw, 'roughness': ROUGHNESS, 'opacity': 100, 'boundElements': []
    }
    if rd:
        e['roundness'] = {'type': rd}
    return e


def T(id, x, y, text, size=16, color=TEXT, align='left', valign='top', w=None, h=None):
    lines = text.split('\n')
    lc = len(lines)
    mc = max(len(l) for l in lines) if lines else len(text)
    tw = w if w else min(mc * size * CHAR_WIDTH_FACTOR + 20, 900)
    th = h if h else (lc * size * LINE_HEIGHT_FACTOR + 8)
    return {
        'type': 'text', 'id': id, 'x': x, 'y': y, 'width': tw, 'height': th,
        'text': text, 'fontSize': size, 'fontFamily': FONT_FAMILY, 'strokeColor': color,
        'textAlign': align, 'verticalAlign': valign,
        'originalText': text, 'autoResize': True
    }


def BT(id, x, y, w, h, text, bg=PRIMARY, color='#FFFFFF'):
    rect = R(id, x, y, w, h, bg, bg, 0, 3, 'solid')
    rect['boundElements'] = [{'id': f'{id}_t', 'type': 'text'}]
    t = T(f'{id}_t', x, y, text, 14, color, 'center', 'middle', w, h)
    t['containerId'] = id
    return [rect, t]


def IMG(id, x, y, w, h):
    """Image placeholder: hachure-filled gray box with ☒ in center."""
    els = [R(f'{id}_bg', x, y, w, h, IMG_BG, BORDER, 1, 2, 'hachure')]
    cx = x + w // 2 - 12
    cy = y + h // 2 - 14
    els.append(T(f'{id}_x', cx, cy, '☒', 28, IMG_X, 'center', 'middle', w=24, h=32))
    return els


def CARD(id, x, y, w, h, title='', sub='', price='', badge=None):
    out = [R(id, x, y, w, h, WHITE, BORDER, 1, 3)]
    ih = int(h * 0.45)
    out += IMG(f'{id}_img', x + 1, y + 1, w - 2, ih - 2)
    if title:
        out.append(T(f'{id}_t', x + 14, y + ih + 12, title, 15, TEXT, w=w - 28))
    if sub:
        out.append(T(f'{id}_s', x + 14, y + ih + 34, sub, 13, TEXT_LIGHT, w=w - 28))
    if price:
        out.append(T(f'{id}_p', x + 14, y + h - 32, price, 16, PRIMARY, w=w - 28))
    if badge:
        bw = len(badge) * 9 + 16
        out.append(R(f'{id}_b', x + w - bw - 8, y + 8, bw, 22, PRIMARY, PRIMARY, 0, 2))
        out.append(T(f'{id}_bt', x + w - bw + 2, y + 11, badge, 11, '#FFFFFF'))
    return out


def FRAME(col, row, title):
    x = col * (SCREEN_W + GAP_X)
    y = row * (SCREEN_H + GAP_Y)
    E.append(R(f'f{col}{row}', x, y, SCREEN_W, SCREEN_H, BG, BORDER, 2, 0))
    E.append(T(f'fl{col}{row}', x + 20, y + 8, title, 18, TEXT_LIGHT))
    return x, y


def NAV(x, y, w, active=''):
    h = 60
    E.append(R(f'n{x}{y}', x, y, w, h, WHITE, BORDER, 1, 0, 'solid'))
    E.append(T(f'nb{x}', x + 24, y + 18, 'Brand', 18, PRIMARY))
    items = [('Home', 'home'), ('Products', 'products'), ('Services', 'services')]
    nx = x + w - 300
    for label, key in items:
        clr = PRIMARY if key == active else TEXT_LIGHT
        E.append(T(f'n{key}', nx, y + 20, label, 14, clr))
        nx += 80
    return h


def FOOTER(x, y, w):
    E.append(R(f'ft{x}', x, y, w, 50, WHITE, BORDER, 1, 0))
    E.append(T(f'ftt{x}', x + 24, y + 16, '© Footer', 13, TEXT_LIGHT))


def SECTION_LABEL(x, y, label, width):
    """Full-width section banner to separate logical screen groups (user vs admin)."""
    E.append(R(f'sec_{label}', x, y, width, 70, DARK_ACCENT, DARK_ACCENT, 0, 0))
    E.append(T(f'sectl_{label}', x + 30, y + 18, label, 24, '#FFFFFF',
               'left', 'middle', w=len(label) * 14, h=32))


def SB(x, y, w, h, active_index=0, menu=None):
    """Admin sidebar with nav items and logout at bottom."""
    if menu is None:
        menu = ['Dashboard', 'Products', 'Services', 'Orders', 'Customers']
    E.append(R(f'sb{x}', x, y, w, h, WHITE, BORDER, 1, 0))
    E.append(T(f'sbtl{x}', x + 20, y + 20, 'Admin', 16, PRIMARY))
    E.append(T(f'sbad{x}', x + 20, y + 50, 'Panel', 12, TEXT_LIGHT))
    E.append(R(f'sbln{x}', x + 10, y + 75, w - 20, 1, BORDER, BORDER, 0, 0))
    for i, label in enumerate(menu):
        yy = y + 100 + i * 44
        if i == active_index:
            E.append(R(f'sbm_{x}_{i}', x + 5, yy - 4, w - 10, 34, '#E5E7EB', '#E5E7EB', 0, 3))
        E.append(T(f'sbt_{x}_{i}', x + 20, yy, label, 14, PRIMARY if i == active_index else TEXT_LIGHT))
    E.append(T(f'sbout{x}', x + 20, y + h - 40, 'Logout', 14, '#4B5563'))


def STAT_CARD(id, x, y, label, val, clr=PRIMARY):
    """Dashboard stat card: horizontal layout with icon circle left, label+value right."""
    E.append(R(id, x, y, 237, 70, WHITE, BORDER, 1, 6))
    E.append(R(f'{id}_ic', x + 12, y + 8, 48, 48, clr, clr, 0, 24, 'solid'))
    E.append(T(f'{id}_l', x + 72, y + 8, label, 12, TEXT_LIGHT, w=150))
    E.append(T(f'{id}_v', x + 72, y + 28, val, 22, TEXT))


def TH_ROW(headers, widths, x, y):
    """Table header row."""
    E.append(R(f'thdr_{x}_{y}', x, y, sum(widths) + 20, 36, LIGHT, LIGHT, 0, 0))
    hx = x + 10
    for i, h in enumerate(headers):
        E.append(T(f'th_{x}_{y}_{i}', hx, y + 10, h, 12, TEXT))
        hx += widths[i]


def TD_ROW(vals, widths, x, y, colors=None):
    """Table data row. colors: dict of {col_index: color} for overrides."""
    if colors is None:
        colors = {}
    hx = x + 10
    for i, v in enumerate(vals):
        clr = colors.get(i, TEXT)
        E.append(T(f'td_{x}_{y}_{i}', hx, y + 8, v, 12, clr))
        hx += widths[i]


def assert_table_fits(widths, content_w=980):
    """Assert table header width fits the admin content area."""
    table_w = sum(widths) + 20
    assert abs(table_w - content_w) <= 60, \
        f"Table width {table_w}px doesn't fill content area {content_w}px (gap={content_w - table_w}px)"


def compute_card_width(num_cols, margin=MARGIN, col_gap=COL_GAP):
    """Compute card width to fill available screen width evenly."""
    return (SCREEN_W - 2 * margin - (num_cols - 1) * col_gap) // num_cols


# ============================================================
# ADD YOUR SCREENS BELOW
# ============================================================

# Section header example:
# SECTION_LABEL(0, row_y - 100, 'USER-FACING SCREENS', 3 * SCREEN_W + 2 * GAP_X)

# Example: One screen with hero + 3-column card grid aligned to edges
sx, sy = FRAME(0, 0, 'Screen 1')
ny = sy + NAV(sx, sy, SCREEN_W)
E.append(R('hero', sx, ny, SCREEN_W, 300, DARKEST, DARKEST, 0, 0))
E += IMG('hero_img', sx, ny, SCREEN_W, 200)
E.append(T('hero_t', sx + 40, ny + 60, 'Hero Title', 40, '#FFFFFF'))
E += BT('hero_btn', sx + 40, ny + 200, 180, 48, 'Call to Action')
ny += 340

# Cards: compute width to fill screen evenly
card_w = compute_card_width(3)
for i in range(3):
    cx = sx + MARGIN + i * (card_w + COL_GAP)
    E += CARD(f'c{i}', cx, ny, card_w, 240, f'Card {i+1}', 'Description', '$99')
FOOTER(sx, (0 + 1) * (SCREEN_H + GAP_Y) - 60, SCREEN_W)

# ============================================================
# SAVE
# ============================================================
diagram = {
    'type': 'excalidraw',
    'version': 2,
    'source': 'hermes-agent-wireframe-template',
    'elements': E,
    'appState': {'viewBackgroundColor': '#f3f4f6'}
}

OUTPUT = 'my-wireframes.excalidraw'
with open(OUTPUT, 'w') as f:
    json.dump(diagram, f)

print(f'Written {len(E)} elements to {OUTPUT}')