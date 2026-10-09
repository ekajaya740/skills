# Task templates

Copy the relevant block into `--body-file`. Every template is self-contained: a worker with zero
conversation context must be able to act on it alone.

---

## Feature / change

```
GOAL
<one sentence — the end state that must be true>

CONTEXT
- Repo / path: <absolute path>
- Board / project: <board slug> / <project>
- Prior work: <task ids, commits, PRs>
- Why now: <the reason this exists>
- Already tried: <what did not work, so it is not retried>

ACCEPTANCE CRITERIA
- [ ] <objectively checkable>
- [ ] <objectively checkable>
- [ ] Tests pass: <exact command>

EVIDENCE REQUIRED
- Command run + observed output (paste the relevant lines)
- <file path / URL / screenshot proving the change>

CONSTRAINTS / OUT OF SCOPE
- Do not touch: <...>
- Must not: <...>

WORKSPACE
<scratch | worktree | dir:/abs/path>   # repo work needs a real path
```

---

## Bugfix

```
GOAL
<the bug is fixed: <symptom> no longer occurs under <condition>>

REPRODUCTION
1. <exact steps>
2. <exact steps>
Expected: <...>   Actual: <...>

CONTEXT
- Repo / path: <absolute path>
- Failing since: <commit / deploy / date, if known>
- Error text: <verbatim>

ACCEPTANCE CRITERIA
- [ ] Reproduction steps above now show Expected
- [ ] Regression test added at <path> and fails before the fix, passes after
- [ ] <exact test command> is green

EVIDENCE REQUIRED
- Before/after output of the reproduction
- The new test's name and its run output

CONSTRAINTS
- Fix the cause, not the symptom. Do not disable/skip the failing assertion.
```

---

## Ops / infra

```
GOAL
<service / config / machine is in state X>

CONTEXT
- Host: <...>   - Unit / service: <...>
- Current state: <what it does now>
- Blast radius if wrong: <what breaks and for whom>

ACCEPTANCE CRITERIA
- [ ] <health check command> returns <expected>
- [ ] Change survives a restart / reboot
- [ ] Rollback path documented in this task

EVIDENCE REQUIRED
- Health-check output
- Diff of the changed config
- Confirmation the service came back up

CONSTRAINTS
- Take a backup before mutating.
- Dry run first if the tool supports it.
- Do not restart <unrelated service>.
```

---

## Research / analysis

```
GOAL
<the question answered, to the depth of: <...>>

CONTEXT
- Why: <what decision this informs>
- Scope: <time range, sources, domains>
- Out of scope: <...>

DELIVERABLE
- <format: markdown report at <abs path> / comment on this task / ...>
- Length: <...>
- Must include: <...>

ACCEPTANCE CRITERIA
- [ ] Every claim has a source (URL or file path)
- [ ] Conflicting evidence is stated, not smoothed over
- [ ] Provides a clear recommendation or explicitly says none is possible

EVIDENCE REQUIRED
- The report path, plus the 3 strongest sources
- Anything you could NOT verify, listed explicitly
```

---

## Destructive / migration (Tier 1 — split it)

**Never one task that both dry-runs and applies.** Create three, gated with `--parent`:
dry-run → review → apply. The apply task must not exist in `ready` until the dry run is reviewed.

### Task 1 — dry run
```
GOAL
Produce an exact, reviewable plan of what <operation> will change. CHANGE NOTHING.

CONTEXT
- Target: <abs paths / DB / repo>
- Backup taken at: <abs path>   # must exist before this task runs

ACCEPTANCE CRITERIA
- [ ] Full list of affected items, with counts
- [ ] Nothing was mutated — prove it (e.g. row counts unchanged, git status clean)
- [ ] Rollback steps written out
- [ ] Risky/irreversible items called out individually

EVIDENCE REQUIRED
- The plan as a file at <abs path>
- The proof-of-no-mutation output
```

### Task 2 — review (human or reviewer profile)
```
GOAL
Review the dry-run plan from <task id> and approve or reject.

ACCEPTANCE CRITERIA
- [ ] Counts in the plan verified independently against the target
- [ ] Rollback plan is actually executable
- [ ] Explicit APPROVE or REJECT recorded as a comment
```

### Task 3 — apply (gated on task 2 via `--parent`)
```
GOAL
Execute the approved plan from <task id>. Nothing outside it.

CONSTRAINTS
- Follow the approved plan exactly; stop and comment if reality differs.
- Never delete — archive/rename only.
- If any step fails, STOP. Do not continue past a failed step.

EVIDENCE REQUIRED
- Command output for each step
- Post-state verification (counts, health checks) proving the intended end state
- Confirmation the rollback path was not needed (or the rollback output if it was)
```
