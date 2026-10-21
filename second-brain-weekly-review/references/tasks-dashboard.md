# Tasks Dashboard - Saved Views

The old `Tasks.md` with live `tasks` query blocks is gone. The dashboard is now a set of
**saved views** over the Tasks data source, created with `POST /v1/views`.

## Task state lives in properties

| Property | Values |
|---|---|
| `Status` | Todo, In progress, Blocked, Done |
| `Priority` | P0, P1, P2, P3 |
| `Due` | date |
| `Project` / `Area` | relation |
| `Context` | Computer, Home, Errands, Calls, Anywhere |
| `Source` | relation to the Notes/Daily Notes row it came from |

The `#type/task` prefix is gone; keep `type/task` as a **tag** on the task row if you want to
filter for it.

## The views

```bash
nb POST /v1/views '{
  "data_source_id": "'"$TASKS_DS"'",
  "name": "Due Today",
  "type": "table",
  "configuration": {"type":"table","group_by":{"type":"select","property":"Status"}},
  "filter": {"and":[
    {"property":"Status","select":{"does_not_equal":"Done"}},
    {"property":"Due","date":{"on_or_before":"2026-10-21"}}]},
  "sorts": [{"property":"Due","direction":"ascending"}]
}'
```

| View | Filter | Sort | Group |
|------|--------|------|-------|
| Due Today | Status != Done, Due <= today | Due asc | Status |
| Due Tomorrow | Status != Done, Due = tomorrow | Due asc | Status |
| Due This Week | Status != Done, Due in the next 7 days | Due asc | Status |
| By Project | Status != Done | Priority asc | Project |
| By Area | Status != Done | Priority asc | Area |
| All Open Tasks | Status != Done | Due asc | Status |

## The workspace default views

The second-brain workspace already ships with: Inbox (table, `Status` = Untriaged, sorted by
Captured desc), Projects (board, grouped by Status), Now (tasks due in the next 7 days), All Tasks
(grouped by Area), Orphans (Notes with empty `Related`), Stale (Notes with `Stale After` <
today). Create the task views above only if they are missing.

## Maintenance

- When a new Project or Area is created, add a "By Project"/"By Area" view or extend the existing
  one's `group_by`
- Views are live - they never need to be regenerated when a task changes
- `POST /v1/views` is not idempotent: check the existing view names first, or you will create
  duplicates
