# Weekly Review Cron Job Config

**Job ID:** `dbcdcd3626eb`
**Name:** `weekly-review-sunday`
**Schedule:** `0 4 * * 0` (Every Sunday at 04:00 WIB / 20:00 UTC Saturday)
**Last run:** 2026-07-05 OK
**Next run:** 2026-07-12

## Current Prompt

```
Generate a weekly review for the migrated second brain. Use the second-brain-weekly-review skill
to produce the review. Follow all 6 sections of the output format. The review covers the current
week (Monday through Sunday). Save the output as a Daily Notes row named
<MONDAY>-<SUNDAY>-weekly-review in the second-brain workspace: create the page with
POST /v1/pages (parent = the Daily Notes data source id from
$WORKSPACE/migration/ledger/notion_db_ids.json), or update it with
PATCH /v1/pages/{id}/markdown if the row already exists. Do not write a local file and do not run
git - the second brain lives in Notion. Finally, deliver the full review text to the user so they
can read it.
```

## Keep in sync

The prompt hardcodes the save target - the skill and the cron prompt are two separate configs that
must agree. If they diverge, the cron job writes an orphan row.

If you change the output row name or format in `second-brain-weekly-review/SKILL.md`, update the
cron prompt too:

```bash
cronjob(action='update', job_id='dbcdcd3626eb', prompt='<new prompt with the updated target>')
```

## Notes

- The review is a **Daily Notes** row, not a file. The old path
  `01-Daily-Notes/Weekly Review/<MONDAY>-<SUNDAY>-weekly-review.md` no longer exists.
- There is no git step any more. The vault is not a git repo; Notion holds the content.
