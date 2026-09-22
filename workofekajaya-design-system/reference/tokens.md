# Tokens — Work of Ekajaya

Source of truth: the `@theme` block in `src/styles/global.css`. Tailwind v4 derives utilities
from these custom properties automatically. **Never** add a `tailwind.config.js`.

## Full `@theme` block

```css
@import "tailwindcss";
@import "@fontsource/sansation/300.css";
@import "@fontsource/sansation/400.css";
@import "@fontsource/sansation/700.css";
@import "@fontsource/goldman/400.css";
@import "@fontsource/goldman/700.css";
@import "@fontsource/share-tech-mono/400.css";

@layer base {
  html { scroll-behavior: smooth; }
}

@theme {
  --color-background: #141414;
  --color-foreground: #f5f5f5;
  --color-card: #1c1c1c;
  --color-card-foreground: #f5f5f5;
  --color-border: #2e2e2e;
  --color-input: #2e2e2e;
  --color-primary: #f5f5f5;
  --color-primary-foreground: #0a0a0a;
  --color-secondary: #1e1e1e;
  --color-secondary-foreground: #f5f5f5;
  --color-muted: #2a2a2a;
  --color-muted-foreground: #a0a0a0;
  --color-accent: #dd0303;
  --color-accent-foreground: #f5f5f5;
  --color-destructive: #dd0303;
  --color-ring: #3a3a3a;
  --color-accent-yellow: #fbff1a;
  --color-accent-blue: #1472ff;
  --color-accent-warm: #dd0303;

  --font-sans: "Sansation", ui-sans-serif, system-ui, sans-serif;
  --font-display: "Goldman", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "Share Tech Mono", ui-monospace, monospace;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
}
```

## Base layer

```css
@layer base {
  html {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    scrollbar-width: thin;
    scrollbar-color: #2e2e2e #141414;
  }

  body {
    background-color: #141414;
    color: #f5f5f5;
    font-family: var(--font-sans);
    line-height: 1.6;
  }

  ::selection {
    background-color: rgba(221, 3, 3, 0.3);
    color: #f5f5f5;
  }
}
```

## Utilities layer

```css
@layer utilities {
  .text-balance { text-wrap: balance; }
  .text-pretty  { text-wrap: pretty; }
}
```

`text-balance` goes on headings; `text-pretty` goes on body paragraphs. Both are used
consistently across every section.

## Color usage guide

| Need | Token | Why |
|---|---|---|
| Page field | `bg-background` | `#141414`, never `#000` |
| Body copy | `text-muted-foreground` | `#a0a0a0` — AA floor on this field |
| Emphasis type | `text-foreground` | `#f5f5f5` |
| Separator / outline | `border-border` | `#2e2e2e`, always 1px |
| Identity accent | `text-accent` / `border-accent` | Red — scarce, ~10% weight |
| Hover fill | `hover:bg-secondary` | `#1e1e1e` |
| Heat core | `text-accent-yellow` | Only in heat depictions |
| Heat edge | `text-accent-blue` | Only in heat depictions |
| Raised surface | `bg-card` | `#1c1c1c` |

## Reading tokens from inline styles

The React islands use inline styles rather than Tailwind classes. Read tokens through
`var()` with a literal fallback so they still resolve before CSS loads:

```tsx
style={{
  fontFamily: 'var(--font-display)',
  color: 'var(--color-foreground, #fafafa)',
  border: '1px solid var(--color-border, #27272a)',
}}
```

Note the fallbacks in the existing code (`#fafafa`, `#27272a`) differ slightly from the
canonical tokens (`#f5f5f5`, `#2e2e2e`). They only apply pre-hydration; prefer the canonical
values in new code.

## Focus rings

```css
:focus-visible {
  outline: 2px solid var(--color-ring);
  outline-offset: 2px;
}
```

Skip-link styling lives in a `<style is:global>` block in `BaseLayout.astro` and uses
`--color-accent` as its background.
