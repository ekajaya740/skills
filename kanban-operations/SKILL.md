---
name: kanban-operations
description: "Use for ALL Kanban work: creating, routing, assigning, blocking, unblocking, reviewing or completing a task; choosing a board; decomposing work into a graph; handling handoffs and evidence; and any question about how Hermes kanban operates. Triggers on: 'kanban', 'board', 'create a task', 'assign this', 'route to', 'delegate to a bot', 'task stuck', 'blocked task', 'request review', 'why did this task fail', 'hand this off'. NOT for: short same-profile reasoning with no durable record (use delegate_task); cron scheduling (use the cronjobs skill); the content of what a task produces (use the owning lane's skill)."
version: 1.0.0
author: ekajaya740
license: MIT
metadata:
  hermes:
    tags: [kanban, orchestration, delegation, routing, workflow, bookkeeping]
    related_skills: [notion-second-brain, hermes-profiles]
---

# Kanban Operations — the canonical standard

This is **the** operating standard for Hermes kanban on this machine. `AGENTS.md` and `SOUL.md`
carry only a pointer here; where they disagree with this file, **this file wins**.

Board topology, the routing table, and hard rules are normative. Everything else is convention —
follow it unless you have a reason, and when you deviate, say so in the task body.

## Companion skills (these stay; read them alongside)

| Skill | Role | Status |
|---|---|---|
| `kanban-orchestrator` | deeper decomposition playbook + anti-temptation rules for an orchestrator profile | compatible — this standard defers to it on decomposition depth |
| `kanban-worker` | worker pitfalls and edge cases (auto-loaded for every dispatched worker) | compatible |
| `hermes-kanban-board-admin` | board admin + debugging tasks landing on the wrong board | **partly superseded** — its "isolate one board per agent" model is replaced by per-project boards |
| `kanban-bulk-tracker` | kanban tick-off checklists at scale | **SUPERSEDED** — kanban checklists are retired (see `references/board-map.md`) |

Do not create a board per agent/profile. Do not load big lists as kanban checklists.

---

## 0. Scope and tiers

**Tier 1 — HARD (never skip).** Destructive work, handoffs, evidence, board/assignee correctness,
secrets. Violating one of these is a defect, not a style choice. See §5 and `references/hard-rules.md`.

**Tier 2 — CONVENTION.** Task anatomy, priority, WIP, naming, dedup. Follow by default; justify
deviations in the task body.

**Tier 3 — ADVISORY.** Preferred patterns (decomposition shape, comment rhythm, log length).

---

## 1. Task anatomy (Tier 2)

Every task is read by a worker that **knows nothing about your conversation**. The body is the
whole briefing. A body missing any of these is not dispatch-ready.

| Field | Required | Rule |
|---|---|---|
| **Title** | yes | `Lane: outcome` — imperative, one line, ≤ 80 chars. E.g. `finance-app: fix raw minor-unit display bug`. Never a question, never "help with". |
| **Goal** | yes | One sentence: the end state that must be true. |
| **Context** | yes | Everything the worker cannot discover: file paths, repo, board/project, prior task ids, why this exists, what was already tried. |
| **Acceptance criteria** | yes | Bulleted, each objectively checkable. "Works" is not a criterion. |
| **Evidence required** | yes | What the worker must produce to prove it: command + observed output, file path, URL, screenshot, test result. |
| **Constraints / out of scope** | yes when non-obvious | Explicit non-goals prevent scope creep. |
| **Workspace** | yes | `scratch` \| `worktree` \| `dir:<path>`. Repo work needs a real path — never let repo work land in an ephemeral scratch dir. |
| **Assignee** | yes | A real profile name. Never blank (see §3). |
| **Priority** | recommended | Higher = sooner. Reserve >0 for real urgency. |
| **idempotency_key** | when retryable | Set it on anything a retry could duplicate (see §6). |

**Templates:** `references/task-templates.md` (feature, bugfix, ops/infra, research, destructive/migration).
**Board map & archiving:** `references/board-map.md`. **Hard-rule checklist:** `references/hard-rules.md`.
**Moving tasks between boards:** `references/migrating-boards.md` (read this before any migration — child-table
`id`s are per-board and copying them silently destroys history).
**Worker gate text:** `references/pre-flight-gate.md`.

