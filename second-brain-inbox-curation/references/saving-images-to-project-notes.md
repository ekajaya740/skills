# Saving Images to Project Notes

When the user sends an image (screenshot, payment proof, receipt, photo) related to a project, put
the **binary in Google Drive** and link it from the project row in Notion.

## Why Drive and not Notion

Notion file URLs returned by the API are **pre-signed and expire**. A file link inside a page
body stops working. Durable binaries belong in Google Drive; Notion holds the text and the
relations.

## Pattern

1. **Determine the project** - from context, or ask the user
2. **Upload the image to Drive** and capture the webViewLink:
   ```bash
   python3 "$SKILL_DIR/email-to-vault-resource/scripts/drive_upload.py" upload \
     /tmp/<image-file> <target_folder_id> --name "payment-50pct.jpg"
   ```
   Project attachments -> the project's Drive folder, area -> the area's Drive folder. Find the
   folder ids with `python3 "$SKILL_DIR/email-to-vault-resource/scripts/drive_upload.py" --list`.
3. **Use a descriptive filename** - lowercase, hyphens, no spaces: `payment-50pct.jpg`,
   `payment-receipt-june-2026.jpg`, `bug-screenshot-login.png`
4. **Link it from the project row** - in the payment task row's body or in the project's note:
   ```bash
   nb PATCH /v1/pages/<project_page_id>/markdown '{"type":"update_content","update_content":{
     "content_updates":[{"old_str":"## Payment",
       "new_str":"## Payment\\n- [x] 50% paid - [payment-50pct](https://drive.google.com/...)"}]}}'
   ```
5. **Never overwrite an existing file** - if the name conflicts, append `-2`, `-3`
6. **Update the Area-level Payment note** when the project belongs to a business Area (see
   `area-payment-index.md`)

## Rules

- **The binary never lives in Notion** - only the Drive link does
- **Never overwrite** an existing file
- **No frontmatter/properties needed for the image itself** - it is a Drive object
- **Link from the project or its task row** so the proof is reachable from the second brain

## Fallback when vision fails

If image analysis is unavailable, do not just say "I can't see it":
1. acknowledge that the image could not be analyzed
2. ask whether the user wants it saved to a project's Drive folder
3. if the user says yes (or implies it), save it immediately and link it
