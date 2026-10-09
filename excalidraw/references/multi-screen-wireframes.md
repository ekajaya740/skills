# Multi-Screen Wireframe Patterns in Excalidraw

For web or mobile app wireframes that need multiple screens laid out in a single canvas.

## Why do this in Excalidraw?

- Free, offline, no API key
- Hand-drawn feel is perfect for lo-fi / mid-fi wireframes
- Drag onto excalidraw.com and the whole grid opens at once
- Easy to annotate arrows between screens for user-flow documentation

## Grid layout conventions

| Screen size | Typical `SCREEN_W` × `SCREEN_H` | Notes |
|-------------|----------------------------------|-------|
| Desktop web | 1280 × 900 | Good default for full-page wireframes |
| Tablet | 820 × 1024 | iPad-ish portrait |
| Mobile | 390 × 850 | iPhone-ish |

Leave a gutter between screens:

```python
GAP_X, GAP_Y = 100, 80
x = col * (SCREEN_W + GAP_X)
y = row * (SCREEN_H + GAP_Y)
```

## Reusable component pattern

Build helpers that generate Excalidraw element dicts. Keep an `E = []` list and append.

```python
def R(id, x, y, w, h, bg='transparent', sc='#D1D5DB', sw=1, rd=0, fill='solid'):
    e = {
        'type': 'rectangle', 'id': id, 'x': x, 'y': y, 'width': w, 'height': h,
        'strokeColor': sc, 'backgroundColor': bg, 'fillStyle': fill,
        'strokeWidth': sw, 'roughness': 0, 'opacity': 100, 'boundElements': []
    }
    if rd: e['roundness'] = {'type': rd}
    return e

def T(id, x, y, text, size=16, color='#1F2937', align='left', valign='top', w=None, h=None):
    lines = text.split('\n')
    lc = len(lines)
    mc = max(len(l) for l in lines) if lines else len(text)
    tw = w if w else min(mc * size * 0.55 + 20, 900)
    th = h if h else (lc * size * 1.3 + 8)
    return {
        'type': 'text', 'id': id, 'x': x, 'y': y, 'width': tw, 'height': th,
        'text': text, 'fontSize': size, 'fontFamily': 2, 'strokeColor': color,
        'textAlign': align, 'verticalAlign': valign,
        'originalText': text, 'autoResize': True
    }

def BT(id, x, y, w, h, text, bg='#E87A2F', color='#FFFFFF'):
    rect = R(id, x, y, w, h, bg, bg, 0, 3, 'solid')
    rect['boundElements'] = [{'id': f'{id}_t', 'type': 'text'}]
    t = T(f'{id}_t', x, y, text, 14, color, 'center', 'middle', w, h)
    t['containerId'] = id
    return [rect, t]

def IMG(id, x, y, w, h):
    """Image placeholder: hachure-filled gray box with ☒ icon."""
    els = [R(f'{id}_bg', x, y, w, h, '#E5E7EB', BORDER, 1, 2, 'hachure')]
    cx = x + w // 2 - 10
    cy = y + h // 2 - 14
    els.append(T(f'{id}_x', cx, cy, '☒', 28, '#9CA3AF', 'center', 'middle', w=24, h=32))
    return els

def CARD(id, x, y, w, h, title='', sub='', price='', badge=None):
    out = [R(id, x, y, w, h, '#FFFFFF', '#D1D5DB', 1, 3)]
    ih = int(h * 0.45)
    out += IMG(f'{id}_img', x+1, y+1, w-2, ih-2)
    if title: out.append(T(f'{id}_t', x+12, y+ih+10, title, 15, '#1F2937', w=w-24))
    if sub: out.append(T(f'{id}_s', x+12, y+ih+32, sub, 13, '#6B7280', w=w-24))
    if price: out.append(T(f'{id}_p', x+12, y+h-30, price, 16, '#6B7280', w=w-24))
    if badge:
        bw = len(badge) * 9 + 16
        out.append(R(f'{id}_b', x+w-bw-8, y+8, bw, 22, '#6B7280', '#6B7280', 0, 2))
        out.append(T(f'{id}_bt', x+w-bw+2, y+11, badge, 11, '#FFFFFF'))
    return out
```

## Screen-frame helper

