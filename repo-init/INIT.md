# Bootstrap a repo

Run when a repo has **no** `AGENTS.md`. Takes 10–15 minutes for a repo you know; an hour for one
you don't.

If the repo already has an `AGENTS.md`, this is the wrong skill: run `repo-align`, which audits
the existing layer instead of replacing it.

The failure this prevents: a repo where every session re-derives the same facts, and the rules
that matter live in a skill the agent never opens. See skill `agent-rules` § The tier test.

## 0. Ask about dotfiles, before anything else

One question cannot be answered from the repo, and the answer changes what steps 1, 4 and 5 may
write: **does this project use `ekajaya740/dotfiles`?**

```bash
ls -d ~/dotfiles 2>/dev/null          # does the machine even have it?
git config --global --get user.email  # is this the same person?
```

Ask once, plainly, and wait for the answer — do not infer it from the repo's file list:

> Does this project use your `ekajaya740/dotfiles`? They are tuned for **omp** (omp-jev routing,
> 9router model aliases, the `claude/` and `jev/` deploy scripts), so a repo on another harness
> inherits wiring it will never read.

Two outcomes:

| Answer | What changes |
| --- | --- |
| **Yes** | The dotfiles are the machine layer. `AGENTS.md` records them as a pointer, not a copy: which harness shims come from them, and that `bash ~/dotfiles/bootstrap.sh` is the machine setup step. Do not restate their rules here — one rule, one home. |
| **No** | Write the shims by hand in step 4, and record no dotfiles dependency anywhere. A repo that does not use them must not document them. |

**Done when** the answer is recorded in one line of `AGENTS.md` under the stack section — either
"machine layer: `ekajaya740/dotfiles` (omp-tuned)" or "self-contained, no dotfiles dependency".

This is a question, not a lookup: a repo cloned on a machine with `~/dotfiles` is not evidence that
it uses them.

## 1. Read the repo before writing a word

Answer these from the files, not from memory. Do not ask the user anything you can look up.

```bash
ls -a
git remote -v
cat package.json pyproject.toml Cargo.toml go.mod 2>/dev/null | head -60
ls .github/workflows 2>/dev/null
```

| Question | Where the answer lives |
| --- | --- |
| What does this repo build? | README first line, `package.json` `description` |
| How do I run it? | `package.json` scripts, `Makefile`, `justfile`, README |
| How do I know it is green? | CI workflow, `scripts/`, `package.json` `test`/`lint` |
| What is the primary branch? | `git branch -r --format='%(refname:short)'` |
| Which files hold secrets? | `.env.example`, `.gitignore`, workflow `secrets.*` |
| Is there existing agent instruction? | `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `.github/copilot-instructions.md` |

**Done when** you can name the build command, the green command, and the primary branch without
opening a file again.

## 2. Pick the tier for each fact

Everything you learned is either **binding** (an agent that never opened another file would
break it) or **detail** (only matters when touching that area). The test, in full, is in
`agent-rules` § The tier test.

Binding goes in `AGENTS.md`. Detail goes in `docs/agents/<area>.md` and is reached by one line
in `AGENTS.md`'s index. A repo with fewer than ten binding rules needs no `docs/agents/` yet —
create the directory on the first detail rule that earns a file.

**Done when** every fact you collected has exactly one destination, and nothing is in two.

## 3. Write `AGENTS.md`

Copy [`TEMPLATE-AGENTS.md`](TEMPLATE-AGENTS.md) and delete every row you cannot fill from step 1.
A short true file beats a complete aspirational one.

Keep it under about 150 lines. Every line is loaded every session, so a line that does not
change behaviour is pure cost. If the file grows past that, the excess is detail — move it and
leave a pointer.

**Done when** the file's Hard Rules section names only things an agent would otherwise get wrong,
and each one has a real consequence stated.

## 4. Add the harness shims, never a second copy

Different harnesses read different files. A shim points; it never restates.

| Harness | File | Content |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` | `@AGENTS.md` (one line) |
| Cursor | `.cursor/rules/000-agents.mdc` | `alwaysApply: true` + `See AGENTS.md` |
| Copilot | `.github/copilot-instructions.md` | `See AGENTS.md` |
| Codex, opencode, most others | `AGENTS.md` | already native |

A shim that repeats the rules is the exact drift `agent-rules` § One rule, one home forbids.
If a harness genuinely cannot read a pointer, it still gets the pointer plus a one-line summary —
not the file.

**Done when** a second harness opening the repo lands in `AGENTS.md` in one hop.

## 5. Record the commands that make it green

One table, in `AGENTS.md`, naming the command a fresh clone runs to prove it works:

```md
| Check | Command | Green when |
| ----- | ------- | ---------- |
| Install | `bun install` | exits 0 |
| Build | `bun run build` | exits 0 |
| Types | `bun run check-types` | exits 0 |
| Tests | `bun test` | exits 0 |
```

This table is what `verify-change` reads before claiming anything works. Without it, "it works"
means "it worked on my machine, in a way I have already forgotten."

**Done when** you can run the green command from step 1 and it passes on a clean checkout.

## 6. Pin the project's skills

`AGENTS.md` says what is true; a skill says how to do it. Both travel with the repo, so the skill
store goes in the repo too — `.agents/skills/` plus a committed `skills-lock.json`.

```bash
cd <repo-root>
npx skills@latest add mattpocock/skills -s grilling -s implement -s tdd -s code-review -s pr
```

No `-y`: it answers the consent question for the user. Show them the source, the author, the
licence and the five skill names, then ask. Omit `-g` — a global install is invisible to a fresh
clone. Then gitignore `.agents/` and commit `skills-lock.json`, so
`npx skills@latest experimental_install` reproduces the set.

Name the store in `AGENTS.md`, next to the green commands — a pointer the agent can follow.

**Done when** a clean checkout runs `experimental_install` and the named skills resolve.

The full set, per project kind, and the lock-versus-manifest distinction →
[`SKILLS.md`](SKILLS.md).

## 7. Prove the file works

Hand `AGENTS.md` to a fresh agent (or read it as one) and ask: *what would I get wrong about
this repo without this file?* Every answer that isn't in the file is a missing binding rule.
Every answer that is in the file but would never be broken is noise to delete.

Then run the checks from skill `verify-change` § Before a commit or push, and record the result.

**Done when** a new session's first action, informed only by `AGENTS.md`, is correct.

## Related

- What to install and how to pin it → [`SKILLS.md`](SKILLS.md)
- The tiers and the registry → skill `agent-rules`
- The repo's shape and stack defaults → skill `project-scaffold`
- What "green" has to prove → skill `verify-change`
