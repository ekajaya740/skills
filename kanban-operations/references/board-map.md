# Board map

**One board per project. `assignee` decides who does the work — never the board.**

## Live boards

| Board | Project | Typical assignees | Notes |
|---|---|---|---|
| `finance-app` | finance-app app + ledger + portfolio | `coding`, `financial-advisor` | merged from the old `finance-app-coding` + `finance-app-finance` lane split (2026-10-05) |
| `storykami` | StoryKami / video + transcript pipeline | `coding`, `default` | |
| `infra` | VPS, 9router / Cartethyia, dotfiles, gateway, harvest tooling | `coding` | |
| `notion-migration` | Second brain → Notion migration | `coding` | |
| `default` | — | — | **RETIRED IN PLACE — do not create work here.** Cannot be archived (see below). |

### `default` cannot be archived — so it is retired in place
`hermes kanban boards rm default` is refused, and `list_boards()` **always** includes `default`
first, unconditionally (`kanban_db.py`). So `default` is permanently in the dispatcher's sweep and
is therefore **not** a safe home for parked work. It was retired in place on 2026-10-05:

- open work was remapped out to the project boards;
- the two remaining `blocked` rows were given a **typed, sticky block** (`--kind needs_input`), so
  no `failure_limit` change can silently re-arm them;
- it holds **0 `ready`/`todo`/`running` rows**.

**Never create a task on `default`.** If you find dispatchable rows there, either remap them to a
project board or type-block them with a real reason.

## Archived boards (read-only, data preserved)

| Board | Was | Why archived |
|---|---|---|
| `finance-app-coding` | coding lane board | folded into `finance-app` |
| `finance-app-finance` | finance lane board | folded into `finance-app` |
| `bennix` | Bennix YouTube video checklist | checklist, not work — see below |
| `tr-videos` | Timothy Ronald video checklist | checklist, not work — see below |
| `_archived/joki-myshop-*` | old project | completed |

### Checklist boards are not work boards
`bennix` and `tr-videos` held manual tick-off checklists (950 + 235 rows, `assignee = NULL`), not
dispatched work. They were archived with data intact and their `board.json` counts corrected
(bennix declared 927 but held 950; tr-videos declared 233 but held 235).

**Rule:** a checklist does not belong on a kanban board. A board where every row has no assignee and
no dispatch outcome is a spreadsheet wearing a kanban costume — it inflates task counts, confuses
`ready` queues, and no dispatcher should ever watch it. Keep checklists in Notion or a CSV.

## Profile → board pins are forbidden

`HERMES_KANBAN_BOARD` in a profile `.env` freezes that bot to one board and breaks routing to any
other project. Removed 2026-10-05 from `coding` (`finance-app-coding`) and `financial-advisor`
(`finance-app-finance`). Routing is the skill's table, not an env var.

If you find a new pin: remove it and note why, do not "work around" it.
