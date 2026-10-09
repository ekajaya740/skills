---
name: excalidraw
description: "Hand-drawn Excalidraw JSON diagrams (arch, flow, seq)."
version: 1.0.0
author: ekajaya740
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Excalidraw, Diagrams, Flowcharts, Architecture, Visualization, JSON]
    related_skills: []

---

# Excalidraw Diagram Skill

Create diagrams by writing standard Excalidraw element JSON and saving as `.excalidraw` files. These files can be drag-and-dropped onto [excalidraw.com](https://excalidraw.com) for viewing and editing. No accounts, no API keys, no rendering libraries -- just JSON.

## Multi-Screen Wireframes

For building multi-screen web or app wireframes in a single `.excalidraw` file,
see `references/multi-screen-wireframes.md` for the full pattern (grid layout,
reusable component helpers, navbar, sidebar, footer primitives), and
`scripts/build_wireframe.py` for a ready-to-run starter template.

## When to use

Generate `.excalidraw` files for architecture diagrams, flowcharts, sequence diagrams, concept maps, and more. Files can be opened at excalidraw.com or uploaded for shareable links.

## Font & Roughness Styles

Excalidraw supports two font families that dramatically change the feel:

| fontFamily | Font | Use for |
|------------|------|---------|
| `1` | Virgil (hand-drawn) | Lo-fi sketches, brainstorming, informal |
| `2` | Helvetica (clean/formal) | Mid-fi wireframes, professional deliverables, client reviews |

**Roughness** controls line shakiness:
| roughness | Look | Use for |
|-----------|------|---------|
| `1` | Hand-drawn wobble | Lo-fi sketches, Virgil font |
| `0` | Crisp / straight lines | Mid-fi wireframes, Helvetica font |

> **Tip:** When the user says "formal", "solid", "clean", "professional", or "medium-fidelity", switch to `fontFamily: 2` and `roughness: 0`. Default to `fontFamily: 1` / `roughness: 1` only for casual sketches.

When using `fontFamily: 2`, use a slightly tighter text-width multiplier (`0.55` vs `0.58` for Virgil):
```python
tw = w if w else min(mc * size * 0.55 + 20, 900)  # Helvetica
tw = w if w else min(mc * size * 0.58 + 20, 900)  # Virgil
```

## Workflow

1. **Load this skill** (you already did)
2. **Write the elements JSON** -- an array of Excalidraw element objects
3. **Save the file** using `write_file` to create a `.excalidraw` file
4. **Optionally upload** for a shareable link using `scripts/upload.py` via `terminal`

### Saving a Diagram

Wrap your elements array in the standard `.excalidraw` envelope and save with `write_file`:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes-agent",
  "elements": [ ...your elements array here... ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

Save to any path, e.g. `~/diagrams/my_diagram.excalidraw`.

### Uploading for a Shareable Link

Run the upload script (located in this skill's `scripts/` directory) via terminal:

```bash
python skills/diagramming/excalidraw/scripts/upload.py ~/diagrams/my_diagram.excalidraw
```

This uploads to excalidraw.com (no account needed) and prints a shareable URL. Requires the `cryptography` pip package (`pip install cryptography`).

---

## Element Format Reference

### Required Fields (all elements)
`type`, `id` (unique string), `x`, `y`, `width`, `height`

### Defaults (skip these -- they're applied automatically)
- `strokeColor`: `"#1e1e1e"`
- `backgroundColor`: `"transparent"`
- `fillStyle`: `"solid"`
- `strokeWidth`: `2`
- `roughness`: `1` (hand-drawn look; set `0` for formal/clean)
- `opacity`: `100`

Canvas background is white.

### Element Types

**Rectangle**:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```
- `roundness: { "type": 3 }` for rounded corners
- `backgroundColor: "#a5d8ff"`, `fillStyle: "solid"` for filled

**Ellipse**:
```json
{ "type": "ellipse", "id": "e1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Diamond**:
```json
{ "type": "diamond", "id": "d1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Labeled shape (container binding)** -- create a text element bound to the shape:

> **WARNING:** Do NOT use `"label": { "text": "..." }` on shapes. This is NOT a valid
> Excalidraw property and will be silently ignored, producing blank shapes. You MUST
> use the container binding approach below.

The shape needs `boundElements` listing the text, and the text needs `containerId` pointing back:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{ "id": "t_r1", "type": "text" }] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```
- Works on rectangle, ellipse, diamond
- Text is auto-centered by Excalidraw when `containerId` is set
- The text `x`/`y`/`width`/`height` are approximate -- Excalidraw recalculates them on load
- `originalText` should match `text`
- Always include `fontFamily: 1` (Virgil/hand-drawn font) or `fontFamily: 2` (Helvetica/formal) — see Font & Roughness Styles above

**Labeled arrow** -- same container binding approach:
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "a1", "originalText": "connects", "autoResize": true }
```

**Standalone text** (titles and annotations only -- no container):
```json
{ "type": "text", "id": "t1", "x": 150, "y": 138, "text": "Hello", "fontSize": 20,
  "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Hello", "autoResize": true }
```
- `x` is the LEFT edge. To center at position `cx`: `x = cx - (text.length * fontSize * 0.5) / 2`
- Do NOT rely on `textAlign` or `width` for positioning

**Arrow**:
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```
- `points`: `[dx, dy]` offsets from element `x`, `y`
- `endArrowhead`: `null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"`
- `strokeStyle`: `"solid"` (default) | `"dashed"` | `"dotted"`

### Arrow Bindings (connect arrows to shapes)

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "r1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "r2", "fixedPoint": [0, 0.5] }
}
```

`fixedPoint` coordinates: `top=[0.5,0]`, `bottom=[0.5,1]`, `left=[0,0.5]`, `right=[1,0.5]`

### Drawing Order (z-order)
- Array order = z-order (first = back, last = front)
- Emit progressively: background zones → shape → its bound text → its arrows → next shape
- BAD: all rectangles, then all texts, then all arrows
- GOOD: bg_zone → shape1 → text_for_shape1 → arrow1 → arrow_label_text → shape2 → text_for_shape2 → ...
- Always place the bound text element immediately after its container shape

### Sizing Guidelines

**Font sizes:**
- Minimum `fontSize`: **16** for body text, labels, descriptions
- Minimum `fontSize`: **20** for titles and headings
- Minimum `fontSize`: **14** for secondary annotations only (sparingly)
- NEVER use `fontSize` below 14

**Element sizes:**
- Minimum shape size: 120x60 for labeled rectangles/ellipses
- Leave 20-30px gaps between elements minimum
- Prefer fewer, larger elements over many tiny ones

### Color Palette

See `references/colors.md` for full color tables. Quick reference:

| Use | Fill Color | Hex |
|-----|-----------|-----|
| Primary / Input | Light Blue | `#a5d8ff` |
| Success / Output | Light Green | `#b2f2bb` |
| Warning / External | Light Orange | `#ffd8a8` |
| Processing / Special | Light Purple | `#d0bfff` |
| Error / Critical | Light Red | `#ffc9c9` |
| Notes / Decisions | Light Yellow | `#fff3bf` |
| Storage / Data | Light Teal | `#c3fae8` |

### Image Placeholders

For wireframes, image placeholders should be gray **hachure**-filled boxes with an ☒ icon — not solid-color fills. The hachure (lined) pattern clearly signals "this is an image placeholder" in a professional way.

```python
def IMG(id, x, y, w, h):
    """Image placeholder: hachure-filled gray box with ☒ in center"""
    els = [R(f'{id}_bg', x, y, w, h, '#E5E7EB', BORDER, 1, 2, 'hachure')]
    cx = x + w // 2 - 10
    cy = y + h // 2 - 14
    els.append(T(f'{id}_x', cx, cy, '☒', 28, '#9CA3AF', 'center', 'middle', w=24, h=32))
    return els
```

> **Pitfall:** Do NOT use `fill='solid'` on image placeholder backgrounds. Solid fills look like real content zones. Always use `fill='hachure'` (or `'cross-hatch'`) to visually distinguish placeholder areas from actual UI surfaces.

### Navbar Overlap

> **Pitfall:** Multi-word nav items (e.g., "Riwayat") are wider than expected and can overlap with "Masuk" or adjacent items. Use ≥80px per-item step and place the rightmost item with an explicit offset from the screen edge. See `references/multi-screen-wireframes.md` for the full pattern.

### Admin Screen Helpers

For admin panels, use `SB()` (sidebar), `STAT_CARD()` (dashboard metrics), and `TH_ROW()` / `TD_ROW()` (tables). See `scripts/build_wireframe.py` for ready-to-use implementations. Typical admin inventory: Dashboard, Customers (list + detail), Products (list + add/edit), Services (list + add/edit), Orders (list + detail with status flow), Feedback (list with rating summary).

#### Admin dashboard layout: side-by-side columns

Real Bootstrap admin dashboards use a **`col-lg-8` / `col-lg-4` split**: the recent orders table sits in the wider left column, and quick-action links/buttons sit in the narrower right column. They are **side-by-side**, not stacked full-width.

```python
left_w = int(CONTENT_W * 0.66) - 15   # ~631px
right_w = CONTENT_W - left_w - 30     # ~319px

# Left: Recent orders table card
E.append(R('tbl_card', cx, ny+160, left_w, 360, W, BD, 1, 6))
# Right: Quick actions card
qx = cx + left_w + 20
E.append(R('qa_card', qx, ny+160, right_w, 360, W, BD, 1, 6))
```

#### Admin stat cards: horizontal (icon left + value right)

Dashboard stat cards in real Bootstrap layouts use a **horizontal layout**: a colored icon circle on the left, with label above and value below on the right. They are **not** tall vertical cards — they are short and wide (~237×70px).

```python
SC_W = (CONTENT_W - 30) // 4   # ~237px per card with 10px gaps
for i, (lbl, val, ic_bg) in enumerate([
    ('Total Pelanggan', '150', P),
    ('Total Pesanan', '89', OK),
]):
    scx = cx + i * (SC_W + 10)
    E.append(R(f'sc{i}', scx, ny+70, SC_W, 70, W, BD, 1, 6))
    # icon circle
    E.append(R(f'sc{i}_ic', scx+12, ny+78, 48, 48, ic_bg, ic_bg, 0, 24, 'solid'))
    # label + value to the right of icon
    E.append(T(f'sc{i}_l', scx+72, ny+78, lbl, 12, TXL, w=SC_W-90))
    E.append(T(f'sc{i}_v', scx+72, ny+96, val, 22, TX))
```

> **Pitfall:** Do NOT use the vertical `STAT_CARD()` helper (label on top, value below, icon bottom-right) for Bootstrap-style admin dashboards. The real layout is horizontal.

#### File upload fields: use standard input rows, NOT image placeholders

In admin add/edit forms, the "Gambar Produk" (image upload) field is a **file input** (e.g., bootstrap-fileinput), NOT an image preview box. Using `IMG()` (hachure-filled gray box) for this field causes overlap with the fields below it because the image placeholder is too tall.

```python
# WRONG — IMG placeholder is too tall, overlaps next field
E += IMG('apf_img', cx+15, fy+18, 200, 120)   # 120px tall!
fy += 60  # way too small an increment for a 120px element

# CORRECT — render as a standard file input row, same height as other inputs
E.append(R(f'apf_in{i}', cx+15, fy+18, CONTENT_W-30, 38, W, BD, 1, 3))
E.append(T(f'apf_ph{i}', cx+25, fy+24, 'Pilih Gambar ▾', 13, TXL))
E.append(T(f'apf_hint{i}', cx+15, fy+60, '(jpg, png, max 5MB)', 11, TXL))
fy += field_h + 30  # proper spacing with field_h=70
```

> **Pitfall:** `IMG()` hachure placeholders are for displaying existing images (product gallery, hero, about section). File upload fields in forms should look like text inputs, not image previews.

#### Product table: image column comes first

The standard admin product table column order is `Gambar | Nama | Harga | Stok | Aksi` (image thumbnail first). The "Aksi" (actions) column is right-aligned (`text-end`) and typically 180px wide to fit Edit + Stock + Delete buttons.

```python
hw = [80, 360, 160, 100, 180]
TH_ROW(['Gambar','Nama','Harga','Stok','Aksi'], hw, cx, ny)
# Data row with small image thumb
E += IMG(f'pimg{r}', cx+10, ry+2, 40, 40)
E.append(T(f'pname{r}', cx+90, ry+8, f'Produk {r+1}', 12, TX))
```

#### Admin sidebar width and content area

Admin sidebars in real Bootstrap layouts are typically **260px** wide (not 220px or 200px). Use `SIDEBAR_W = 260` always. The content area width is then:

```python
SIDEBAR_W = 260
CONTENT_W = SCREEN_W - SIDEBAR_W - 40   # = 980 for SCREEN_W=1280
CONTENT_X_OFF = SIDEBAR_W + 20           # content left edge offset from frame
```

#### Admin table column widths must fill CONTENT_W

When building admin tables with `TH_ROW` / `TD_ROW`, the sum of column widths + 20 (padding) **must approximately equal `CONTENT_W`** (980px for SCREEN_W=1280). Tables that are only half the content width look broken.

**WRONG** — columns too narrow, table only spans ~720px of 980px content area:
```python
hw = [200, 100, 80, 80, 140]  # sum+20=620 ← WAY too narrow
```

**CORRECT** — allocate column widths to fill the available space:
```python
CONTENT_W = 980
# text-heavy (name, email): 200-300px
# medium (phone, status): 100-160px
# narrow (stock, ID): 50-100px
# action columns: 160-240px
hw = [260, 180, 280, 80, 180]  # sum+20=1000 ≈ CONTENT_W ✅
```

**Quick check** after defining column widths:
```python
assert abs(sum(widths) + 20 - CONTENT_W) <= 60, f"Table too narrow/wide: {sum(widths)+20} vs {CONTENT_W}"
```

#### Feedback summary card layout

For the admin feedback screen, the rating summary card uses a **side-by-side layout** matching Bootstrap's `d-flex align-items-center` pattern: big rating number on the left, stars + count on the right. The card is typically `col-md-6` (half the content width), with the filter dropdown and feedback table below.

```python
card_w = CONTENT_W // 2
E.append(R('af_sum', cx, ny+70, card_w, 110, W, BD, 1, 6))
# Left: big rating number
E.append(T('af_avg', cx+20, ny+80, '4.2', 48, WA))
E.append(T('af_of', cx+20, ny+128, 'dari 5.0', 14, TXL))
# Right: stars + count
E.append(T('af_stars', cx+120, ny+85, '★★★★☆', 24, WA))
E.append(T('af_count', cx+120, ny+120, 'Berdasarkan 24 ulasan', 13, TXL))
```

Usage in CARD (replace the solid-color image rectangle):
```python
# BEFORE (solid fill — looks like a real image):
out.append(R(f'{id}_img', x+1, y+1, w-2, ih-2, PRIMARY_LIGHT, PRIMARY_LIGHT, 0, 2))

# AFTER (gray box with X — standard wireframe placeholder):
out += IMG(f'{id}_img', x+1, y+1, w-2, ih-2)
```

Or for standalone image areas (hero banners, detail pages, about sections):
```python
E += IMG('hero_img', sx, ny, SCREEN_W, 300)
E += IMG('pd_img', sx + 40, ny, 500, 420)
```

### Grayscale Wireframe Mode

For medium-fidelity wireframes that avoid brand colors, use a neutral gray palette:

| Role | Color | Hex |
|------|-------|-----|
| Primary / CTA | Gray 500 | `#6B7280` |
| Primary light / accent | Gray 300 | `#D1D5DB` |
| Secondary | Gray 400 | `#9CA3AF` |
| Background | Gray 50 | `#F9FAFB` |
| Text | Gray 800 | `#1F2937` |
| Text light / secondary | Gray 500 | `#6B7280` |
| Borders / dividers | Gray 300 | `#D1D5DB` |
| White surfaces | White | `#FFFFFF` |
| Light backgrounds | Gray 100 | `#F3F4F6` |
| Image placeholder bg | Gray 200 | `#E5E7EB` |
| Image placeholder X | Gray 400 | `#9CA3AF` |
| Dark accents | Gray 700 | `#374151` |
| Darkest / hero bg | Gray 600 | `#4B5563` |

To convert a brand-colored script to grayscale, replace the design-system variables:
```python
# Brand-colored (for high-fidelity mockups)
P = '#E87A2F'; PL = '#FDEBD0'; S = '#2FA87A'
BG = '#FFF8F0'; TX = '#2D2D2D'; TXL = '#6C757D'; BD = '#E8E0D8'

# Grayscale (for medium-fidelity wireframes)
P = '#6B7280'; PL = '#D1D5DB'; S = '#9CA3AF'
BG = '#F9FAFB'; TX = '#1F2937'; TXL = '#6B7280'; BD = '#D1D5DB'
```

Also replace any hardcoded hex colors (e.g. `#E8E0D8`, `#FDEBD0`) with the corresponding gray token.

### Tips
- Use the color palette consistently across the diagram
- **Text contrast is CRITICAL** -- never use light gray on white backgrounds. Minimum text color on white: `#757575`
- Do NOT use emoji in text -- they don't render in Excalidraw's font
- Exception: `☒` works for image placeholder X markers (it's a Unicode symbol, not an emoji)
- For dark mode diagrams, see `references/dark-mode.md`
- For larger examples, see `references/examples.md`
- For multi-screen wireframe patterns, see `references/multi-screen-wireframes.md`
- For rendering frames to PNG images (without a browser), see `references/frame-to-png.md`
- For a ready-to-run wireframe builder script, see `scripts/build_wireframe.py`


