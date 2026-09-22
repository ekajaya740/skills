# Motion — Work of Ekajaya

The site should feel kinetic without feeling busy. One or two orchestrated gestures beat a
scatter of micro-interactions.

## Easing and duration

| Use | Easing | Duration |
|---|---|---|
| Entrances / reveals | `ease-out-quart` / `ease-out-quint` / `ease-out-expo` | 300-600ms |
| Hover / color feedback | `ease-out` | 150-300ms |
| Press feedback | `ease-out` | ~100ms |
| Scroll-linked | spring (`stiffness` 400-500, `damping` 80-90) | continuous |

**Never** use bounce or elastic easing. Real objects decelerate smoothly.

## Animate only `transform` and `opacity`

Animating `width`, `height`, `padding`, or `margin` triggers layout on every frame. For height
changes, transition `grid-template-rows` (`0fr` -> `1fr`) instead.

Existing examples:
- Scroll progress bar: `transform: scaleX(progress)`.
- Nav dot active state: `transform: scale(1.5)` plus a color swap.
- Press feedback: `active:scale-[0.96]`.

## Scroll-linked patterns

### Tracing beam

`TracingBeam.tsx` is the reference implementation:

```tsx
const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });

const y1 = useSpring(useTransform(scrollYProgress, [0, 0.8], [50, svgHeight]), {
  stiffness: 500, damping: 90,
});
const y2 = useSpring(useTransform(scrollYProgress, [0, 1], [50, svgHeight - 200]), {
  stiffness: 500, damping: 90,
});
```

The gradient's `y1`/`y2` are bound to the spring values, so the lit segment tracks the reader.
The dim background path stays static.

### Scroll progress bar

In `BaseLayout.astro`, a passive scroll listener writes `scaleX` to a fixed 2px `bg-accent` bar:

```js
window.addEventListener('scroll', () => {
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  progressBar.style.transform = 'scaleX(' + (docHeight > 0 ? window.scrollY / docHeight : 0) + ')';
}, { passive: true });
```

## Measuring geometry

Use `ResizeObserver` through the `useContainerSize` hook rather than reading `offsetHeight` once:

```ts
const ref = useCallback((node: HTMLDivElement | null) => {
  if (!node) return;
  const observer = new ResizeObserver(([entry]) => {
    const w = Math.round(entry.contentRect.width);
    const h = Math.round(entry.contentRect.height);
    setSize({ width: w, height: h, aspect: h > 0 ? w / h : 1 });
  });
  observer.observe(node);
  return () => observer.disconnect();
}, []);
```

A one-shot `useEffect` measurement drifts whenever the element changes size after mount — for
example after a webfont loads or when content reflows. Any scroll-linked drawing that depends on
content height must re-measure on resize, not only on mount.

## Reduced motion

Two layers of protection, both required:

1. **Global kill switch** in `BaseLayout.astro`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

2. **Per-element opt-out** for purely decorative scroll art: the lit beam path carries
`motion-reduce:hidden`, so the animated stroke disappears entirely while the static dim path
remains as a structural line.

`scroll-behavior: smooth` is set globally in `@layer base`. Keep smooth scrolling opt-in to the
stylesheet so the reduced-motion block can neutralise it.

## React hook conventions

- Prefer `useSyncExternalStore` for browser-state subscriptions (`useMediaQuery`). It avoids
  hydration mismatch by returning a stable server snapshot (`false`) and re-syncing on the client.
- When the project's `no-use-effect` skill is active, reach for `useSyncExternalStore`,
  callback refs, or event handlers before `useEffect`.
- `client:only="react"` skips SSR entirely — appropriate for shader and scroll components that
  cannot render server-side.
