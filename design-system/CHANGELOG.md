# Changelog

All notable changes to the `design-system` skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The version in this file matches the `version` field in `SKILL.md`.

## [1.0.0] - 2026-09-25

First stable release. The skill documents the Work of Ekajaya design system:
its tokens, typographic roles, section anatomy, component patterns, motion
rules and anti-patterns, for an Astro 6 + React 19 + Tailwind v4 dark
portfolio.

### Added

- `SKILL.md` — design context, tokens, typography, layout and review guidance.
- `reference/tokens.md` — colour, spacing, radius and type-scale tokens, with
  the `@theme` block in `src/styles/global.css` as the source of truth.
- `reference/components.md` — copy-paste component vocabulary taken from, or
  consistent with, the live site.
- `reference/motion.md` — motion rules: one or two orchestrated gestures rather
  than many small ones.
- `reference/og-images.md` — build-time social cards generated with Takumi
  (via `astro-takumi`), including the home eyebrow marker.
- `og-images`: recorded the eyebrow marker as a solid `#dd0303` block behind the
  whole role label (4.71:1 off-white on brand red), and why the lifted
  `#ff5a5a` accent fails contrast at 2.81:1.
- `og-images`: reference `logo-mark.png` and drop unrendered tag chips.

### Changed

- Renamed the skill from `workofekajaya-design-system` to `design-system`.

[1.0.0]: https://github.com/ekajaya740/skills/releases/tag/design-system-v1.0.0
