---
name: design-system
description: The design system for workofekajaya.com (Work of Ekajaya) — an Astro 6 + React 19 + Tailwind v4 dark portfolio. Use when building, editing, reviewing, or extending any UI on this site: new sections, components, pages, OG images, or visual polish. Provides the exact tokens, typography roles, section anatomy, component patterns, motion rules, and anti-patterns that keep new work indistinguishable from the existing site.
version: 1.0.0
---

# Work of Ekajaya — Design System

A dark-first, high-contrast portfolio system. Near-black canvas, a single scarce red accent,
three typographic roles, and a heat-shader monogram as the signature asset.

**Stack contract:** Astro 6 (SSG) · React 19 islands · Tailwind CSS v4 via `@tailwindcss/vite`
(no `tailwind.config.js` — tokens live in `@theme`) · Bun runtime · `astro-icon` + `@iconify-json/lucide`.

---

## 1. Design Context

Read this before making aesthetic decisions. It is the "why" behind every token below.

### Users

| Audience | Context | What they need |
|---|---|---|
| **Recruiters / hiring managers** (primary) | Mobile, several tabs open, skimming a shortlist | Identity, role, seniority, location in ~2 seconds |
| **Prospective freelance clients** | Email or Slack thread | Capability and trust, a hint of what he builds |
| **Peer developers** | X, Reddit, shared links | Craft, memorability, evident skill |

### Brand personality

**Bold, kinetic, technical.**

- *Bold* — full-bleed, high-contrast, commits to scale rather than hedging.
- *Kinetic* — heat, drift, a beam that tracks scroll. Energy is identity, not garnish.
- *Technical* — monospace labels, hairline rules, precise alignment, a palette taken from a
  shader's color stops.

Voice: first-person, plain, unembellished. Short declarative sentences. No marketing inflation.

### Design principles

1. **Identity in two seconds.** Name, role, location resolve before decoration is parsed.
2. **Accent is a scarcity economy.** Red works *because* it is rare. ~10% of visual weight.
3. **Type does the work.** Hierarchy from scale contrast and weight — not boxes, borders, shadows.
4. **On-system or absent.** New artifacts must look like a crop of the existing site.
5. **Motion implies life, never noise.** One or two orchestrated gestures; always reduced-motion safe.

### Anti-references

- **Generic SaaS gradient cards** — purple-to-blue wash, floating laptop mockup, soft shadow,
  centered logo. The single most important thing to avoid.
- **Busy portfolio collages** — screenshot grids, skill-badge soup, competing type sizes.
- **Dark-neon developer cliché** — terminal chrome, blinking cursor, green-on-black, code rain.
  Dark does not mean cyberpunk.

---

## 2. Tokens

All tokens are declared in the `@theme` block of `src/styles/global.css`. Tailwind v4 generates
utilities from them automatically (`--color-accent` → `bg-accent`, `text-accent`, `border-accent`).

### Color

| Token | Value | Utility | Role |
|---|---|---|---|
| `--color-background` | `#141414` | `bg-background` | Page field |
| `--color-foreground` | `#f5f5f5` | `text-foreground` | Primary type |
| `--color-card` | `#1c1c1c` | `bg-card` | Raised surfaces |
| `--color-card-foreground` | `#f5f5f5` | — | Type on card |
| `--color-border` | `#2e2e2e` | `border-border` | All hairlines |
| `--color-input` | `#2e2e2e` | — | Field borders |
| `--color-primary` | `#f5f5f5` | — | Primary button fill |
| `--color-primary-foreground` | `#0a0a0a` | — | Type on primary |
| `--color-secondary` | `#1e1e1e` | `bg-secondary` | Hover fills, chips |
| `--color-secondary-foreground` | `#f5f5f5` | — | Type on secondary |
| `--color-muted` | `#2a2a2a` | — | Muted fills |
| `--color-muted-foreground` | `#a0a0a0` | `text-muted-foreground` | Body copy, metadata |
| `--color-accent` | `#dd0303` | `text-accent` | **Identity accent (red)** |
| `--color-accent-foreground` | `#f5f5f5` | — | Type on accent |
| `--color-destructive` | `#dd0303` | — | Errors (shares accent) |
| `--color-ring` | `#3a3a3a` | — | Focus rings |
| `--color-accent-yellow` | `#fbff1a` | `text-accent-yellow` | Heat core |
| `--color-accent-blue` | `#1472ff` | `text-accent-blue` | Heat edge |
| `--color-accent-warm` | `#dd0303` | — | Alias of accent |