```python
def FRAME(col, row, title, E):
    x = col * (SCREEN_W + GAP_X)
    y = row * (SCREEN_H + GAP_Y)
    E.append(R(f'f{col}{row}', x, y, SCREEN_W, SCREEN_H, BG, BORDER, 2, 0))
    E.append(T(f'fl{col}{row}', x+20, y+8, title, 20, '#2D2D2D'))
    return x, y
```

## Common screen primitives

### Navbar
```python
def NAV(x, y, w, active='', E):
    h = 60
    E.append(R(f'n{x}{y}', x, y, w, h, '#FFFFFF', '#D1D5DB', 1, 0, 'solid'))
    E.append(T(f'nb{x}', x+24, y+18, 'Brand', 18, '#6B7280'))
    # ...nav items...
    return h
```

### Footer
```python
def FT(x, y, w, E):
    E.append(R(f'ft{x}', x, y, w, 50, '#FFFFFF', '#D1D5DB', 1, 0))
    E.append(T(f'ftt{x}', x+24, y+16, '© Footer text', 13, '#6B7280'))
```

### Admin sidebar
```python
SIDEBAR_W = 260  # matches standard Bootstrap admin layout (not 220!)
CONTENT_W = SCREEN_W - SIDEBAR_W - 40  # = 980 for SCREEN_W=1280

def SB(x, y, w, h, active_index, E):
    E.append(R(f'sb{x}', x, y, w, h, '#FFFFFF', '#D1D5DB', 1, 0))
    E.append(T(f'sbtl{x}', x+20, y+20, 'Admin', 16, '#6B7280'))
    menu = ['Dashboard', 'Produk', 'Layanan', 'Pesanan', 'Pelanggan']
    for i, label in enumerate(menu):
        yy = y + 100 + i * 44
        if i == active_index:
            E.append(R(f'sbm_{x}_{i}', x+5, yy-4, w-10, 34, '#E5E7EB', '#E5E7EB', 0, 3))
        E.append(T(f'sbt_{x}_{i}', x+20, yy, label, 14, '#6B7280' if i == active_index else '#6B7280'))
```

## Critical pitfall: admin table column widths must fill CONTENT_W

When building admin tables with `TH_ROW` / `TD_ROW`, the sum of column widths + 20 (padding) **must approximately equal `CONTENT_W`** (980px for SCREEN_W=1280). Tables that are only half the content width look broken.

**Verify** after defining column widths:
```python
assert abs(sum(widths) + 20 - CONTENT_W) <= 60, f"Table too narrow/wide: {sum(widths)+20} vs {CONTENT_W}"
```

Column width guidance for admin tables:
- text-heavy columns (name, email): 200-300px
- medium columns (phone, status): 100-160px
- narrow columns (stock, ID): 50-100px
- action columns (Edit | Hapus): 160-240px

## Critical pitfall: navbar item overlap

For medium-fidelity wireframes that avoid brand colors and present a neutral, professional look, use the grayscale Tailwind-style palette:

| Role | Hex | Notes |
|------|-----|-------|
| Primary (buttons, links) | `#6B7280` (gray-500) | Replaces brand orange/green |
| Primary light (highlights) | `#D1D5DB` (gray-300) | Replaces brand-light fills |
| Image placeholder bg | `#E5E7EB` (gray-200) | Light box for image areas |
| Image placeholder X icon | `#9CA3AF` (gray-400) | `☒` symbol color |
| Dark accent / hero bg | `#4B5563` (gray-600) | Dark backgrounds |
| Darkest accent | `#374151` (gray-700) | Near-black for emphasis |
| Text primary | `#1F2937` (gray-800) | Headings |
| Text secondary | `#6B7280` (gray-500) | Descriptions, labels |
| Borders & dividers | `#D1D5DB` (gray-300) | Lines, card borders |
| Screen background | `#F9FAFB` (gray-50) | Canvas bg |
| Light backgrounds | `#F3F4F6` (gray-100) | Sections, stripes |
| Canvas view background | `#f3f4f6` | appState |

To convert a brand-colored script to grayscale, replace the design-system variables:
```python
# Brand-colored
P = '#E87A2F'; PL = '#FDEBD0'; S = '#2FA87A'
BG = '#FFF8F0'; TX = '#2D2D2D'; TXL = '#6C757D'; BD = '#E8E0D8'

# Grayscale
P = '#6B7280'; PL = '#D1D5DB'; S = '#9CA3AF'
BG = '#F9FAFB'; TX = '#1F2937'; TXL = '#6B7280'; BD = '#D1D5DB'
```

