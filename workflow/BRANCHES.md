# Branch topology

The branches that outlive a task, what each one is for, and how a change reaches them.

A feature branch is born, merged, deleted. A **permanent branch** is one that never merges away,
because something outside the repository depends on it continuing to exist and to mean one thing.
Before an agent can put work anywhere, it has to know which of those it is looking at.

## Why a repo needs a permanent branch at all — the explanation to give the user

Ask this before writing a topology, in these terms, because it is the reason the question is not
ceremony:

> **Deployments fire on merge, and they fire per target branch.** A merge to the branch that
> mirrors production runs production. That is the whole reason a second permanent branch exists: to
> have somewhere a change can be *deployed and tested* without reaching users. Without one, either
> every change goes to production, or nothing is ever tested in an environment that looks like it —
> and both of those are a decision someone made without noticing.
>
> **A permanent branch is also a review boundary.** If a document change merges to the same branch
> as a schema migration, then every prose edit runs the migration. A branch whose purpose is "docs
> only, no deploy" makes that impossible by construction, which is more reliable than a rule saying
> "be careful".
>
> **And it is what the repository's own conventions become.** Release automation, tags, branch
> protection, and preview environments are all configured per branch name. A permanent branch named
> before the first deploy is a policy the tooling can key on; one invented later is a migration.

So the question is never "should this repo have branches" — every repo has at least one. It is
**how many, each mirroring what, and who is allowed to push to it.** Those answers cost nothing
now and cannot be retrofitted cheaply once CI, tags, and deploy targets name them.

## Ask these, once, and write the answers down

Do this at init, and at align when the repo has branches but no stated topology. It is a
conversation, not a lookup: nothing in the filesystem says which branch mirrors production.

| Question | Why it cannot be inferred |
| --- | --- |
| **Which branch is production, and what is it called?** | `main`, `master`, `trunk`, `release` — a rename can leave one stale. Tags and releases point at it, so getting this wrong tags the wrong code. |
| **Which branch is the staging mirror, if any, and what is it called?** | `beta-master`, `staging`, `dev`, `preview`. It may be a preview environment, a half-finished migration, or a dead fork. Only the owner knows. |
| **What local conventions does the repo already have?** | PROFILL: production is `master`, staging is `beta-master`, prose lives on `playbook`, SEO work on `seo`. The names encode the purpose, and a new branch that repeats an existing purpose is a second home for one thing. |
| **Are there any permanent branches?** | These are the branches no issue may work on directly. Everything else is a working branch, created per issue and per worktree. |

**Done when** the answer fits in one table, every permanent branch names the environment it mirrors
or the content it exclusively carries — and every name in that table is one the repo already has.

## The topology record

One table, in `docs/agents/version-control.md` — any area doc may own it; the check looks in
`AGENTS.md` and every `docs/agents/*.md`.

```md
| Branch | Mirrors | Syncs from | Merge produces | Direct push |
| --- | --- | --- | --- | --- |
| `main` | production | — (the apex) | a deploy + a release tag | no — PR only |
| `beta` | staging | `main` | a preview, not a release | no — PR only |
| `docs` | nothing (prose only) | `main` | a gate run, no deploy | yes, `.md` only |
```

**The names above are examples, not a naming scheme.** A branch is identified by its role, and the
project picks the word: `master` or `main` for production, `beta-master` / `staging` / `dev` for a
staging mirror, `playbook` / `docs` / `wiki` for prose. Never introduce a branch to match this
table — read the roles the project already has, and record *its* names. A repo whose production
branch is `master` and whose staging branch is `beta-master` gets those two rows and no `beta`.
Prose may live on no branch at all if the repo has no deploy to avoid.

**The table lists permanent branches and nothing else.** Working branches are not rows: they are
created per issue and per worktree, and they are deleted when the task lands. A table that tries to
enumerate them is stale the day it is written, and the staleness buries the few lines that matter.
The count of permanent branches is the whole topology; everything else is a convention, covered in
§ Working branches.

