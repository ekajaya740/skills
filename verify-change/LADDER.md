# The evidence ladder, in detail

The expanded version of skill `verify-change` § The ladder: how to actually reach each rung, and
when a rung is lying to you.

## Rung 1 — automated test

The only rung that keeps working after the session ends.

```bash
# the shape that proves a fix, not just a pass
git stash && bun test <path>     # red: the test sees the bug
git stash pop && bun test <path> # green: the change is what fixed it
```

If the test passes before the change, it is not pinning the thing you fixed.

**Where to write it:** the highest seam that still exercises the behaviour. A handler test beats
a service test beats a unit test on a helper, because the handler is where the wiring lives.

**When it is a lie:** the test asserts on a mock of the very thing that changed. That test verifies
your mock, not your code.

## Rung 2 — command output

The cheap proof for anything the toolchain understands.

| Change | Command | What green means |
| --- | --- | --- |
| Types changed | `tsc --noEmit` / `pyright` | No contract broke anywhere in the repo |
| Bindings, routes, config | `wrangler deploy --dry-run` | The config resolves without shipping |
| Package boundaries | `turbo run build` | Every package builds in dependency order |
| Container | `docker build .` | The image assembles |
| Schema | `drizzle-kit generate` | The migration matches the schema |

**When it is a lie:** a dry-run resolves config but does not run the code. Passing `--dry-run`
means "deployable", not "deployed and working".

## Rung 3 — real run

The only rung that proves the wiring.

```bash
# start it
bun run dev &
# hit it
curl -sS -X POST localhost:3000/api/things -H 'content-type: application/json' -d '{"a":1}'
# paste the first meaningful line
# {"id":"…","createdAt":"…"}
```

For a UI, rung 3 means a browser you drove:

```bash
agent-browser open http://localhost:3000/login
agent-browser snapshot
agent-browser screenshot /tmp/login-after.png
```

Then **read the screenshot**. A path printed without looking at the file is not evidence.

**When it is a lie:** you hit a different build than the one you changed, or a stale process is
still serving the old code. Restart, then re-hit.

## Rung 4 — read the diff

Legitimate only for artifacts whose text *is* the behaviour: docs, comments, config you cannot run,
a skill's `SKILL.md`.

```bash
git diff --stat && git diff -- <path>
```

**When it is a lie:** anything with a runtime. A correct-looking diff is the normal state of a
broken change.

## Rung 5 — reasoning

Not evidence. Say so in one clause and move on:

```
Untested: no local Postgres, so the migration is unverified (rung 5).
```

The value of naming it is that the next session does not inherit an unmarked assumption.

## Matching the rung to the blast radius

| Blast radius | Minimum rung |
| --- | --- |
| One pure function | 1 |
| One route or handler | 1 or 3 |
| Shared package used by three apps | 1 + 2 at the root |
| A migration | 3, then query the result |
| Anything that deploys | 3, then 2 as a dry-run of the next deploy |
| Anything that touches money, auth, or deletion | 1 + 3, and say both |

## The report

When a task involved several changes, report **one line per claim**, not a paragraph:

```
- `POST /api/things` returns 201 — rung 3, curl above
- `createThing` rejects empty name — rung 1, `bun test things.spec.ts`
- migration adds `status` — rung 3, `psql -c '\d things'` shows the column
- README updated — rung 4
```

A reader can then see which claims are load-bearing and which are prose.

## Related

- The ladder and the claim sentence → [`SKILL.md`](SKILL.md)
- Writing a test at the right seam → skill `tdd` (if installed)