**Also search for any hardcoded hex colors** (e.g. `#E8E0D8`, `#FDEBD0`) and replace them with the corresponding gray token.

## Critical pitfall: navbar item overlap

When building navbars with multi-word items (e.g., "Riwayat", "Layanan"), fixed per-item spacing can cause overlap with adjacent items like a "Masuk" button.

**WRONG** (70px step — "Riwayat" at ~74px wide overlaps "Masuk"):
```python
nx = x + w - 420
for item in items:
    E.append(T(f'n{item}', nx, y+20, item, 14, clr))
    nx += 70  # too tight
```

**CORRECT** — start the nav group further left, use 80px steps, and place "Masuk" with an explicit right-edge offset:
```python
nx = x + w - 530
for item in items:
    E.append(T(f'n{item}', nx, y+20, item, 14, clr))
    nx += 80
E.append(T(f'nl{x}', x + w - 90, y+20, 'Masuk', 14, TXL))
```

**Verify**: last nav item's right edge (`x + text_width`) must be ≥30px before the next element.

## Critical pitfall: admin dashboard column layout

Real Bootstrap admin dashboards use a **col-lg-8 / col-lg-4 split**, not a full-width stacked layout. The recent orders table sits in the wider left column (~66%), and quick-action buttons sit in the narrower right column (~33%). They are side-by-side.

Additionally, stat cards are **horizontal** (icon circle left + label/value right), not vertical tall cards.

```python
left_w = int(CONTENT_W * 0.66) - 15
right_w = CONTENT_W - left_w - 30
```

## Critical pitfall: form file-upload fields must not use IMG() placeholder

In admin add/edit forms, the "image upload" field is a **file input**, not an image preview box. Using `IMG()` (hachure-filled gray box) for the file upload field creates a 120px-tall element that overlaps the next form field because the `fy` increment is typically only 60px per field.

**WRONG** — IMG placeholder overlaps next field:
```python
E += IMG('apf_img', cx+15, fy+18, 200, 120)   # 120px tall!
fy += 60   # way too small for 120px element
```

**CORRECT** — use a standard file input row (same height as other inputs):
```python
E.append(R(f'apf_in{i}', cx+15, fy+18, CONTENT_W-30, 38, W, BD, 1, 3))
E.append(T(f'apf_ph{i}', cx+25, fy+24, 'Pilih Gambar ▾', 13, TXL))
E.append(T(f'apf_hint{i}', cx+15, fy+60, '(jpg, png, max 5MB)', 11, TXL))
fy += 70 + 30  # field_h + gap
```

> `IMG()` hachure placeholders are for displaying existing images (product gallery, hero banner, about section). File upload fields in forms should look like text inputs.

## Critical pitfall: product table image column comes first

The standard admin product table column order is `Gambar | Nama | Harga | Stok | Aksi` — image thumbnail is the first column. "Aksi" (actions) is right-aligned (`text-end`).

```python
hw = [80, 360, 160, 100, 180]  # Gambar(80) + Nama(360) + Harga(160) + Stok(100) + Aksi(180)
TH_ROW(['Gambar','Nama','Harga','Stok','Aksi'], hw, cx, ny)
# Small thumbnail in data row:
E += IMG(f'pimg{r}', cx+10, ry+2, 40, 40)
```

## Critical building pitfall: execute_code does NOT persist variables

`execute_code` runs in a **fresh Python sandbox per call**. Any variables, imports, or helper functions defined in one call **will be gone on the next call**.

**WRONG approach** (builds in multiple separate execute_code calls):
```python
# Call 1: defines helpers
E = []
def R(...): ...
def CARD(...): ...

# Call 2: NameError — R and CARD are gone
```

**CORRECT approach**: Write the complete script as a file via `write_file`, then run it via `terminal`:

```bash
python3 /tmp/build_wireframes.py
```

Or build everything in a **single** `execute_code` call.

## Critical pitfall: product/card grid alignment

When laying out cards in a grid (e.g., 3 products per row), **always compute card width to fill the available space evenly**. Hardcoding a fixed card width (e.g., `PW = 270`) often leaves a gap on the right side of the screen.

