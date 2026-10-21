---
name: second-brain-skills-autofix
description: "Auto-improve second-brain skills on demand - create new skills from the Notion contract, patch outdated skills, fix bugs found during use, and keep all second-brain skills consistent. Use when the user says 'improve this skill', 'update the X skill', 'this skill is wrong', 'add a skill for Y', 'the skill missed a step', 'fix the skill'. NOT for: running a second-brain operation (use second-brain-operations), or general skill authoring (use writing-skills)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, Skills, Meta, API]
    related_skills: [notion-second-brain, second-brain-operations, second-brain-inbox-curation, second-brain-clipping-processor, second-brain-daily-note-curation, second-brain-weekly-review, second-brain-summary, second-brain-synthesis, second-brain-action-items, second-brain-project-area-creator, second-brain-decision-manager, second-brain-cross-linker]
---

# Second-Brain Skills Autofix

Auto-improve second-brain skills on demand. This skill is the **meta-skill** - it reads, analyzes,
creates, patches, and keeps the second-brain skills consistent with the Notion contract
(`notion-second-brain`) and actual usage patterns.

**Contract: `notion-second-brain`.** Read it first - it is the source of truth for the data
sources, property names, select options, markdown dialect and rate limit.

## Where the Skills Live

```bash
SKILLS_DIR=~/Documents/01-Projects/Work-Of-Ekajaya/skills
AGENT_SKILLS_DIR=~/.agents/skills
```

The skills repo is still a git repo - skill files are versioned there. The *vault* is Notion now, so
there is nothing to commit for second-brain **content**.

## All Second-Brain Skills

| # | Skill | Purpose |
|---|-------|---------|
| 0 | notion-second-brain | the contract - data sources, properties, markdown, rate limit |
| 1 | second-brain-operations | control panel - explains the full system |
| 2 | second-brain-inbox-curation | scan the Inbox, classify into PARA |
| 3 | second-brain-clipping-processor | process web clippings -> Notes rows |
| 4 | second-brain-daily-note-curation | extract + archive daily notes |
| 5 | second-brain-weekly-review | generate the 6-section weekly review |
| 6 | second-brain-summary | quick summary of note/project/area/topic |
| 7 | second-brain-synthesis | cross-note synthesis + gap analysis |
| 8 | second-brain-action-items | extract tasks from raw notes |
| 9 | second-brain-project-area-creator | create new projects/areas |
| 10 | second-brain-decision-manager | create/supersede decisions |
| 11 | second-brain-cross-linker | find orphans, add relations |
| 12 | second-brain-skills-autofix | this skill - keeps the others consistent |

## Workflow

### Phase 1: Understand the Request

1. **"Fix skill X"** - the skill has wrong commands, missing steps or outdated info
2. **"Add a skill for Y"** - create a new skill from the contract rules or the user's description
3. **"Update skill X to match the contract"** - the property vocabulary changed, the skill needs a
   sync
4. **"This skill missed X"** - the user found a gap during use
5. **"Audit all skills"** - check every skill against `notion-second-brain` for consistency

### Phase 2: Read Current State

```bash
# the skill to fix
cat "$SKILLS_DIR/<skill-name>/SKILL.md"

# the source of truth
cat "$SKILLS_DIR/notion-second-brain/SKILL.md"

# related skills for cross-reference consistency
cat "$SKILLS_DIR/<related-skill>/SKILL.md"
```

### Phase 3: Analyze the Gap

Compare what the skill says vs what it should say:

| Check | What to look for |
|-------|-----------------|
| **API calls** | Do the curl calls still work? Right method, right endpoint, right header? |
| **Token** | Does it read `NOTION_API_KEY` from the workspace `.env`, or does it still point at `~/.hermes`? |
| **Data sources** | Are the property names the ones in the contract? (Notion property names are case-sensitive.) |
| **Select values** | Are the option names real? An unknown value silently creates a new option. |
| **Markdown dialect** | Escaping, callouts, tables, mention syntax correct? |
| **Tagging rules** | Only `status/*` and `type/*`? `type/task` not `type/tasks`? |
| **Linking** | Relations set on one side only? Mentions use `<mention-page url="https://www.notion.so/ID">`? |
| **Cross-references** | Skill names correct and not stale? |
| **Cron references** | Job ids and schedules still accurate? |
| **Edge cases** | Any new pitfalls discovered during use? |

### Phase 4: Apply the Fix

#### Option A: Patch an existing skill

Targeted fixes - replace the outdated block with the corrected one:

```bash
# edit the file in place, then verify
grep -n "<outdated text>" "$SKILLS_DIR/<skill-name>/SKILL.md"
```

#### Option B: Create a new skill

Create `$SKILLS_DIR/<new-skill-name>/SKILL.md` with the live repo's frontmatter format:

