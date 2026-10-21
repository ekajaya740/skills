# Payment Tracking in Project Tasks

For client-billed projects (especially under Joki or any freelance/consulting work), track payment
status inside the project - as **Task rows** in the Tasks data source, related to the project.

## When to use

- any project where the client pays in milestones or installments
- Joki client projects (Petshop, Laboratory, etc.)
- fixed-price contracts with partial payments

## Pattern

Payment milestones are Task rows:

```bash
nb POST /v1/pages '{
  "parent": {"type":"data_source_id","data_source_id":"'"$TASKS_DS"'"},
  "properties": {
    "Name": {"title":[{"text":{"content":"50% paid - down payment"}}]},
    "Status": {"select":{"name":"Done"}},
    "Project": {"relation":[{"id":"'"$PROJECT_ID"'"}]},
    "Tags": {"multi_select":[{"name":"payment"}]}
  }
}'
```

Use `Status` = `Done` for a received milestone and `Todo` for a pending one, and put the
percentage and the trigger in the task name.

## Rules

1. **Use the Status property** - `Done` for received, `Todo` for pending
2. **Label clearly** - include the percentage or amount and what triggers it (down payment,
   milestone, final delivery)
3. **Keep it visible** - payment tasks are a quick-glance signal; give them a `payment` tag so
   they can be filtered
4. **Not synced to Google Tasks** - payment tracking is second-brain only (financial info does not
   belong in a task manager)
5. **Update on trigger** - when the user says "X is paid" or "half paid", update the task row
   immediately

## Variants

**No payment received yet:** one Task row `Status` = Todo, name "Not paid yet".

**Partial payment:** two rows - "50% paid (down payment received)" Done, "50% paid (on final
delivery)" Todo.

**Multiple milestones:** one row per milestone ("30% paid (contract signed)", "30% paid (midpoint
delivery)", "40% paid (on final acceptance)").

## Why separate from ordinary tasks?

Payment status is **not a task** - it is a project state signal. Mixing it into the ordinary task
list makes it look like an action item. A dedicated `payment` tag gives instant visibility into
the financial health of the project without cluttering the task list.
