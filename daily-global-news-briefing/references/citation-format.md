# Citation Format for Daily Briefing

This is the canonical format for citations in the daily briefing skill.
Every story headline gets a bracketed citation index. All URLs are collected in a `## References` glossary at the bottom.

## Output Structure

```markdown
# Daily Global News Briefing — YYYY-MM-DD HH:MM UTC

## Geopolitics 🌍

**• [One-sentence headline]** [1]
1–2 sentences of key context / impact.

**• [One-sentence headline]** [2]
1–2 sentences of key context / impact.

## Business & Economy 💰

**• [One-sentence headline]** [3]
1–2 sentences of key context / impact.

## Tech & Science 🔬

**• [One-sentence headline]** [4]
1–2 sentences of key context / impact.

## Big Picture

2–3 sentences synthesizing how the top stories connect or what to watch next.

---

## References

[1] https://www.example.com/news/article-1
[2] https://www.example.com/news/article-2
[3] https://www.example.com/news/article-3
[4] https://www.example.com/news/article-4

*Sources: BBC, Reuters, CNBC | Compiled: YYYY-MM-DD HH:MM UTC*
```

## Rules

1. **Sequential numbering** — `[1]`, `[2]`, `[3]`... in order of first appearance across the whole document (not per-category).
2. **One URL per story** — each headline gets one `[N]` pointing to its canonical article URL.
3. **Deduplication** — if two headlines reference the same source article, reuse the same `[N]` for both.
4. **No bare URLs inline** — never paste a raw `https://...` inside a body paragraph. Always use the `[N]` shorthand.
5. **Glossary at bottom** — the `## References` section comes after `## Big Picture` and before the footer.
6. **Telegram safety** — since delivery is via Telegram, keep citations clean and predictable. Avoid nested brackets or markdown footnote syntax that Telegram doesn't render well.