```yaml
---
name: <new-skill-name>
description: "<one long quoted line with 'Triggers on: ...' and 'NOT for: ...' clauses>"
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Notion, Second-Brain, ...]
    related_skills: [notion-second-brain, ...]
---
```

Then, per the live repo conventions (`AGENTS.md`):
1. add `CHANGELOG.md` with a `## [1.0.0]` heading matching the version
2. add a row to the README published-skills table: `| [name](./name) | 1.0.0 | desc |`
3. add the `!/<skill-dir>/` allowlist entry to `.gitignore` (it is deny-by-default)
4. symlink it into the agent skills dir: `ln -s "$SKILLS_DIR/<skill-dir>" "$AGENT_SKILLS_DIR/<skill-dir>"`
5. do **not** add it to `skills.json` - that file is only for third-party skills

#### Option C: Full rewrite

For a major overhaul, rewrite the whole `SKILL.md` and keep the frontmatter format above.

### Phase 5: Verify

1. **Load the skill** - confirm it loads without errors
2. **Check the symlink** - `ls -la "$AGENT_SKILLS_DIR/<skill-name>"`
3. **Test a key command** - if the skill has API calls, run a read-only one (e.g. a data-source
   query) to verify the endpoint and the property names
4. **Cross-reference** - check that related skills still reference the correct name
5. **Check the contract** - no property, select value or endpoint that is not in
   `notion-second-brain`

### Phase 6: Commit

The skills repo is versioned:

```bash
cd "$SKILLS_DIR"
git add skills/ 2>/dev/null || git add .
git commit -m "fix: update <skill-name> skill - <reason>"
git push
```

## Common Fix Patterns

### Fix 1: Hardcoded path or wrong token location

**Problem:** the skill points at `~/.hermes/.env` or a hardcoded vault path.

**Fix:** use the workspace `.env` and the ledger:

```bash
export WORKSPACE="${WORKSPACE:-$HOME/Documents/01-Projects/Notion-Migration}"
[ -f "$WORKSPACE/.env" ] && set -a && . "$WORKSPACE/.env" && set +a
LEDGER="$WORKSPACE/migration/ledger/notion_db_ids.json"
```

### Fix 2: Stale tag reference

**Problem:** `type/tasks` instead of `type/task`.

**Fix:** replace every occurrence with `type/task`.

### Fix 3: Outdated data source or property

**Problem:** the skill writes `Status` = `Active` on a data source whose option is `Ongoing`.

**Fix:** check the property table in `notion-second-brain` section 2 and use a real option. An unknown
value creates a new option instead of failing - so a typo silently corrupts the schema.

### Fix 4: Missing edge case

**Problem:** the user found a scenario the skill did not handle.

**Fix:** add a new edge-case entry with the discovered pattern.

### Fix 5: Cron job id changed

**Problem:** the skill references a cron job id that no longer exists.

**Fix:** list the current jobs first (`cronjob(action='list')`) and update both the id and the
schedule.

### Fix 6: Vault-era mechanics left over

**Problem:** the skill still greps the vault, writes `[[wikilinks]]`, calls `qmd`, or moves
files with `mv`.

**Fix:** replace with the API equivalent - a data-source query, a relation + mention, a page
create/update, or (for "moving" a row) create the destination and set the source row's Status.

## Audit Checklist

- [ ] Every second-brain skill references `notion-second-brain`
- [ ] No skill mentions `qmd`, `$VAULT`, `OBSIDIAN_VAULT_PATH`, `[[wikilinks]]` or
      `~/.hermes`
- [ ] The token comes from `NOTION_API_KEY` in the workspace `.env`
- [ ] Every property name and select value exists in the contract
- [ ] Tagging rules are `status/*` + `type/*` only
- [ ] Relations are set on one side only; mentions use the `https://www.notion.so/<PAGE_ID>` form
- [ ] Every skill has `name:`, `description:` and a SemVer `version:` in frontmatter
- [ ] Descriptions include trigger phrases and NOT-for clauses
- [ ] Every skill has a `CHANGELOG.md` with a matching `## [x.y.z]` heading
- [ ] Every skill has a README published-skills row and a `.gitignore` allowlist entry
- [ ] Skills are symlinked into the agent skills dir
- [ ] Skills are committed to the skills repo

## Anti-Patterns

- Don't rewrite a skill from scratch when a targeted patch would do
- Don't forget the repo chores for a new skill: CHANGELOG, README row, `.gitignore`, symlink
- Don't change a skill's `name:` field without updating every cross-reference
- Don't update a skill without updating `notion-second-brain` if the rule itself changed
- Don't skip verification - always load the skill after editing
- Don't commit without a descriptive message explaining what changed and why
- Don't invent a Notion property, select value or endpoint
