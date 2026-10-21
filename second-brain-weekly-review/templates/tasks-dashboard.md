# Tasks Dashboard - Saved Views (template)

The tasks dashboard is a set of **saved views** over the Tasks data source, not a markdown file.
Use this template to describe the dashboard for the human, and to recreate the views with
`POST /v1/views` if they are missing.

## Views to create

| View | Type | Filter | Sort | Group |
|------|------|--------|------|-------|
| Due Today | table | Status != Done, Due <= today | Due asc | Status |
| Due Tomorrow | table | Status != Done, Due = tomorrow | Due asc | Status |
| Due This Week | table | Status != Done, Due in the next 7 days | Due asc | Status |
| By Project | table | Status != Done | Priority asc | Project |
| By Area | table | Status != Done | Priority asc | Area |
| All Open Tasks | table | Status != Done | Due asc | Status |

## Request template

```bash
nb POST /v1/views '{
  "data_source_id": "'"$TASKS_DS"'",
  "name": "<view name>",
  "type": "table",
  "configuration": {"type":"table","group_by":{"type":"select","property":"Status"}},
  "filter": {"and":[
    {"property":"Status","select":{"does_not_equal":"Done"}},
    {"property":"Due","date":{"on_or_before":"2026-10-21"}}]},
  "sorts": [{"property":"Due","direction":"ascending"}]
}'
```

## Rules

- Task state lives in the `Status` property (Todo / In progress / Blocked / Done), never in a
  `#type/task` prefix
- `POST /v1/views` is not idempotent - list the existing views before creating
- A view is live; it never needs regenerating when a task changes
