---
name: design
description: The craft bar for UI work — tokens, layout, motion, states, and the design doc that must match the code. Use when building, editing, or reviewing any interface, or when deciding whether a UI change is finished.
disable-model-invocation: true
version: 0.0.1
---

# Design

What "finished" means for an interface, and the documents that keep it true. The bar is not taste
— every item below is checkable.

This is the generic craft bar. A project with its own design system overrides the tokens; it does
not override the states, the craft checks, or the design-doc rule.

## The five questions before any UI code

Answer these in the reply, one line each. If any answer is "whatever looks fine", that is the
decision to make first.

1. **Who is looking, and at what size?** Phone at arm's length, laptop at a desk, a TV across a
   room. It changes the type scale, not just the breakpoints.
2. **What is the one thing on this screen?** If there are two, one is the page and one is a card.
3. **What is the page's job in one verb?** Browse, compare, confirm, edit, monitor. The verb picks
   the layout.
4. **What is the empty, loading, error, and done state?** Four states per surface, not one.
5. **What existing component or token does this reuse?** Copy the nearest existing surface. A new
   shape must earn itself.

## The craft bar

Each row is verifiable by looking. Full explanations and the anti-pattern behind each:
[`CRAFT-BAR.md`](CRAFT-BAR.md).

| Area | The bar | Fails when |
| --- | --- | --- |
| **Tokens** | Every colour, radius, font size, and spacing value comes from the token layer | A hex code, a `13px`, a magic `17px` padding |
| **Type** | Three roles at most: display, body, mono. A deliberate scale | Five sizes between 14 and 18 |
| **Spacing** | One scale, applied on a rhythm | 4/6/8/10/12 all used for the same kind of gap |
| **Hierarchy** | Exactly one thing is loudest; the eye has a path | Everything bold, everything a card, everything accented |
| **States** | Empty, loading, error, success — designed, not defaulted | Bare "Loading…" text; an empty table with no explanation |
| **Density** | Rows and cards sized for their content, consistently | Mixed row heights in one list |
| **Motion** | Motion explains a change in state; 120–250ms; respects reduced-motion | Decorative animation, or a 600ms fade on every element |
| **Interaction** | Every clickable thing has hover, focus-visible, active, disabled | Focus ring removed with no replacement |
| **Copy** | Concrete, verb-first, sentence case, no filler | "Submit", "Oops!", "Something went wrong" |
| **Responsive** | Real content at 360/768/1280; no horizontal scroll; 44px touch targets | A desktop layout squeezed |

## States are the work

Most unfinished UI is missing states, not missing polish. For every surface that fetches or
mutates:

| State | Must show |
| --- | --- |
| **Empty** | Why it is empty and the one action that fills it |
| **Loading** | A skeleton matching the final layout, or a spinner in place — never bare text |
| **Error** | What failed, in the user's words, and a retry |
| **Partial** | What loaded and what did not, in that order |
| **Success** | The new state, not a toast that vanishes before it is read |
| **Disabled** | Why it is disabled, visible without hovering |

A loading state that changes the layout when it resolves is a bug, not a rough edge.

## The design doc rule

**A component is not done until its `DESIGN.md` matches.** The doc is not a write-up after the
fact; it is the contract the next change checks against.

Per component or surface, `DESIGN.md` holds:

```md
---
tokens: [surface-1, text-primary, accent, radius-md]
states: [empty, loading, error, success]
---

## Purpose
One sentence: what this is for and where it appears.

## Anatomy
The parts, and which are optional.

## Contract
Props, variants, and what each variant is for.

## Tokens consumed
The exact names, from the token layer.

## Not for
The adjacent case this should not be used for.
```

Plus one row in the component index (map) so the doc is findable. A component whose tokens changed
without its doc changing is a review finding, not a nit.

When the project has no design system yet: create `docs/design-system.md` with the tokens, and put
the first `DESIGN.md` beside the first real component. Do not write thirty design docs for zero
components.

## Reviewing UI

Two axes, reported side by side:

- **Craft** — the table above, checked by looking at a rendered screen.
- **Contract** — the design doc and tokens match the code; states exist; the change did not
  invent a new pattern where one existed.

A review that never rendered the UI is a code review, and should say so.

## Anti-patterns at a glance

- Accent colour used for more than one purpose on a screen.
- A card inside a card inside a card.
- Icons without labels where the icon is not universal.
- A toast as the only confirmation of a destructive action.
- Text contrast below 4.5:1 for body copy.
- A modal for something that could be inline.
- Three different border radii in one view.
- Motion on hover for every element, so nothing reads as interactive.

## Related

- The full reasoning per area → [`CRAFT-BAR.md`](CRAFT-BAR.md)
- Design docs in a monorepo → skill `project-scaffold` → `targets/monorepo.md`
- Proving a UI change → skill `verify-change` § UI changes
