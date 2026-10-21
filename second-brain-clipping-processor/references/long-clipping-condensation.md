# Long Clipping Condensation

## Problem

Some clippings are extremely long - 500+ lines, sometimes 1700+ lines (e.g. a 10,000-word AI
engineer roadmap). Preserving the full raw text in a Notes row is wasteful and hard to navigate,
and it burns the markdown payload budget.

## Solution: Structured Summary

For clippings over ~300 lines, condense into a structured summary instead of preserving the full
raw text:

1. **Read the full content** to understand the structure (headings, sections, key points)
2. **Extract the core framework** - the outline, milestones, or step-by-step structure
3. **Preserve key quotes, code snippets, and resource links** - these are the high-value parts
4. **Summarize each section** in 2-5 sentences with the actionable takeaway
5. **Drop filler** - introductory fluff, repeated examples, lengthy motivational passages

## Example

**Input:** 1741-line Twitter thread "How to become an AI Engineer in 6 months" - 10,000+ words with
a detailed month-by-month curriculum.

**Output:** a Notes row "AI engineer roadmap" (~200 lines of markdown) with:
- Core thesis (2 paragraphs)
- What an AI engineer does (bullet list)
- Each month's goal + key resources (condensed from 50+ links to the essential ones)
- Key code snippets preserved
- Filler and repeated examples dropped

## Decision Rule

| Clipping length | Approach |
|----------------|----------|
| < 100 lines | Preserve full content, minor formatting cleanup |
| 100-300 lines | Preserve full content, trim redundant examples |
| 300-1000 lines | Condense to structured summary, preserve key quotes/code |
| 1000+ lines | Condense to structured outline, extract only the most valuable resources and code |

## Notion specifics

- One markdown payload must stay under 5000 blocks; a condensed row is comfortably under that.
- Pages over ~20,000 blocks come back **truncated** on read - a condensed row never hits that.
- Preserve the original URL in the `Source URL` property so the full text is still reachable.
- Put the raw excerpt in a `## Original` section only if it is short enough to be worth it.
