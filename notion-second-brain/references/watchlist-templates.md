# Watchlist/Readlist Template Guide

This guide explains how to track anime, comics (manga/webtoons), books, and media series in your Notion second brain using the unified Notes/Areas/Topics structure.

## Core Concept

The user's Notion second brain uses a **unified structure**:
- **Notes** - Individual entries (anime episodes, comics, books, articles)
- **Areas** - Broad categories (Anime, Comic, Language, Programming)
- **Topics** - Tags/subjects (nano-machine, fitness, japanese)
- **Projects** - Work container with tasks

Media series like anime/comics should be tracked as **Notes** with appropriate Area relations. **Topics are optional — only add if the user explicitly mentions a topic or tag.**

## Area Classification

| Content Type | Where it goes | Area ID |
|--------------|---------------|---------|
| Anime (TV series, OVA, ONA) | Notes + **Anime** Area | `3284c337-6067-8132-a673-c014bf8ddba6` |
| Manga/Webtoons/Comics | Notes + **Comic** Area | `3374c337-6067-81aa-939f-d127aa20bea8` |
| Films/Movies | Notes + possibly Resources | - |
| Books | Notes + appropriate Area | - |
| TV Series | Notes + appropriate Area | - |
| Article/Video | Resources or Notes | - |

## Adding a New Media Entry

### Step 1: Create Note Entry

Create the note in the Notes database with the correct Area and icon (from Notes Template):

```bash
ntn api v1/pages -d '{
  "parent": {"database_id": "4de4c337606782d4b9e381a96e9d5384"},
  "icon": {"type": "icon", "icon": {"color": "gray", "name": "document"}},
  "properties": {
    "Name": {"title": [{"text": {"content": "Series Title"}}]},
    "Areas": {"relation": [{"id": "AREA_ID"}]}
  }
}'
```

### Step 2: Update Area Bidirectional Link

```bash
ntn api v1/pages/AREA_ID -X PATCH -d '{
  "properties": {
    "Notes": {"relation": [{"id": "NOTE_ID"}]}
  }
}'
```

### Step 3 (Optional): Add Topic Only If User Explicitly Mentions It

```bash
# Only create a topic if user explicitly mentions a topic/tag
ntn api v1/pages -d '{
  "parent": {"database_id": "af74c3376067830f8e4401fbf30ac3ce"},
  "properties": {
    "Name": {"title": [{"text": {"content": "topic-name"}}]}
  }
}'

# Then link Note → Topic and Topic → Note bidirectionally
ntn api v1/pages/NOTE_ID -X PATCH -d '{
  "properties": {
    "Topics": {"relation": [{"id": "TOPIC_ID"}]}
  }
}'

ntn api v1/pages/TOPIC_ID -X PATCH -d '{
  "properties": {
    "Notes": {"relation": [{"id": "NOTE_ID"}]}
  }
}'
```

### Step 4: Add Page Content (See Template Below)

## Page Content Template

Based on the user's 薬屋のひとりごと (The Apothecary Diaries) entry, use this exact structure.

**IMPORTANT**: Only add Season/Volume headers if:
- User explicitly mentions multiple seasons/volumes, OR
- The series is known to have multiple seasons/volumes

If not specified, use a simple chapter/episode list without season headers.

### No Season Headers Template (Default - Use This When Not Mentioning Seasons)

When the user does NOT mention seasons/volumes, list episodes/chapters directly with NO season labels:

```
## [Title] ([Native Title]) — [English Title]

Genre: [Genre1, Genre2, Genre3]

---

- [ ] [Episode/Chapter 1 Title]
- [ ] [Episode/Chapter 2 Title]
- [x] [Episode/Chapter 3 Title] (completed items are checked)

---

### Notes

- **Status:** Use checkboxes to mark episodes/chapters as watched
- **Last Updated:** {{date}}

### Resources

- [MyAnimeList](url)
- [Official Website](url)
```

### Multi-Season/Volume Template

Use ONLY when user mentions OR series is known to have multiple seasons/volumes:

```
## [Title] ([Native Title]) — [English Title]

Genre: [Genre1, Genre2, Genre3]

---

### Season 1

- [ ] [Episode/Chapter 1 Title]
- [ ] [Episode/Chapter 2 Title]
- [x] [Episode/Chapter 3 Title] (completed items are checked)

### Season 2

- [ ] [Episode/Chapter 1 Title]
- [ ] [Episode/Chapter 2 Title]

---

### Notes

- **Status:** Use checkboxes to mark episodes/chapters as watched
- **Last Updated:** {{date}}

### Resources

- [MyAnimeList](url)
- [Official Website](url)
```

### Key Formatting Rules

1. **Title**: Japanese/English format with native script first
2. **Genre**: Listed as comma-separated paragraph after title
3. **Divider**: `---` separator after header info
4. **Season/Chapter Headers**: Only use `heading_2` if MULTIPLE seasons/volumes exist or user specifies
5. **Episode/Chapter List**: Use `to_do` blocks (checkbox unchecked = not watched, checked = completed)
6. **Notes Section**: heading_2 with bullet points for meta info
7. **Resources Section**: heading_2 with bullet points containing links

## Manga/Webtoon Series Entry Example

For webtoons like Nano Machine (no season labels by default, no topic unless user mentions one):

```
## Nano Machine (나노 머신)

Genre: Action, Martial Arts, Sci-Fi, Fantasy

---

- [ ] Chapter 1
- [ ] Chapter 2
- [ ] Chapter 3

---

### Notes

- **Status:** Use checkboxes to mark chapters as read
- **Last Updated:** {{date}}

### Resources

- [Webtoon](url)
```

## Known Area IDs

| Area Name | Area ID | Content Type |
|-----------|---------|--------------|
| Anime アニメ | `3284c337-6067-8132-a673-c014bf8ddba6` | Anime (TV, OVA, ONA) |
| Comic | `3374c337-6067-81aa-939f-d127aa20bea8` | Manga, Webtoons, Comics |
| Language | `3254c337-6067-8173-a514-d0dad6f110b7` | Language learning |
| Programming | `3254c337-6067-819f-aba6-d0ca073d1dda` | Programming projects |

## Common Metadata Sources

| Source | URL | Best For |
|--------|-----|----------|
| MyAnimeList | myanimelist.net | Anime info, episodes |
| AniDB | anidb.net | Detailed episode lists |
| Webtoon | webtoons.com | Webtoon series |
| Wikipedia | wikipedia.org | General info |
| MangaDex | mangadex.org | Manga chapters |

## Related Files

- [database-patterns.md](database-patterns.md) - General database schemas
- [action-templates.md](action-templates.md) - How to add and update entries
- [linking-strategy.md](linking-strategy.md) - Connect entries to other content