Fill `Direct push` from what CI actually does, not from what would be tidy: a branch no workflow
names can be pushed to safely, and that is the fact to record.

**`Syncs from` is the column you cannot guess, and the one that does damage when it is wrong.**
It names the single direction a permanent branch takes updates from. Record `—` for the apex and
one source for every other branch.

## Permanent branches are never merged into each other

**A permanent branch takes work by merge *from* its source, and by nothing else. Do not merge one
permanent branch down into a sibling.** When work must reach a second permanent branch, **port it
onto a fresh working branch cut from that branch's own source** and land it the normal way.

The reason is measured, not stylistic. Two branches that both carry real work have diverged; a
merge between them is mostly conflict resolution, and resolving conflicts in favour of the target
deletes the target's own work. PROFILL's `seo` branch is the worked example: it has never taken a
commit from `beta-master` (every `beta-master`-only commit tested for ancestry in `origin/seo`
comes back negative), and both syncs in its history run the other way. Its own doc states the
consequence plainly — nothing reaches `master` by merging `seo` down, because that merge
"mostly resolves conflicts and deletes `master` work".

The mirror image is also a rule: **prose and rules flow from the apex outward, never inward.** A
rule binds where it is stated first and is then copied out; a permanent branch whose docs are
behind the apex carries a backlog, not a steady state. Two copies of a rule are one rule stated
zero times plus a drift — see skill `agent-rules` § One rule, one home.

So `Syncs from` has exactly one right answer per branch, and a direction that reads "either way"
is the defect the column exists to catch.

## One permanent branch is a complete answer

**A repo with a single permanent branch is not missing anything.** Small repos, docs vaults and
libraries with no deploy target need their production branch and nothing else — every change is a
working branch that merges to it. Do not add a staging branch to a repo with no deploy to hide
from, and do not add a prose branch to a repo whose gate is fast enough that prose and code can
share one PR.

What makes the topology wrong is a branch with **no stated purpose** or **two branches with the
same purpose**. Not the count.

## Working branches: per issue, per worktree, deleted on landing

A working branch exists because one issue is being worked on, and stops existing when it merges.
It is not part of the topology and nothing records it — the issue tracker and `git worktree list`
are its record, and both are live rather than written down.

- **Never author on a permanent branch.** Feature work happens on a branch cut from the branch it
  targets, and the target is named before the first edit. A session that starts on a permanent
  branch and begins editing is the failure this rule exists to stop, and nothing else catches it:
  the edit is valid code, on the wrong branch.
- **The branch name states the issue and the task** — `fix/<issue>-<slug>`, `feat/<slug>`,
  `docs/<slug>`, or whatever prefix the project already uses — so `git branch --show-current`
  answers both questions without a lookup.
- **Cut from the remote ref, not the local one.** `git fetch origin` then
  `git switch -c <name> origin/<base>`. A local copy of the base is whatever the last session left
  there.
- **One issue, one branch, one worktree.** Two issues on one branch cannot be reverted or reviewed
  separately, and the second inherits whatever the first broke. A repo that runs several tasks in
  parallel gives each one its own worktree, so a permanent branch keeps a stable clone as the
  environment source of truth and a task never runs in it. The full procedure — ports, environment
  files, teardown — belongs to the repo's own `docs/agents/worktree.md`.
- **Check the branch before every commit**, not once at the start. A merge, a `git switch` in the
  wrong window, or a stale tool call moves a long session off its branch, and the commit lands
  somewhere nobody looked.
- **Delete the branch when it lands, and never delete unmerged work.** A merged branch is
  `git branch -d`; a branch carrying commits absent from every permanent branch is not cleanup
  material — read `git log --oneline <permanent>..<branch>` first, and ask before touching it.
  `-D` throws away the only reference to those commits.

## Related

- Writing the rule down, and its tier → skill `agent-rules` § The tier test
- Where the record goes at init → [`repo-init/INIT.md`](../repo-init/INIT.md) § 1b
- Auditing a repo that has branches but no topology → skill `repo-audit`, check `BRANCH-01`
- Proving a change before it merges → skill `verify-change`