**Heat triad** — `#dd0303` → `#fbff1a` → `#1472ff` are the three stops of the `WoeHeatmap`
shader. Yellow and blue appear **only** where heat is literally being depicted (shader, tracing
beam, code highlights). Never as general-purpose accents.

**Rules**
- Never pure black (`#000`) or pure white (`#fff`). The field is `#141414`; type is `#f5f5f5`.
- Never gray text on a colored background — use a shade of the background instead.
- Never gradient text. Solid fills only.

### Radius

| Token | Value | Utility |
|---|---|---|
| `--radius-sm` | `4px` | `rounded-sm` |
| `--radius-md` | `8px` | `rounded-md` |
| `--radius-lg` | `12px` | `rounded-lg` |
| `--radius-xl` | `16px` | `rounded-xl` |

Pills and chips use `rounded-full`. Cards use `rounded-xl`. Buttons use `rounded-md`.

### Spacing

Tailwind's 4pt scale. The system's recurring rhythm:

- Section vertical: `py-24 md:py-32`
- Container: `max-w-3xl mx-auto px-6`
- Section header to content: `mb-12` / `mb-16`
- Card interior: `p-6 md:p-8`
- Chip gaps: `gap-2` / `gap-3`

### Breakpoints

`sm: 640` · `md: 768` · `lg: 1024` · `xl: 1280`. Section padding steps at `md`. Hero shader
responds to aspect ratio (not breakpoints) via `useContainerSize` + `getPreset`.

---

## 3. Typography

Three families, three non-overlapping jobs. Never blur the roles.

| Token | Family | Job | Utility |
|---|---|---|---|
| `--font-display` | **Goldman** | Headings, the name | `font-[family-name:var(--font-display)]` |
| `--font-sans` | **Sansation** | Body copy (default on `body`) | inherited |
| `--font-mono` | **Share Tech Mono** | Eyebrows, metadata, timestamps, buttons | `font-mono` |

Fonts load via Fontsource CSS imports at the top of `global.css`:
`@fontsource/sansation/{300,400,700}.css`, `@fontsource/goldman/{400,700}.css`,
`@fontsource/share-tech-mono/400.css`.

### Scale in use

| Role | Classes |
|---|---|
| Hero name | inline `fontSize` 1.875rem (mobile) → 3.75rem, `lineHeight: 1.05`, `letterSpacing: -0.025em` |
| Section heading | `text-3xl md:text-5xl font-bold text-balance` |
| Sub-heading / card title | `text-lg font-bold` |
| Body | `text-sm` / base, `leading-relaxed`, `text-pretty` |
| Eyebrow / label | `text-xs tracking-[0.3em] text-accent` |
| Micro-chip | `text-[10px] font-mono` |

**Rules**
- At least a 1.25 ratio between heading steps. Fewer sizes with more contrast beats many near-identical sizes.
- Add `0.05–0.1` to line-height for light-on-dark body text — light type reads as lighter weight.
- Cap body measure at 65–75ch (`max-w-3xl` at this scale).
- All-caps only for short labels and eyebrows — never long passages.
- Always pair `text-balance` on headings and `text-pretty` on body paragraphs.

---

## 4. Section anatomy

Every portfolio section follows the same skeleton. Deviating breaks the site's rhythm.

