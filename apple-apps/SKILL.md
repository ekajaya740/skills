---
name: apple-apps
description: "Manage Apple Notes, Reminders, and iMessage/SMS on macOS via CLI tools (memo, remindctl, imsg)."
version: 1.0.0
author: ekajaya740
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Apple, macOS, Notes, Reminders, iMessage, SMS, productivity]
    related_skills: [obsidian, notion-second-brain]
---

# Apple Apps (Notes, Reminders, iMessage)

CLI-based access to three Apple productivity apps on macOS. All sync across Apple devices via iCloud.

> **For Find My device/AirTag tracking**, use the separate `findmy` skill — it uses UI automation (AppleScript + vision), not CLI wrappers.

---

## Shared Prerequisites

- **macOS** with the relevant Apple apps (Notes.app, Reminders.app, Messages.app)
- Grant Automation access when prompted (System Settings → Privacy → Automation)
- Each app has its own CLI tool (install via Homebrew, see below)

---

## Apple Notes (via `memo`)

Manage Apple Notes from the terminal. Notes sync across all Apple devices via iCloud.

### Install

```bash
brew tap antoniorodr/memo && brew install antoniorodr/memo/memo
```

### When to Use

- User asks to create, view, or search Apple Notes
- Saving information to Notes.app for cross-device access
- Organizing notes into folders
- Exporting notes to Markdown/HTML

### When NOT to Use

- Obsidian vault management → use the `obsidian` skill
- Bear Notes → separate app (not supported here)
- Quick agent-only notes → use the `memory` tool instead

### Quick Reference

```bash
# View
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)

# Create
memo notes -a                     # Interactive editor
memo notes -a "Note Title"        # Quick add with title

# Edit / Delete / Move
memo notes -e                     # Interactive selection to edit
memo notes -d                     # Interactive selection to delete
memo notes -m                     # Move note to folder (interactive)

# Export
memo notes -ex                    # Export to HTML/Markdown
```

### Limitations

- Cannot edit notes containing images or attachments
- Interactive prompts require terminal access (use pty=true if needed)
- macOS only — requires Apple Notes.app

### Rules

1. Prefer Apple Notes when user wants cross-device sync (iPhone/iPad/Mac)
2. Use the `memory` tool for agent-internal notes that don't need to sync
3. Use the `obsidian` skill for Markdown-native knowledge management

---

## Apple Reminders (via `remindctl`)

Manage Apple Reminders from the terminal. Tasks sync across all Apple devices via iCloud.

### Install

```bash
brew install steipete/tap/remindctl
```

Check access: `remindctl status` / Request access: `remindctl authorize`

### When to Use

- User mentions "reminder" or "Reminders app"
- Creating personal to-dos with due dates that sync to iOS
- Managing Apple Reminders lists
- User wants tasks to appear on their iPhone/iPad

### When NOT to Use

- Scheduling agent alerts → use the cronjob tool instead
- Calendar events → use Apple Calendar or Google Calendar
- Project task management → use GitHub Issues, Notion, etc.
- If user says "remind me" but means an agent alert → clarify first

### Quick Reference

```bash
# View
remindctl                    # Today's reminders
remindctl today              # Today
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything
remindctl 2026-01-04         # Specific date

# Manage Lists
remindctl list               # List all lists
remindctl list Work           # Show specific list
remindctl list Projects --create    # Create list
remindctl list Work --delete        # Delete list

# Create
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"

# Complete / Delete
remindctl complete 1 2 3          # Complete by ID
remindctl delete 4A83 --force     # Delete by ID

# Output Formats
remindctl today --json       # JSON for scripting
remindctl today --plain      # TSV format
remindctl today --quiet      # Counts only
```

### Date Formats

Accepted by `--due` and date filters:
- `today`, `tomorrow`, `yesterday`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:mm`
- ISO 8601 (`2026-01-04T12:34:56Z`)

### Rules

1. When user says "remind me", clarify: Apple Reminders (syncs to phone) vs agent cronjob alert
2. Always confirm reminder content and due date before creating
3. Use `--json` for programmatic parsing

---

## iMessage / SMS (via `imsg`)

Read and send iMessage/SMS via macOS Messages.app.

### Install

```bash
brew install steipete/tap/imsg
```

Grant Full Disk Access for terminal (System Settings → Privacy → Full Disk Access). Grant Automation permission for Messages.app when prompted.

### When to Use

- User asks to send an iMessage or text message
- Reading iMessage conversation history
- Checking recent Messages.app chats
- Sending to phone numbers or Apple IDs

### When NOT to Use

- Telegram/Discord/Slack/WhatsApp messages → use the appropriate gateway channel
- Group chat management (adding/removing members) → not supported
- Bulk/mass messaging → always confirm with user first

### Quick Reference

```bash
# List Chats
imsg chats --limit 10 --json

# View History
imsg history --chat-id 1 --limit 20 --json
imsg history --chat-id 1 --limit 20 --attachments --json

# Send Messages
imsg send --to "+141****1212" --text "Hello!"
imsg send --to "+141****1212" --text "Check this out" --file /path/to/image.jpg
imsg send --to "+141****1212" --text "Hi" --service imessage   # Force iMessage
imsg send --to "+141****1212" --text "Hi" --service sms        # Force SMS

# Watch for New Messages
imsg watch --chat-id 1 --attachments
```

### Service Options

- `--service imessage` — Force iMessage (requires recipient has iMessage)
- `--service sms` — Force SMS (green bubble)
- `--service auto` — Let Messages.app decide (default)

### Rules

1. **Always confirm recipient and message content** before sending
2. **Never send to unknown numbers** without explicit user approval
3. **Verify file paths** exist before attaching
4. **Don't spam** — rate-limit yourself

### Example Workflow

User: "Text mom that I'll be late"

```bash
# 1. Find mom's chat
imsg chats --limit 20 --json | jq '.[] | select(.displayName | contains("Mom"))'
# 2. Confirm with user: "Found Mom at +155****3456. Send 'I'll be late' via iMessage?"
# 3. Send after confirmation
imsg send --to "+155****3456" --text "I'll be late"
```