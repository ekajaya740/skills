# The craft bar, per area

The reasoning behind each row of skill `design` § The craft bar. Read the row you are
failing; not the whole file.

## Tokens

A token layer is the difference between a design system and a pile of screens that agree today.

**The bar:** every colour, radius, font size, spacing value, and shadow comes from a named token.
No raw values in component code.

**Why:** a raw value is a decision made once, in one place, invisible to the next person. The
second raw `#1a1a1a` is a drift nobody notices until the dark mode pass.

**Fails when:**

- `style={{ color: '#111' }}` in a component that has a `text-primary` token
- `13px`, `17px`, `23px` — sizes off any scale
- A token named after its value (`gray-700`) rather than its role (`text-muted`)

**Fix order:** find the nearest token → if none fits, name the role and add it → only then use a
raw value, with the reason in the design doc.

## Type

**The bar:** three roles — display, body, mono — each with a deliberate scale. A fourth role needs
a reason.

**Why:** the eye reads hierarchy from contrast in size and weight. Five sizes between 14 and 18 read
as "no decision", and every additional size makes the next one easier to add.

**Fails when:**

- A heading sized by what fits the container rather than by its role
- Line height under 1.4 on body copy, or over 1.7
- Measure over ~75 characters on a wide screen
- Mono used for emphasis rather than for code

## Spacing

**The bar:** one scale, on a rhythm. Gaps between similar things are equal.

**Why:** inconsistent spacing reads as sloppiness before it reads as anything else, and it is the
cheapest thing to get right.

**Fails when:**

- 4/6/8/10/12 all used for "a small gap" in the same view
- Padding that changes between two instances of the same card
- A gap that exists only because a margin collapse made it look right once

## Hierarchy

**The bar:** exactly one thing is loudest per screen. The eye has a path: primary → supporting →
secondary.

**Why:** two loud things mean zero loud things. Emphasis is a scarce resource — spend it once.

**Fails when:**

- Every section is a card with a border and a shadow
- Every button is the accent colour
- A page title the same weight as its section titles
- Emphasis added by bolding a whole paragraph

## States

The detailed table is in skill `design` § States are the work. The reasoning:

**Why:** a screen that is only designed in its happy state is a screen that was never designed for
the network. Users meet loading and error far more often than the designer does.

**Fails when:**

- `Loading…` as text, where a skeleton would keep the layout still
- An empty table with only a header row
- An error that says "Something went wrong" and nothing else
- A success toast that disappears before it can be read, with no state change behind it

## Density

**The bar:** rows and cards sized for their content, and consistent across one list.

**Why:** mixed row heights in a list destroy scanning, which is the only thing a list is for.

**Fails when:**

- One row is 48px and the next is 72px because of a two-line title with no clamp
- Table cells with different vertical alignment
- A card grid where one card is taller because of a longer description

## Motion

**The bar:** motion explains a change in state. 120–250ms for UI transitions. Respects
`prefers-reduced-motion`.

**Why:** motion is a cue, not decoration. A fade that takes 600ms does not feel luxurious; it feels
slow, and it delays every subsequent action.

**Fails when:**

- Every element fades in on mount, so nothing reads as new
- A hover animation on elements that are not interactive
- Layout-shifting animation on a list that is still loading
- Transform-based motion without a reduced-motion fallback

## Interaction

**The bar:** every clickable thing has hover, `focus-visible`, active, and disabled states.
Touch targets at least 44×44px.

**Why:** the focus state is the only way a keyboard user knows where they are. Removing it is the
single most common accessibility regression, and it is invisible to a mouse user.

**Fails when:**

- `outline: none` with no replacement
- A disabled button with no visual difference and no explanation
- Hover-only affordances on a touch screen
- A checkbox whose label is not part of the hit area

## Copy

**The bar:** concrete, verb-first, sentence case. The user's words, not the system's.

**Why:** "Submit" tells the user nothing about what happens next. "Create invoice" does, and it
makes the button testable — if the label is wrong, the action probably is too.

**Fails when:**

- "Oops!", "Something went wrong", "An error occurred"
- "Submit", "OK", "Yes" on a destructive action
- Title Case On Every Button And Label
- An error that names the system's concept instead of the user's

## Responsive

**The bar:** real content checked at 360, 768, and 1280. No horizontal scroll. Touch targets hold
at the small end.

**Why:** a layout checked only at desktop is a layout with two unverified surfaces. The narrow one
is where the content actually breaks.

**Fails when:**

- A table that scrolls the whole page horizontally instead of its own container
- Text clamped to one line that truncates the only meaningful word
- A fixed-width sidebar that eats the screen at 360
- A modal taller than the viewport with no internal scroll

## Related

- The skill itself, and the design-doc rule → [`SKILL.md`](SKILL.md)
- Proving a UI change → skill `verify-change` § UI changes