**WRONG** (fixed width leaves empty space on right):
```python
PW = 270  # 4 * 270 = 1080 → right side has 200px gap
CG = (SCREEN_W - 80 - 4 * PW) // 3  # awkward remainder
```

**CORRECT** (compute card width from available space):
```python
MARGIN = 40
COL_GAP = 30
NUM_COLS = 3
PW = (SCREEN_W - 2 * MARGIN - (NUM_COLS - 1) * COL_GAP) // NUM_COLS
# 1280 - 80 - 60 = 1140 → 1140 / 3 = 380 per card → fills perfectly
```

**Verify** after generating: check that the rightmost card's right edge (`x + width`) is within ~40px of the screen frame's right edge (`frame_x + SCREEN_W - MARGIN`).

## Section headers (admin vs. user separation)

When wireframes span both user-facing and admin screens, **visually separate them with full-width banner labels**. Place a dark banner above each section group:

```python
def SECTION_LABEL(x, y, label, width):
    """Full-width section banner to separate logical groups"""
    E.append(R(f'sec_{label}', x, y, width, 80, '#374151', '#374151', 0, 0))
    E.append(T(f'sectl_{label}', x + 30, y + 22, label, 28, '#FFFFFF',
               'left', 'middle', w=len(label) * 16, h=36))

# Place above the first row of each section group:
SECTION_LABEL(0, row_start_y - 100, 'USER-FACING SCREENS', full_grid_w)
SECTION_LABEL(0, admin_row_start_y - 100, 'ADMIN SCREENS', full_grid_w)
```

Position the banner with enough vertical gap before the first screen frame so it doesn't overlap.

## Typical admin screen inventory (CRUD apps)

When wireframing an admin panel for a CRUD-style web app, the typical screen set includes:

| Screen | Sections |
|--------|----------|
| **Dashboard** | 4 stat cards (customers, orders, pending, services), recent orders table, quick action buttons |
| **Customers — List** | Header + "Add" button, search bar, table (name, phone, email, pet count, actions) |
| **Customers — Detail** | Breadcrumb, info card (name/phone/email/address), order history table |
| **Products — List** | Header + "Add" button, search bar, table (image thumb, name, price, stock, actions incl. stock adjust) |
| **Products — Add/Edit** | Breadcrumb, form card (name, description, price, image upload, stock qty) |
| **Services — List** | Header + "Add" button, table (name, description, price, duration, actions) |
| **Services — Add/Edit** | Breadcrumb, form card (name, description, price, duration) |
| **Orders — List** | Header, status filter dropdown, table (id, customer, pet, service, date, status, total, actions) |
| **Orders — Detail** | Breadcrumb, order info card, status flow visualization (3-step progress), action buttons (confirm/complete/cancel) |
| **Feedback** | Rating summary (avg + stars + count), rating filter, feedback table (name, phone, rating, comment, date) |

Admin sidebar typically shows: Dashboard, Pelanggan, Produk, Layanan, Pesanan, Umpan Balik + Keluar (logout).

Use `SB()` helper for sidebar, `STAT_CARD()` for dashboard stats, `TH_ROW()` / `TD_ROW()` for tables, and status flow visualization with connected circles/rectangles for order detail.

## Saving the result

```python
import json

diagram = {
    "type": "excalidraw",
    "version": 2,
    "source": "hermes-agent",
    "elements": E,
    "appState": {"viewBackgroundColor": "#f5f5f5"}
}

with open('my-wireframes.excalidraw', 'w') as f:
    json.dump(diagram, f)
```

## Text-width estimation rule

Text width depends on the font family:
- **Virgil** (`fontFamily: 1`): roughly `0.58 × fontSize` per character for average-width text
- **Helvetica** (`fontFamily: 2`): roughly `0.55 × fontSize` per character (tighter)

```python
# Virgil
text_width = max_line_length * font_size * 0.58 + padding

# Helvetica
text_width = max_line_length * font_size * 0.55 + padding
```

Line height also differs:
- **Virgil**: `fontSize * 1.4 + 8`
- **Helvetica**: `fontSize * 1.3 + 8` (tighter leading)

Always give text elements an explicit `width` and `height` so they render correctly when the file is opened.
