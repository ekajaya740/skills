# Clipping to Project Notes Pattern

Clippings don't always belong as standalone references. When content directly informs or
strategizes around an existing project or area, the filed row is related to that project/area
instead of standing alone.

## When to Use Project/Area Notes vs. Standalone References

| Signal | Destination |
|--------|-------------|
| Tutorial, how-to, cheatsheet, tech reference | standalone Notes row (Type=Reference) |
| Philosophical/strategic material that shapes direction | Notes row (Type=Note) related to the Area/Project |
| Cultural context relevant to personal brand | Notes row related to the Area/Project |
| Quote/essay that influences how you approach work | Notes row related to the Area/Project |
| No clear project/area match | standalone Notes row (Type=Reference) |

## Example

**Input:** Inbox clipping "Haven't had a single worry all day - retardmaxxing" (YouTube).
Speaker: Elisha Long. Content: philosophical take on rejecting overthinking, the attention
economy, the "escape the circus" metaphor.

**Classification decision:** Relates to Work-Of-Ekajaya because:
- It's about content creation philosophy (create from intuition vs. algorithmic anxiety)
- The "building in public" / creator economy is itself a form of the circus he describes
- Useful strategic context for how to approach the personal brand

**Destination:** a Notes row titled "retardmaxxing" with `Type` = Note, `Tags` = status/note, and
an `Area` relation pointing at the Work-Of-Ekajaya area row.

**Key additions in the curated body:**
- Core thesis summary
- Key ideas extracted
- Memorable lines blockquote
- "## My Take" section connecting the philosophy to the project

## Title convention

- Standalone references: a short descriptive title (the Notion title is the page name, not a slug)
- Project/area notes: a descriptive title, can be shorter since it lives in the context of the
  parent row - the relation carries the context, so the title does not need to repeat it
