# Migrating boards safely

How to move tasks between boards without destroying history. Learned the hard way on 2026-10-05.

## The trap: child-table `id` is per-board, not global

`task_events`, `task_comments`, `task_runs` and `task_attachments` use
`INTEGER PRIMARY KEY AUTOINCREMENT id`, unique **only within one board's DB**. Two source boards both
number from 1. If you copy rows while preserving `id`, the second board's rows collide with the
first's and — with `insert or ignore` — are **silently dropped**. No error, no warning, just missing
history.

On 2026-10-05 this dropped **116 events, 4 runs and 2 attachments**, and the damage was not cosmetic:
a dropped `blocked` event destroyed a task's sticky block, so it auto-promoted and re-dispatched.

**Worse: the corrupted task did not re-block.** It spawned a live worker and started acting on
stale instructions with no human in the loop.

## The rules

1. **Never copy `id` for child tables.** Insert them without `id` and let the target allocate.
   Keep chronological order: sort the source rows by `created_at` (or source `id`) before inserting.
2. **`tasks.id` is safe to preserve** (it is a text `t_xxxxxxxx`), and preserving it is what keeps
   cross-board references — cron watchdogs, comments, docs — working.
3. **`task_runs.id` is remapped, so `task_events.run_id` must be rewritten.** Build
   `{(task_id, old_run_id): new_run_id}` while inserting runs, then map `run_id` on every event or
   the run↔event linkage breaks.
4. **Verify with counts, from the source.** After migrating, assert
   `target_count == sum(source_counts)` per child table. Do not trust "moved=N".
5. **Check sticky blocks survived.** For every migrated task that was blocked, assert a `blocked`
   (or `gave_up`) event exists on the target. Missing ⇒ it will auto-promote.
6. **A migrated `blocked` task is a live hazard** until its block is re-established. Type-block it
   (`--kind needs_input`) as soon as it lands, and confirm it does not spawn.
7. **Use `insert or ignore` nowhere in a migration.** Prefer plain `insert` so a collision is a loud
   failure, not silent data loss.

## After any migration / archive

```bash
python3 scripts/kanban_hygiene.py     # catches stale runs, fragile/untyped blocks, dupes, WIP
hermes kanban --board <b> stats
hermes kanban --board <b> diagnostics
```

`kanban_hygiene.py` flags a `blocked` task that is untyped with `consecutive_failures >= failure_limit`
— exactly the shape that re-arms when the failure limit is raised. If you migrate or park tasks, run
it before walking away.

## Config changes that are actually dangerous

- **`kanban.default_assignee`** — the dispatcher *persists* it onto unassigned `ready` rows
  (`_apply_default_assignee`). Setting it while unassigned rows exist **arms every one of them**.
  Keep it `''` unless the board has no unassigned rows.
- **`kanban.failure_limit`** — raising it un-parks every task the previous limit had auto-blocked.
  Those tasks have `block_kind IS NULL` and are held by that gate *only*; typing them first
  (`--kind needs_input`) makes them immune.
- **`kanban.dispatch_stale_timeout_seconds`** — a `running` task with no progress past this is
  reclaimed and re-queued. Too low kills legitimately long jobs; give long harvests their own
  `--max-runtime` instead.