### Context-passing rule (Tier 1)
Never write "as discussed", "the file we talked about", or "continue from before". Restate it.
A worker that has to guess will guess wrong and cost you a dispatch cycle.

### Acceptance-criteria rule (Tier 1 for handoffs)
If a task will be reviewed or its result trusted, acceptance criteria and the evidence requirement
are **mandatory**. A task with neither cannot be verified, so it cannot be honestly completed.

---

## 2. Lifecycle (Tier 2, with Tier 1 gates)

```
triage → todo → ready → running → review → done
                   ↑         ↓
              blocked ←──────┘   (needs_input | dependency | capability | transient)
```

| Transition | Tool | Notes |
|---|---|---|
| flesh out a stub | `kanban_create --triage` then worker promotes | use when the spec is not ready |
| make ready | automatic when all parents are `done` | never hand-promote a gated task |
| start | dispatcher claims, or `kanban claim` | claims are atomic |
| park on a human | `kanban_block --kind needs_input` | goes to `blocked`, human-visible |
| park on another task | `kanban_block --kind dependency` | waits in `todo`, **auto-resumes** — no human needed |
| park on time | `kanban schedule` | waiting on a clock, not a human |
| hard wall | `kanban_block --kind capability` | no access / impossible action — do not retry |
| flaky | `kanban_block --kind transient` | may clear; retry expected |
| hand off | `kanban_request_review` | **not** a block. Never counts toward escalation. |
| reject a review | `kanban_request_changes` | returns to the implementer, no block accounting |
| finish | `kanban_complete` | with `summary` + `artifacts` (see §5) |

### Block-kind rule (Tier 1)
`dependency` is the **only** kind that auto-resumes without a human. Choosing the wrong kind is the
most common kanban defect: parking on `needs_input` when you are really waiting on a task stalls work
until a person notices. Ask: *does a task or a person unblock me?*

### Escalation limit (Tier 1)
A task that is unblocked and re-blocked for the **same reason** is auto-escalated to triage. Do not
unblock-and-retry the same wall. Fix the cause, change the approach, or leave it blocked with a clear
reason. Repeatedly nudging a blocked task is a defect, not persistence.

### Review gate (Tier 1)
Implementation ≠ verification. Request review for: destructive changes, anything touching external
side effects (uploads, sends, remote writes, publishes), schema/data migrations, and cross-bot
handoffs. Use `kanban_request_review`, never `kanban_block --kind needs_input`, for a review.

---

## 3. Routing (Tier 1 — get this right or work goes to the wrong bot)

### Boards are per-project and profile-agnostic
One board per **project**, not per bot. The `assignee` alone decides who does the work.

| Board | Project | Typical assignees |
|---|---|---|
| `finance-app` | finance-app app + ledger + portfolio | `coding`, `financial-advisor` |
| `storykami` | StoryKami / video + transcript pipeline | `coding`, `default` |
| `infra` | VPS, 9router/Cartethyia, dotfiles, gateway, harvest tooling | `coding` |
| `notion-migration` | Second-brain → Notion migration | `coding` |

Full map with history and legacy notes: `references/board-map.md`.

**Do not create a board per profile.** Do not reintroduce `HERMES_KANBAN_BOARD` pins in a profile
`.env` — pins freeze a bot to one board and break cross-project routing. Routing lives in this table.

### Assignee table
| Profile | Lane |
|---|---|
| `default` | orchestration, bookkeeping, records, general/life, second-brain filing |
| `coding` | all repo/code/infra/file edits — the only profile that edits code |
| `financial-advisor` | finance-app ledger writes, TradingAgents runs, budgeting, IDX |
| `health-coach` | Hevy, training, sleep/stress, health data |

**Hard rules:** never leave `assignee` blank (a blank task is unroutable and will sit idle). Never
assign `default` domain work that belongs to a specialist. Never edit code on `default` — route it.

### `kanban_create` vs `delegate_task`
| Use | When |
|---|---|
| **`kanban_create`** | work that needs a specialist's own memory, must survive a restart, needs to be tracked/reviewed, or is cross-profile. **Default choice.** |
| **`delegate_task`** | short, same-profile reasoning that needs no durable record and no specialist identity. |

### Decomposition (Tier 2/advisory)
- One task = one outcome. If the acceptance criteria need "and" twice, split it.
- Use `--parent` to gate: a child stays in `todo` until every parent is `done`.
- Fan-out/fan-in: parallel workers → one verifier → one synthesizer (`kanban swarm`), or hand-link
  with `kanban_link`.
