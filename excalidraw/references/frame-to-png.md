# Rendering Excalidraw Frames to PNG Images

When no browser/Chromium is available for screenshot-based rendering, you can parse the `.excalidraw` JSON directly and render each frame as a PNG using Pillow (PIL).

## Prerequisites

```bash
# If system pip is blocked by read-only filesystem, use a venv:
python3 -m venv --without-pip /tmp/venv
curl -sS https://bootstrap.pypa.io/get-pip.py | /tmp/venv/bin/python3
/tmp/venv/bin/pip install Pillow
```

## Approach

1. Load the `.excalidraw` JSON
2. Find frame rectangles by their `id` pattern (e.g., `f{col}{row}`) and look up their label text elements
3. For each frame, collect all elements whose `x`/`y` falls within the frame bounds
4. Render rectangles (filled backgrounds, hachure patterns, outlines) and text elements
5. Save each frame as a separate PNG

## Key implementation details

- **Hachure fill**: Draw diagonal lines across the rectangle area, composited through a rounded-rect mask
- **Rounded rectangles**: Use `ImageDraw.rounded_rectangle()` with `radius=6`
- **Text positioning**: Subtract the frame's `x`/`y` to get local coordinates; handle multi-line text with `\n` splits
- **Font**: Use DejaVuSans or LiberationSans from `/usr/share/fonts/`; fall back to `ImageFont.load_default()`
- **Drawing order**: Sort rectangles first (backgrounds), then texts (foreground)

## Limitations

- Arrows, diamonds, ellipses, and lines are not rendered (add as needed)
- Text alignment (`textAlign: center/right`) requires manual bbox calculation
- Container-bound text auto-centering is not recalculated
- Complex Excalidraw features (groups, bindings, linear elements) are not supported

## Output

Each frame produces one PNG at the frame's native size (e.g., 1280×900). Save to a directory like `myshop-wireframes-frames/`.