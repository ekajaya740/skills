# Hard rules — the pre-flight gate

Tier 1. These are not preferences. Checklist form so it can be run mechanically.

---

## A. Before creating / dispatching a task

- [ ] **Board** = the project's board (`finance-app` | `storykami` | `infra` | `notion-migration`).
      Not `default` (archived), not a per-profile board.
- [ ] **Assignee** is present and in the right lane. Blank assignee = unroutable = defect.
- [ ] **Body is self-contained.** No "as discussed", "the file we talked about", "continue from before".
      A worker with zero conversation context can act on it.
- [ ] **Acceptance criteria** exist and are objectively checkable ("works" is not one).
- [ ] **Evidence requirement** is stated (command + output / path / URL / test).
- [ ] **Workspace** is real for repo work (`worktree` or `dir:<path>`), not `scratch`.
- [ ] **`idempotency_key`** set if a retry could duplicate the work.
- [ ] **Destructive work is split**: dry-run task → review task → apply task, gated with `--parent`.
- [ ] **No secrets** in title, body, comment, or metadata.

## B. Before completing a task

- [ ] **Evidence exists**, and the mutated target was **read back** to confirm the change — not assumed.
- [ ] **External side effects have a verifiable handle** (URL, id, absolute path). A worker's
      self-report is not proof; verify it yourself.
- [ ] **Deliverable files** attached (`hermes kanban attach` / `artifacts`) with absolute paths.
- [ ] **`summary`** is a 1–3 sentence human handoff, not "done".
- [ ] **Not merely implemented.** If it needs review, call `kanban_request_review` — do not complete.

## C. Blocking

- [ ] Right **kind**: `dependency` (waiting on a task — auto-resumes, **no human needed**),
      `needs_input` (a person must decide), `capability` (no access / impossible — do not retry),
      `transient` (flaky, may clear).
- [ ] **Reason** is one or two concrete sentences. Not "stuck".
- [ ] **Not a nudge.** A task unblocked and re-blocked for the same reason auto-escalates to triage.
      If you are re-blocking the same task for the same cause, stop and fix the cause instead.
- [ ] Use `kanban_request_review` for review, **never** `block --kind needs_input`.

## D. Never

- Never commit, paste, echo, or log a secret (task body, comment, metadata, title).
- Never delete a board or a task — **archive only**.
- Never mark a destructive task done without its evidence, or with only partial evidence.
- Never unblock-and-retry the same wall (see the escalation limit).
- Never hand-promote a parent-gated task to `ready`.
- Never put credentials, tokens or personal data in a task title.
- Never leave a `running` task silently wedged past the stale timeout — reclaim it.

---

## Verification honesty (the one that bites)

A worker reporting "uploaded successfully" / "file written" / "pushed" may be wrong.
For any external side effect, require a handle and **check the handle yourself** before telling the
user it succeeded. This applies to the orchestrator too: do not relay a worker's success claim as fact.
