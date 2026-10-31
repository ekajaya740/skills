# Align checklist

One row per check. Every check is mechanical: it has a shell command that finds the candidate, a
test that decides `drift` vs `ok`, and a fix. Run only the enabled sections.

Ids are stable — cite them in the report so the user can say "fix 2 and 5".

## `rules`

| Id | Detect | Drift when | Fix |
| --- | --- | --- | --- |
| `RULE-DUP-01` | `rg -n 'the same 4+ words' AGENTS.md docs/ *.md` | The substance appears in two files | Keep the owner; replace the copy with a pointer |
| `RULE-DUP-02` | Read every `**bold**` claim in `AGENTS.md`, `rg` its subject across `docs/` | A doc restates it instead of linking | Link the doc line to `AGENTS.md` § Hard rules |
| `RULE-TIER-01` | For each `AGENTS.md` hard rule, ask: would an agent that never opened a detail file break it? | No, and it is not needed every session | Move to `docs/agents/<area>.md`, leave a one-line pointer |
| `RULE-TIER-02` | For each `docs/agents/*.md`, find rules phrased as universal ("always", "never", "every file") | A universal rule lives only in detail | Promote to `AGENTS.md` |
| `RULE-SHIM-01` | `cat CLAUDE.md .github/copilot-instructions.md .cursor/rules/*.mdc 2>/dev/null` | Any shim restates rules instead of pointing at `AGENTS.md` | Replace with `@AGENTS.md` or a one-line pointer |
| `RULE-NOOP-01` | Read each binding rule | It states something a competent agent already does ("write clean code", "be thorough") | Delete it |
| `RULE-CAP-01` | `rg -c '^- \*\*' AGENTS.md`, plus `rg --files -g '*.md'` for the budget and its test | More than ~7 hard rules — unless `AGENTS.md` declares `rules-budget: N` **and** a doc other than `AGENTS.md` states the admission test (`RULE-TIER-01`) behind it | Demote the weakest to detail, or declare the budget the tier test justifies — with the test written where a reader lands when asking why a rule binds |
| `RULE-REG-01` | Is there a registry table mapping rule → owner → detail? | Binding rules exist with no index | Add one — see skill `agent-rules` § Keeping the registry |
| `RULE-BOUND-01` | Read each prohibition ("never touch production") | No concrete boundary named (which host, which path, which command) | Add the boundary, or delete the rule |

## `structure`

| Id | Detect | Drift when | Fix |
| --- | --- | --- | --- |
| `BRANCH-01` | `git branch --format='%(refname:short)'`, then grep `^\| *[Bb]ranch` across `AGENTS.md docs/agents/` | More than one branch and no `\| Branch \|` table. One branch is `ok` by definition — the count is never the defect | Ask which mirrors production, which is staging, which carry content only; record it. See skill `workflow` § [`BRANCHES.md`](../workflow/BRANCHES.md) |
| `STRUCT-01` | `ls -a` at the root | A top-level folder with no one-line justification | Justify it in `docs/architecture.md` or delete it |
| `STRUCT-02` | `find . -maxdepth 2 -name 'utils*' -o -maxdepth 2 -name 'shared*' -o -maxdepth 2 -name 'helpers*'` | A dumping-ground folder exists | Name the concept; split or delete |
| `STRUCT-03` | `ls src tests docs scripts 2>/dev/null` | A non-trivial project has no `docs/` or `scripts/` | Create the one that is missing, with one real file in it |
| `STRUCT-04` | `cat .env.example` vs `rg -o 'process\.env\.[A-Z_]+' -N . \| sort -u` | A var read in code is missing from `.env.example` | Add it, no value |
| `STRUCT-05` | `cat .gitignore` | `.env`, build output, or `node_modules` not ignored | Add before the next commit, not after |
| `STRUCT-06` | `cat package.json \| jq .scripts` (or `pyproject.toml`) | `build`/`test`/`lint` missing or pointing at nothing | Add or delete the script |
| `STRUCT-07` | `git ls-files -s \| awk '\$1==160000'` | A submodule present with no stated purpose | Document it in `docs/architecture.md`, or remove it |
| `STRUCT-08` | `ls skills-lock.json .agents/skills 2>/dev/null` | The repo has an agent layer but no pinned skill store | Pin the set per skill `repo-init` § [`SKILLS.md`](../repo-init/SKILLS.md) |
| `STRUCT-09` | `git check-ignore .agents/skills; git ls-files skills-lock.json` | `.agents/` is committed, or the lock is untracked | Ignore `.agents/`, commit `skills-lock.json` |
| `STRUCT-10` | `npx skills@latest experimental_install` in a throwaway clone | The pinned set cannot be restored | Fix the lock, or drop the entries that upstream no longer serves |

## `verify`

