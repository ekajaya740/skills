# OG Images — Work of Ekajaya

Social cards are generated at build time with **Takumi** (via `astro-takumi`). No headless
browser, no runtime cost. Images are written next to each page's HTML in `dist/`.

## How it works

`astro-takumi` runs in the `astro:build:done` hook:

1. Reads each emitted `index.html`.
2. Parses it with jsdom and extracts `og:title`, `og:description`, `og:url`, `og:type`, `og:image`.
3. Calls the `render()` function with that page data **plus the jsdom `document`**.
4. Rasterizes the returned React node via Takumi and writes `<page>.webp` beside the HTML.
5. **Fails the build** if the `og:image` path does not exactly match the generated file path.

Because step 5 is enforced, `og:image` must come from `getImagePath({ url, site })` — never a
hand-written path.

## Required meta tags

Missing any of these throws at build time:

| Tag | Source |
|---|---|
| `og:title` | `Head.astro` -> `title` |
| `og:url` | `Head.astro` -> `canonicalURL` |
| `og:type` | `Head.astro` -> `type` (`website` / `article`) |
| `og:image` | `getImagePath({ url: Astro.url, site: Astro.site })` |
| `og:description` | Optional; `Head.astro` -> `description` |

## Fonts

Takumi has **no system fonts**. Every family must be supplied as raw bytes. The three project
families are read from Fontsource at config time:

```js
import * as fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const fontFile = (pkg, file) =>
  fs.readFileSync(fileURLToPath(import.meta.resolve(`${pkg}/files/${file}`)));

const ogFonts = [
  fontFile('@fontsource/goldman', 'goldman-latin-700-normal.woff'),
  fontFile('@fontsource/goldman', 'goldman-latin-400-normal.woff'),
  fontFile('@fontsource/sansation', 'sansation-latin-400-normal.woff'),
  fontFile('@fontsource/share-tech-mono', 'share-tech-mono-latin-400-normal.woff'),
];
```

Family names resolve from the font's own metadata, so `fontFamily: 'Goldman'`,
`'Sansation'`, and `'Share Tech Mono'` all work in the render function.

## Two variants

Per-page variants, dispatched on `pathname`:

| Route | Variant | Composition |
|---|---|---|
| `/` | **Heat portrait** | Full-bleed `logo-mark.png` heat treatment as the field; identity block anchored bottom-left |
| `/blog/<id>/` | **Typographic** | Near-black field, eyebrow, post title in Goldman, description |
| `/404`, `/blog/` | Typographic (default) | Falls back to the typographic variant |

### Shared card grammar

Both variants use the same 1200x630 grammar so they read as one family:

- Field: `#141414`
- Eyebrow: `Share Tech Mono`, uppercase, `letterSpacing` ~`0.3em`, `#ff5a5a` (lifted from `#dd0303` for contrast)
- Eyebrow marker (home only): the whole label on a solid `#dd0303` block, off-white type (4.71:1)
- Display type: `Goldman`, tight leading, off-white `#f5f5f5`
- Metadata: `Share Tech Mono`, `#a0a0a0`
- Accent hairline: heat card 120x3 `#ff5a5a`; typographic divider 1px `#2e2e2e` (border, not accent)
- Red occupies well under 10% of the card.

### Eyebrow marker (home)

The home eyebrow (`Full-Stack Engineer`) carries the only highlight in the system: the entire
role sits on a solid `#dd0303` block, off-white type, so it reads at full accent strength over
the busy mark field. The blog/404 eyebrow stays plain — it is a short label, not a role.

The marker is a deliberate exception to "hierarchy comes from scale and weight, not boxes"
(`.impeccable.md` principle 3). It earns the exception because the eyebrow sits over the mark's
hottest band, where plain accent type cannot hold legibility. It is confined to this one label,
and the red stays inside the accent's ~10% weight budget.

Contrast: off-white `#f5f5f5` on `#dd0303` is 4.71:1 (AA). Note the block uses the true brand
red, not the lifted `#ff5a5a` — off-white on `#ff5a5a` is only 2.81:1 and fails.

Layout: the block's 14px left padding is cancelled by a `-14px` margin so the marked text starts
flush with the name below it (both at x=80, the identity column's padding). The background lives
on an inner span inside the eyebrow's flex row, so the block hugs the label (379px) instead of
stretching the full column width — no `alignSelf` needed.

### Heat portrait (home)

```tsx
// pseudo-structure
<div style={{ width:'100%', height:'100%', display:'flex', position:'relative', backgroundColor:'#141414' }}>
  <img src={logoDataUrl} style={{ position:'absolute', inset:0, width:'100%', height:'100%', objectFit:'cover', opacity:0.9 }} />
  <div style={{ position:'absolute', inset:0, background:'linear-gradient(to top, #141414 8%, rgba(20,20,20,0.55) 45%, rgba(20,20,20,0.15) 100%)' }} />
  <div style={{ position:'relative', display:'flex', flexDirection:'column', justifyContent:'flex-end', padding:'0 72px 64px' }}>
    {/* eyebrow, name, role, location, hairline */}
  </div>
</div>
```

### Typographic (blog)

```tsx
<div style={{ width:'100%', height:'100%', display:'flex', flexDirection:'column',
              justifyContent:'space-between', backgroundColor:'#141414', padding:'72px' }}>
  <div style={{ display:'flex', flexDirection:'column' }}>
    <div style={{ fontFamily:'Share Tech Mono', fontSize:22, letterSpacing:'0.3em', color:'#ff5a5a' }}>BLOG</div>
    <div style={{ fontFamily:'Goldman', fontSize: title.length > 60 ? 60 : 76, color:'#f5f5f5', lineHeight:1.08 }}>{title}</div>
  </div>
  <div style={{ display:'flex', flexDirection:'column' }}>
    <div style={{ fontFamily:'Sansation', fontSize:28, color:'#a0a0a0' }}>{description}</div>
    <div style={{ display:'flex', height:1, backgroundColor:'#2e2e2e' }} />
    <div style={{ fontFamily:'Share Tech Mono', fontSize:22, color:'#a0a0a0' }}>workofekajaya.com</div>
  </div>
</div>
```

**Title sizing:** step down for long titles (about `76` under 60 chars, `60` up to 90, `48`
beyond). Never let the title wrap past three lines — truncate instead.

## Images

Local assets (e.g. `public/logo-mark.png`) are passed as pre-supplied `images` sources in the
integration options and referenced by their `src`. Remote URLs are fetched and cached across
pages by the integration's shared `fetchCache`.

```js
images: [{ src: '/logo-mark.png', data: fs.readFileSync('public/logo-mark.png') }],
```

## Config

```js
astroTakumi({
  options: {
    fonts: ogFonts,
    format: 'webp',
    quality: 90,
    width: 1200,
    height: 630,
    images: [{ src: '/logo-mark.png', data: fs.readFileSync('public/logo-mark.png') }],
  },
  render: ogRenderer,
});
```

Output format `webp` is recommended for compression. If you change `format`, you must also
change the `format` passed to `getImagePath`, or the build will fail its path check.

## Rules

- Never hand-write an `og:image` path. Always derive it from `getImagePath`.
- Never use a gradient background wash (anti-reference: generic SaaS gradient card).
- Never render text in a gradient fill.
- Keep the red accent rare — a hairline plus at most one eyebrow (the home marker).
- Always run a production build to verify; a mismatch fails the build rather than shipping.