```astro
---
// Optional: import { Icon } from 'astro-icon/components';
---

<section id="SECTION_ID" class="relative z-20 bg-background border-t border-border">
  <div class="max-w-3xl mx-auto px-6 py-24 md:py-32">
    <header class="mb-12 md:mb-16">
      <p class="font-mono text-xs tracking-[0.3em] text-accent mb-3">EYEBROW</p>
      <h2 class="font-[family-name:var(--font-display)] text-3xl md:text-5xl font-bold text-foreground text-balance">
        Sentence-case heading.
      </h2>
    </header>

    <!-- content -->
  </div>
</section>
```

**Invariants**
- `id` **must** match a nav dot's `data-section` in `BaseLayout.astro`. Valid ids:
  `hero`, `about`, `experience`, `projects`, `skills`, `contact`.
- `relative z-20` keeps content above the hero shader; `bg-background` paints over it.
- `border-t border-border` is the section separator. Do not substitute shadows or gaps.
- The eyebrow is uppercase; the heading is sentence case with a period.

---

## 5. Component patterns

See `reference/components.md` for full copy-paste snippets. Summary of the vocabulary:

| Pattern | Signature |
|---|---|
| **Eyebrow** | `font-mono text-xs tracking-[0.3em] text-accent mb-3`, uppercase |
| **Tech chip** | `text-xs font-mono px-3 py-1 border border-border rounded-full text-muted-foreground` + `hover:border-accent hover:text-accent` |
| **Micro chip** | `text-[10px] font-mono px-2 py-1 border border-border rounded-full text-muted-foreground` |
| **Card** | `p-6 md:p-8 border border-border rounded-xl hover:border-accent transition-colors` |
| **Primary CTA** | `px-6 py-3 bg-foreground text-background rounded-md font-mono text-sm font-medium active:scale-[0.96] transition-transform` |
| **Secondary CTA** | `px-6 py-3 border border-border rounded-md font-mono text-sm font-medium hover:bg-secondary hover:border-foreground active:scale-[0.96] transition-colors` |
| **Entry row** | `flex flex-col md:flex-row md:items-baseline md:justify-between gap-1 mb-3` with `<h3>` + `<time class="font-mono text-xs text-muted-foreground">` |
| **Bullet list item** | `flex items-start gap-2` with a `w-1 h-1 rounded-full bg-muted-foreground mt-1.5` dot |
| **Section dot nav** | Fixed right-center, `IntersectionObserver`-driven, label on hover |

**Interaction rules**
- Interactive surfaces get `transition-colors` (or `transition-transform` for scale feedback).
- Buttons use `active:scale-[0.96]` — a small, fast press response.
- Hover on clickable titles moves color to `text-accent`; hover on outlined elements moves
  `border-border` → `border-accent`.
- Never make every button primary. Mix primary, secondary, and text links for hierarchy.

---

## 6. Signature devices

These are what make the site recognizable. Reuse them; do not invent parallel motifs.

### Heat shader (hero)

`WoeHeatmap.tsx` wraps `@paper-design/shaders-react`'s `<Heatmap>`, driving `logo.webp`
through a red/yellow/blue heat field. Rendered as the only React island in the hero
(`client:only="react"`).

- Aspect-driven presets via `getPreset(aspect)` (5 buckets, `<0.75` → `>=2.2`).
- Media-query overrides for mobile portrait, tablet portrait, and short screens.
- Defaults: `colors ['#dd0303','#fbff1a','#1472ff']`, `colorBack '#1c1c1c'`, `speed 0.96`,
  `contour 0.23`, `noise 0.27`, `fit 'contain'`.

### Tracing beam (experience)

`TracingBeam.tsx` draws a scroll-linked SVG beam through the experience list: a dim path plus a
gradient-lit path whose `y1`/`y2` are spring-smoothed from `scrollYProgress`. Gradient runs
`#dd0303` → `#fbff1a` → `#1472ff`.

