# Decision Archive Rule (Overwrite -> Archive, Never Delete)

When a decision is revisited and the conclusion changes, in Notion:

1. **Create the new Decisions row** with `Supersedes` -> the old row:
   ```json
   "Supersedes": {"relation":[{"id":"<old_decision_page_id>"}]}
   ```
2. **Mark the old row superseded:**
   ```bash
   nb PATCH /v1/pages/<old_decision_page_id> '{"properties":{"Status":{"select":{"name":"Superseded"}}}}'
   ```
3. **Record the forward link** in the old row's body - there is no `superseded_by` property:
   ```bash
   nb PATCH /v1/pages/<old_decision_page_id>/markdown '{"type":"update_content","update_content":{
     "content_updates":[{"old_str":"## Related",
       "new_str":"## Related\\n- Superseded by <mention-page url=\"https://www.notion.so/<new_id>\">New title</mention-page>"}]}}'
   ```
4. **The decision log view updates itself** - no index file to edit.

**Never delete a decision - only supersede.**

The old row stays in the Decisions data source with Status = Superseded; it is not moved to an
archive data source and it is not deleted. An Archive row is for daily notes and old content, not
for decisions.
