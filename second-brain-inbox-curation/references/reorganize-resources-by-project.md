# Reorganize Notes By Project Relevance

When the user asks to reorganize reference notes by project relevance (e.g. "relate Git/Java/Web
to Project X, Node.js to Project Y, archive all except Fitness and Finance").

## Workflow

1. **Identify the categories from the user request** - which topics go to which project/area, and
   what to keep or archive
2. **List the current standalone reference rows**:
   ```bash
   nb POST "/v1/data_sources/$NOTES_DS/query" '{"filter":{"and":[
     {"property":"Type","select":{"equals":"Reference"}},
     {"property":"Project","relation":{"is_empty":true}}]},"page_size":100}'
   ```
3. **Look up the target rows** by name (`nb POST /v1/search`) and note their page ids
4. **Set the relation** on each note - one side only, Notion mirrors it:
   ```bash
   nb PATCH /v1/pages/<note_page_id> '{"properties":{"Project":{"relation":[{"id":"<project_id>"}]}}}'
   ```
5. **Archive the rest** - create an Archive row (`Name`, `Type`, `Original Path` = the note's
   page id, `Archived` date) and mark the note's Status = `Archived`. Never delete a page for a
   reorganisation.
6. **Verify counts** at each destination after the moves
7. **No reindex needed** - there is no QMD, no index, no reindex step
8. **No git commit** - the vault is not a git repo any more

## Pitfalls

- Don't move a note twice - check the current relations first
- Don't delete a note that already has a Project/Area relation
- Google Tasks naming - when an area/project is renamed, update the Google Tasks list name too
  (DELETE + recreate, due to an API 404 quirk on PATCH)
- Area name stability - names use hyphens; never change to spaces unless asked
- Space the PATCH calls ~350 ms apart (3 requests/second limit)

## Example distribution

| Destination | Topics |
|---|---|
| Notes related to PT-SUM-Digital-Konsultan | Git/GitHub, Java/Spring, Web Dev/Frontend, Backend/API, DevOps/Docker |
| Notes related to Profill-Link-Monorepo-Web | Git/GitHub, Node.js, Web Dev/Frontend, Backend/API, DevOps/Docker, Cloudflare, Supabase |
| Standalone Notes rows | Fitness, Finance, AI, lifestyle, language, music, books, health |
| Archive rows | Everything else |
