# Notion Conventions Check

There is no vault any more, so there is no vault `AGENTS.md` to read. The conventions for the
migrated second brain live in three places:

1. **The contract skill** - `notion-second-brain/SKILL.md`: the nine data sources, the exact
   property names, the valid select options, the markdown dialect, the escaping rules, the mention
   syntax, the rate limit and the token location. This is the authority.
2. **The scaffold doc** - `notion-scaffold-and-beautify.md` in the migration workspace: how each
   data source was created, which property each frontmatter key landed in, and the default views.
3. **This skill's property templates** (section 2e) - the shape used when writing rows.

## What to check before writing a row

| Convention | Rule | Where it lives |
|---|---|---|
| Allowed tags | `status/*` and `type/*` only, plus the flexible categories. No topic tags, no project-name tags | contract skill, section 7 |
| Status values | Notion Status selects are Title Case and narrower than the vault vocabulary: `Active`, `Archived`, `Stale` (Notes); `Todo`, `In progress`, `Blocked`, `Done` (Tasks) | contract skill, sections 2 and 7 |
| Statuses with no select option | seed, note, seedling, evergreen, investigation, resolved, processed -> keep as `status/<value>` tags, Status stays `Active` | contract skill, section 7 |
| Type values | Note, Reference, Overview, Readme, Guide, Ticker | contract skill, section 2 |
| Linking | relation properties, one side only; inline `<mention-page url="https://www.notion.so/<PAGE_ID>">Title</mention-page>` for human-readable links | contract skill, section 6 |
| Never invent | an unknown select value silently creates a new option - check the list first | contract skill, section 10 |
| Nothing dropped | frontmatter keys with no property (aliases, domain, author, published, period, sessions, location, description, keywords, doi) go into a `## Metadata` section in the page body | contract skill, section 7 |

## Quick check before every write

1. Am I using a property that exists on that data source?
2. Is every select value one of the documented options?
3. Are my tags only `status/*` / `type/*`?
4. Did every leftover frontmatter key land in a `## Metadata` section?
5. Am I setting relations on one side only?

## Common patterns in the vault's conventions

| Convention | Example |
|---|---|
| Status-only tags | `status/seed`, `status/active`, `status/evergreen` |
| Category tags | `type/reference`, `type/project`, `type/area` |
| No topic tags | topics go into relations and content, not tags |
| No project-name tags | use the `Project` relation instead |
