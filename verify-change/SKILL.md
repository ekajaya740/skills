---
name: verify-change
description: Decide what counts as proof a change works, and say it correctly. Use before claiming done, fixed, or working, when choosing between a test and a manual check, or when a change touches UI, data, or a deploy. Covers code repos and non-coding ones (docs, notes, writing) where the check is a link or schema lint instead of a build.
disable-model-invocation: true
version: 0.1.0
---

# Verify Change

Before any claim that something works, name **the layer it was verified at**. "Should work" is
not a layer. Neither is "the types pass" when the change is a database migration.

The rule that makes this matter: **a throwaway probe is not evidence.** A script you deleted
proved the behaviour once and left nothing to catch the next change.

## The ladder

Walk down until a rung is available. Use the **lowest rung that actually exercises the change** —
not the highest one you can reach cheaply.

| # | Rung | Evidence | Catches |
| --- | --- | --- | --- |
| 1 | **Automated test** | A test that fails before the change and passes after | Regressions, forever |
| 2 | **Command output** | `build`, `typecheck`, `lint`, `deploy --dry-run`, exit 0 | Broken contracts, unresolved bindings |
| 3 | **Real run** | Start it, hit it, paste the response or the log line | Wiring, config, runtime |
| 4 | **Read the diff** | The changed lines, quoted | Nothing at runtime |
| 5 | **Reasoning** | "This should work because…" | Nothing |

Rungs 4 and 5 are not evidence for a behaviour claim. They are what you say when no rung above is
reachable — and then the claim is `unverified`, in those words.

## Choosing the rung

| The change is… | Minimum rung | Why |
| --- | --- | --- |
| Pure logic with a seam | 1 | The test is cheap and outlives the session |
| A framework boundary (route, handler, component) | 1 or 3 | Prefer a test at the seam; a run is acceptable |
| Config, env, bindings | 2 then 3 | `--dry-run` proves it parses; only a run proves it works |
| Schema or migration | 3 | The migration must run against a real database, then be read back |
| Visual or interactive UI | 3, in a browser | Never claim a UI change from a diff |
| Docs, comments, `.md` | 4 | The diff is the artifact |
| A dependency bump | 1 + 2 | The old suite plus a clean build; then read the changelog for breaking notes |

**When a test is cheap, write it.** A criterion that is cheap to pin gets a test, not a ticket.
"When tests are off" (the `tests` section) means *do not build a suite the user did not ask for* —
not *do not verify*.

## When there is nothing to run

A vault, a research corpus, a writing project, a slide deck — no build, no test suite. The ladder
still applies, but rungs 1 and 2 mean something else: **a check that reads the artifact**, not a
compiler that produces one.

| The change is… | Rung | Evidence |
| --- | --- | --- |
| A note added or moved | 2 | The link check or schema lint exits 0 — `lychee --offline .`, a frontmatter validator |
| A link or cross-reference edited | 2 | The checker reports that target resolves; paste the line |
| Prose edited, no structure touched | 4 | The diff, quoted. This is honest here, not a cop-out |
| A doc that renders (site, PDF, slides) | 3 | The rendered artifact, opened — the page or slide, not the source |
| A note whose frontmatter drives tooling | 2 | The tool that reads it runs clean on the changed file |
| A claim about how something *works* | 3 | Someone followed it and it held. A doc that lies is a runtime bug |

**The trap in a non-coding repo:** rung 4 feels like enough because there is nothing to run. It is
not enough when the change affects a reader's *action* — a wrong path, a stale command, a
frontmatter key the query depends on. Those are behaviour, and behaviour needs rung 2 or 3.

When no check exists at all, say exactly that:

```
Untested: the vault has no link checker. Read the diff only — rung 4.
```

That sentence is complete. It names the missing tool, which is the next thing to add.

## The sentence

Every completion claim takes one shape:

```
<what now works> — verified at <rung>: <the command and its first meaningful line>
```

Examples:

```
Magic-link login works — verified at rung 3: `curl -X POST localhost:3000/auth/magic` → 200 {"sent":true}
```

```
Token refresh fixed — verified at rung 1: `bun test auth.spec.ts` → 1 pass, 0 fail (was 1 fail before)
```

```
Build no longer fails — verified at rung 2: `bun run build` → exit 0, 41 pages built
```

When no rung was reachable:

```
Untested: the R2 upload path needs a real bucket. Read the diff only — rung 4.
```

That last sentence is acceptable. Silence plus "done" is not.

## UI changes

A visual claim needs the artifact in front of you: a screenshot you actually opened, a browser
session you actually drove. Say which you did.

```
Verified at rung 3: drove the login flow in agent-browser, screenshot at /tmp/login-after.png
```

Never describe an image you have not read. "It looks right" about a screenshot nobody opened is a
claim with no evidence.

## Before a commit or push

The repo's `AGENTS.md` § Commands table is the pre-flight list. Run it, do not sample it.

```bash
bun run build && bun run check-types && bun test
```

If a command is documented but broken, say so once and fix it or delete the row — a command in
the table that nobody can run is worse than a missing row.

## The trap log

When a change took longer than it should have, the cause was one of these. Record it (symptom →
cause → fix) in the file that owns that area, then move on.

| Symptom | Usually |
| --- | --- |
| "Works locally, fails in CI" | A config value read outside `config.py` / not in `.env.example` |
| "Types pass, runtime fails" | A boundary not validated; a cast at an external call |
| "Test passes, user sees broken UI" | The test sits below the seam the bug lives above |
| "Fixed, then broke again" | No test at the seam — the fix was a probe |
| "Migration ran, app cannot read" | Migration ran against the wrong database |

## Pinning a criterion

Ask once: *will this behaviour be cheap to check again?*

- **Yes** → write the test now, in the same change.
- **No, it needs a human or a paid service** → state the manual check in the reply as the next
  action, and say it will need re-running.
- **No, it is a one-time migration** → the run's output *is* the evidence. Save the output.

## Related

- What the repo's green command is → that repo's `AGENTS.md` § Commands
- Where a rule about proof belongs → skill `agent-rules` § The tier test
- Browser-driven verification in detail → [`LADDER.md`](LADDER.md)
