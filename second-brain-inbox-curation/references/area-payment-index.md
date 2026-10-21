# Area-Level Payment Note

For business Areas (like Joki) with several client projects, keep a **Payment note** at the Area
level to give a cross-project payment overview.

## When to use

- the Area is a service/freelance business with multiple client projects
- each project has its own payment tracking
- you need a quick glance at all payment statuses across the business

## Where it lives

A Notes row named `<Area> - Payment`, with the `Area` relation set to the business area and
`Type` = Note.

## Body format

A single markdown table (GFM pipe table, blank line before and after):

```markdown
| Project | Status | Date | Proof Location |
|---------|--------|------|----------------|
| Laboratory Management System | ✅ Fully paid | 2026-06-27 | [proof 1](https://drive.google.com/...), [proof 2](...) |
| Petshop Information System | ⏳ 50% paid | 2026-06-27 | [payment-50pct](https://drive.google.com/...) |
```

## Rules

1. **One row per project** - each client project gets one line
2. **Status column** - emoji for quick scanning: ✅ fully paid, ⏳ partial, ❌ unpaid
3. **Date column** - last payment date
4. **Proof Location** - a Drive link (Notion file URLs are pre-signed and expire, so binaries live
   in Google Drive, never in the page body)
5. **Update on every payment event** - update the project row *and* this index
6. **Link from the Area row** - add a mention of the payment note in the area's body

## Project-level vs Area-level

| | Project level (Tasks rows) | Area level (Payment note) |
|---|---|---|
| **Scope** | Single project | All projects in the business |
| **Detail** | One task row per milestone | One line per project |
| **Purpose** | Track individual milestones | Business health overview |
| **Proof images** | Linked from the task row or the project body | Referenced by link only |

## Workflow on a payment event

1. Upload the proof image to Google Drive
2. Update the project's payment task rows (Status = Done, and a mention of the proof)
3. Update the Area's Payment note table
4. Mention the Payment note in the Area row's body