| Id | Detect | Drift when | Fix |
| --- | --- | --- | --- |
| `VERIFY-01` | `rg -n 'Green when\|Passes when\|## Commands' AGENTS.md` | No commands table at all. A row reading `None yet` is honest, not drift | Derive it from the manifest/CI; if nothing is checkable, write the `None yet` row rather than invent a command |
| `VERIFY-02` | Run every command in the table | A documented command exits non-zero | Fix the command or delete the row — never leave a broken row |
| `VERIFY-03` | `ls .github/workflows 2>/dev/null` | A `code` repo that documents commands has no CI, or CI runs commands the developer cannot run locally. No documented command is `n/a`; `knowledge` with no build is `manual` | Make CI call the same scripts |
| `VERIFY-04` | `rg -n 'Loading\.\.\.\|TODO\|FIXME' --type-add 'src:*.{ts,tsx,py,go,rs}' -tsrc` | A placeholder the repo treats as done | Fix it or file it |
| `VERIFY-05` | Look for test files asserting on mocks of the changed unit | A test that passes before and after the fix | Rewrite at the seam the behaviour lives at |

## `hook`

Decided by `scripts/audit.py`, and reported under the `verify` section. The rule's owner is skill
`verify-change` § The commit hook; these rows only decide compliance.

| Id | Detect | Drift when | Fix |
| --- | --- | --- | --- |
| `HOOK-01` | Read `.githooks/`, `.husky/`, `.git/hooks/`; strip comment lines; match `bun test`, `npm test`, `pytest`, `audit.py`, `tsc --noEmit`, `vitest run`, `jest`, `run build` | A `pre-commit` or `commit-msg` runs the full suite, or the file is not executable — git skips that silently | Move the suite to CI; keep lint, format and the one cheap gate. `chmod +x` |
| `HOOK-02` | `git ls-files --error-unmatch <hook>`, then `git check-ignore`, then `git config --get core.hooksPath` | The hook is ignored by a deny-by-default `.gitignore` (so it can never ship), or it is uncommitted | Add `!/.githooks/` and commit it |
| `HOOK-02` (local) | Same commands | The hook is committed but this clone does not run it | **`manual`, never `drift`** — `core.hooksPath` is per-clone config, absent in a fresh CI checkout. Enable it, and confirm `AGENTS.md` or the README names the command |

`pre-push` is out of `HOOK-01`'s scope: the developer already waits on the network there, so a slow
push-time suite is not the bypass magnet a slow commit hook is.

## `design`

| Id | Detect | Drift when | Fix |
| --- | --- | --- | --- |
| `DESIGN-01` | `ls docs/design-system.md packages/*/DESIGN.md 2>/dev/null` | UI exists with no token layer documented | Create `docs/design-system.md` with the tokens |
| `DESIGN-02` | For each component folder with a `DESIGN.md`, diff its `tokens:` frontmatter against the tokens used in its source | Doc and code disagree | Update the doc; a token change without a doc change is drift |
| `DESIGN-03` | `rg -n '#[0-9a-fA-F]{3,6}\b' src --type-add 'ui:*.{tsx,jsx,astro,vue,svelte}' -tui` | Raw colour values in component code | Move into the token layer |
| `DESIGN-04` | `rg -n 'Loading\.\.\.' src` | Bare loading text where a skeleton belongs | Replace with a skeleton or spinner |
| `DESIGN-05` | `rg -n 'outline:\s*none\|outline-none' src` | Focus ring removed with no replacement | Add `focus-visible` styling |
| `DESIGN-06` | Compare the component index/map against the folders on disk | A component missing from the map | Add the row |

## `skills`

Only relevant to a repo that publishes or stores skills.

| Id | Detect | Drift when | Fix |
| --- | --- | --- | --- |
| `SKILLS-01` | `ls */SKILL.md` | A skill directory with no `SKILL.md` | Delete it or write the skill |
| `SKILLS-02` | For each `SKILL.md`, compare `name:` with its directory name | Mismatch | Rename one |
| `SKILLS-03` | Compare each `version:` with its `CHANGELOG.md` headings | Version with no matching heading | Add the heading |
| `SKILLS-04` | Compare the README table against `SKILL.md` versions | Table stale | Update the row |
| `SKILLS-05` | `cat .gitignore \| head -5` | Not deny-by-default, in a directory that is also a live skill store | Rewrite as an allowlist |
| `SKILLS-06` | For each skill, read only its `description` | It names no trigger branch, or lists synonyms for one branch | Rewrite: front-load the trigger, one per branch |
| `SKILLS-07` | `ls -l ~/.claude/skills/<name>` for each | Link missing or dangling | Relink, restart the harness |
| `SKILLS-08` | Read `skills.json` and `install-skills.sh` | The two disagree | Make them match, same commit |

## Reporting

Group by section, then sort by blast radius: a duplicated binding rule outranks a missing design
row, because it changes what every future session does.

```
## rules — 3 findings
| # | Check | Finding | Fix |
...

## verify — 1 finding
...
```

End with one line: `Apply which? Name the check ids.` Nothing is edited before that answer.

## Related

- The procedure → [`SKILL.md`](SKILL.md)
- Tier test and ownership → skill `agent-rules`
- The template a repo should match → skill `repo-init`
