# The rule registry

An index of every binding rule: what it says, where it is stated, where the detail lives. It
**quotes**; it never states a rule a second time.

## Format

One table, split by owner file:

```md
### From AGENTS.md § Hard rules

| Rule | Says | Owner | Detail |
| ---- | ---- | ----- | ------ |
| Never guess a specification | Underspecified scope, criteria, naming, or surface → stop and ask, don't assume | `AGENTS.md` | `docs/workflow.md` § Phase 1 |
| Prove it before calling it done | A claim names the layer it was verified at | `AGENTS.md` | `docs/testing.md` |
```

Columns that matter:

- **Rule** — the name an agent would use when referring to it. Short, stable, greppable.
- **Says** — one clause, the substance. Not the full text; that lives at the owner.
- **Owner** — the one file that states it. Never two entries.
- **Detail** — where to read more, or `—`.

## Maintaining it

| Moment | Action |
| --- | --- |
| Adding a binding rule | Add a row in the same commit. An unregistered rule is invisible. |
| Editing a rule | Edit the owner. Update the `Says` clause only if the substance moved. |
| Deleting a rule | Delete the row. |
| Finding a rule in two files | Keep the owner, make the other a pointer, then check the registry has one row. |
| A rule fires from the detail tier but gets violated | Wrong tier, not a missing row. Promote it — see [`RULE-TIERS.md`](RULE-TIERS.md). |

## Checking for duplication

The registry makes duplication *detectable*. Detection can be manual or scripted.

**Manual pass**, before adding any rule:

```bash
rg -n --no-heading 'the substance in three or four words' AGENTS.md CODING_STANDARDS.md docs/
```

Two hits in two files means one of them must become a pointer.

**Scripted**, when the rule set has settled — a small script that holds a `RULES` array of
`{ name, owner, phrase }` and fails when `phrase` appears in a file other than `owner`. Keep the
registry's `Rule` names in sync with that array so a reader can see the guard's coverage.

## Known gap

A guard only checks the rules registered in it. A rule stated twice but not registered is not
caught. Say so where the guard is documented — a check that claims full coverage it does not have
is worse than a check that names its bound.

## Related

- Which tier a rule belongs to → [`RULE-TIERS.md`](RULE-TIERS.md)
- Resolving a collision → skill `agent-rules` § When two rules collide