- Give each child its own acceptance criteria — a parent's criteria do not flow down.
- Cap blast radius: split migrations into dry-run → review → apply, never one task that does both.

---

## 4. Hygiene (Tier 2)

- **WIP limit:** keep a profile's `running` tasks ≤ 3 unless the work is genuinely parallel.
- **Dedup:** before creating, `kanban list` the target board. Use `--idempotency-key` for anything a
  retry or a re-run could duplicate.
- **Priority:** leave 0 as default; reserve 1+ for real urgency. Everything urgent = nothing urgent.
- **Naming:** board slugs lowercase-hyphen; task titles `Lane: outcome`.
- **Comments:** one comment per state change that a future reader needs (decision, blocker, result).
  Not a running diary — the events table already records transitions.
- **Retention:** close, then `kanban archive`. Never delete a board or task — archive only.
- **Stale sweep:** `running` tasks past `dispatch_stale_timeout_seconds` are wedged, not busy. Reclaim
  with `kanban reclaim` and re-dispatch, or block with a real reason.
- **`kanban.default_assignee` must stay EMPTY (`''`) while any board holds unassigned `ready` rows.**
  The dispatcher *persists* the default onto unassigned ready rows (`_apply_default_assignee`), so
  setting it backfills `assignee=NULL` rows and **arms them for dispatch**. On 2026-10-05 the two
  checklist boards held 1,150 unassigned `ready` rows — setting `default_assignee: default` would
  have dispatched all of them to the orchestrator. Leave it `''` and require an explicit assignee,
  or the safety net becomes a footgun.

---

## 5. Hard rules (Tier 1 — the pre-flight gate)

Run this before creating a task and before completing one.

**Before dispatch:**
1. Correct **board** for the project, and correct **assignee** (non-blank, right lane).
2. Body is self-contained — a worker with zero conversation context can act on it.
3. Acceptance criteria are objectively checkable; evidence requirement is stated.
4. Workspace is real for repo work (`worktree`/`dir:`), not `scratch`.
5. `idempotency_key` set if a retry could duplicate.
6. Destructive work is split: dry-run task → review → apply task.

**Before completing:**
1. Evidence produced and **verified by reading back the mutated target**, not assumed.
2. External side effects have a **verifiable handle** (URL, id, absolute path) — a self-report is not
   proof. Verify it yourself before claiming it.
3. `artifacts` lists absolute paths for deliverable files.
4. `summary` is a 1–3 sentence human handoff, not "done".
5. Nothing is marked done that is actually only implemented — request review instead.

**Never:** commit secrets; paste secrets into a task body/comment; delete a board or task; put
credentials in a title; mark a destructive task done without its evidence.

Full checklist: `references/hard-rules.md`.

---

## 6. Quick reference

```bash
# discover
hermes kanban boards ls
hermes kanban --board finance-app list
hermes kanban --board finance-app show t_abc123

# create (project board + explicit assignee)
hermes kanban --board finance-app create "finance-app: fix FX rounding" \
  --assignee coding --body-file /tmp/body.md --workspace worktree \
  --idempotency-key finance-app-fx-rounding-v1 --priority 1

# graph  (positional: parent child)
hermes kanban --board finance-app link t_parent t_child
hermes kanban --board finance-app swarm --help

# state
hermes kanban --board finance-app block t_abc --kind needs_input "reason text"
hermes kanban --board finance-app block t_abc t_def --kind dependency "reason"   # bulk
hermes kanban --board finance-app unblock t_abc --reason "..."
hermes kanban --board finance-app reclaim t_abc --reason "..."
hermes kanban --board finance-app request-review t_abc --summary "..."
hermes kanban --board finance-app complete t_abc --summary "handoff" \
  --result "one-line" --metadata '{"changed_files":["/abs/path"]}'

# diagnose
hermes kanban --board finance-app diagnostics
hermes kanban --board finance-app stats
hermes kanban --board finance-app gc --event-retention-days 30
```

`--board` is always required when working outside the active board. Omitting it silently targets
`default` — which is archived legacy and must not receive new work.

**Deliverable files:** the CLI `complete` has no artifact flag. Attach files with
`hermes kanban attach <task_id> <path>` (or the `artifacts` argument of the `kanban_complete` tool)
so they land as durable task attachments.