### Scroll progress bar

A 2px `bg-accent` bar at the top of `BaseLayout`, `scaleX`-driven by scroll position.

### Eyebrow label

The most repeated structural motif. `font-mono text-xs tracking-[0.3em] text-accent`, uppercase,
above every section heading.

---

## 7. Motion

See `reference/motion.md`.

- **Easing:** exponential deceleration (`ease-out-quart/quint/expo`). No bounce, no elastic.
- **Animate:** `transform` and `opacity` only. Never `width`, `height`, `padding`, `margin`.
- **For height changes:** transition `grid-template-rows`, not `height`.
- **Reduced motion:** the global `@media (prefers-reduced-motion: reduce)` block in
  `BaseLayout.astro` collapses animation and transition durations. Scroll-driven decorative
  paths additionally carry `motion-reduce:hidden`.
- **One orchestrated gesture** beats scattered micro-interactions.
- Measure element geometry with `ResizeObserver` (`useContainerSize`), and re-measure when the
  element can change size after mount — a one-shot `useEffect` measurement will drift.

---

## 8. Accessibility

Non-negotiable, already established in `BaseLayout.astro`:

- Skip link (`.skip-link`) as the first focusable element, targeting `#main-content`.
- `<main id="main-content" tabindex="-1">`.
- Section nav has `aria-label="Section navigation"`; each dot has an `aria-label`.
- Decorative SVG carries `aria-hidden="true"`.
- `:focus-visible` rings via `--color-ring`.
- Respect `prefers-reduced-motion`.
- Maintain AA contrast: `#a0a0a0` on `#141414` is the floor for body text; prefer `#f5f5f5`
  for anything small.

---

## 9. Anti-patterns

**Never** in this system:

- Side-stripe accents — `border-left`/`border-right` wider than 1px as a colored stripe on
  cards, list items, or callouts.
- Gradient text (`background-clip: text` + a gradient).
- Generic SaaS gradient cards, floating laptop mockups, soft drop shadows.
- Glassmorphism / blur used decoratively rather than functionally.
- Nested cards. One container level only.
- Identical card grids repeated endlessly.
- Centered everything — the system is left-aligned with asymmetric space.
- Pure `#000` / `#fff`, or gray text on colored backgrounds.
- Skill-badge soup, screenshot collages, competing type sizes.
- Terminal chrome, blinking cursors, code rain.
- Same spacing everywhere — vary rhythm between tight groups and generous separations.
- Modals when an inline or progressive-disclosure pattern would do.

---

## 10. Project conventions

- **Tokens live in `@theme`** in `src/styles/global.css`. Never add a `tailwind.config.js`.
- **`global.css` must be imported in every layout** or Tailwind emits nothing.
- **New lucide icons** must be added to the `include.lucide` allowlist in `astro.config.mjs` —
  `astro-icon` inlines only allowlisted icons at build time.
- **Path alias:** `@/*` → `./src/*`.
- **React islands:** prefer `.astro` components. Only reach for React when you need state,
  effects, or a browser-only library (shaders, motion). Use `client:only="react"` when the
  component cannot SSR.
- **Class merging:** `cn()` from `@/lib/utils`, re-exported from the `cn` package
  (drop-in replacement for `clsx` + `tailwind-merge`).
- **Commit messages:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `style:`,
  `refactor:`, `ci:`, `build:`, `perf:`).
- **Runtime:** Bun only. `bun dev` · `bun run build` · `bun run preview`.

---

## 11. Reference files

| File | Contents |
|---|---|
| `reference/tokens.md` | Full token table, `@theme` block, global CSS layers |
| `reference/components.md` | Copy-paste snippets for every pattern above |
| `reference/og-images.md` | Takumi OG image setup, home + blog variants, fonts, meta wiring |
| `reference/motion.md` | Easing, durations, scroll-driven patterns, reduced-motion handling |
