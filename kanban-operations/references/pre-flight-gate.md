# Worker pre-flight gate

Text to inject ahead of a kanban worker's instructions (the `kanban` lifecycle block) so the standard
is enforced at execution time, not just read as documentation.

Install per profile. Keep it short — it is a gate, not a second skill; the detail lives in the
`kanban-operations` skill which auto-loads.

---

## Gate text

```
KANBAN PRE-FLIGHT (run before you act, and again before you close)

Before starting:
1. Confirm you can state the GOAL in one sentence from the task body alone. If the body is missing
   context you need, do NOT guess — block with --kind needs_input and name exactly what is missing.
2. Confirm ACCEPTANCE CRITERIA are checkable. If there are none and the work is verifiable, that is
   a body defect: block with --kind needs_input.
3. Confirm your workspace is the right one for the work (repo work must not land in scratch).

Before completing:
4. Produce the evidence the task asked for. Read back every target you mutated and confirm the change.
5. For any external side effect (upload, send, remote write, publish, deploy), capture a verifiable
   handle — URL, id, or absolute path. Never claim success from your own intent.
6. Call kanban_complete with a 1-3 sentence `summary` and an `artifacts` list of absolute paths for
   every deliverable file. "done" is not a summary.
7. If the work is implemented but NOT verified, or touches anything destructive/shared, call
   kanban_request_review instead of completing.
8. If blocked: pick the right --kind (dependency = waits on a task and auto-resumes; needs_input = a
   human must decide; capability = impossible, don't retry; transient = flaky). Never re-block the
   same task for the same reason — if you are, stop and escalate the cause.
```

---

## Notes for the installer

- If the profile already has a kanban lifecycle block injected automatically, append the gate items
  in a clearly-labelled section rather than duplicating the lifecycle description.
- Do not let the gate contradict the skill. The skill is normative; if they drift, fix the gate.
- Keep the block-kind list in sync with `hermes kanban block --help`.
