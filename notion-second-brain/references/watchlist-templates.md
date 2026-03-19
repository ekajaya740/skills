# Watchlist Template Guide

This guide provides templates for tracking anime, films, and movies in your Notion second brain, with automated metadata enrichment from web sources.

## Table of Contents

1. [Overview](#overview)
2. [Anime Watchlist Database](#anime-watchlist-database)
3. [Film & Movie Database](#film--movie-database)
4. [Example: Dr. Stone (ドクターストーン)](#example-dr-stone-ドクターストーン)
5. [Automated Metadata Lookup](#automated-metadata-lookup)
6. [Template Setup Instructions](#template-setup-instructions)

---

## Overview

Track your media consumption with rich metadata including episode counts, seasons, release dates, and watch progress. Link entries to your projects, notes, and knowledge base.

---

## Anime Watchlist Database

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Title (Japanese) | title | Original Japanese title |
| Title (English) | rich_text | English/localized title |
| Status | select | Plan to Watch, Watching, Completed, On Hold, Dropped |
| Format | select | TV, Movie, OVA, ONA, Special |
| Seasons | number | Number of seasons |
| Total Episodes | number | Total episode count |
| Episodes Watched | number | Your progress |
| Progress % | formula | `prop("Episodes Watched") / prop("Total Episodes") * 100` |
| Score | select | 1-10 rating |
| Genres | multi_select | Action, Adventure, Comedy, etc. |
| Studio | rich_text | Animation studio |
| Source | select | Manga, Light Novel, Original, etc. |
| Aired | date | Release date range |
| Related Notes | relation | Links to Notes database |
| Cover Image | files | Poster/cover image |

### Notion DDL

```sql
CREATE TABLE "Anime Watchlist" (
  "Title (Japanese)" TITLE,
  "Title (English)" RICH_TEXT,
  "Status" SELECT('Plan to Watch', 'Watching', 'Completed', 'On Hold', 'Dropped'),
  "Format" SELECT('TV', 'Movie', 'OVA', 'ONA', 'Special'),
  "Seasons" NUMBER,
  "Total Episodes" NUMBER,
  "Episodes Watched" NUMBER,
  "Progress %" FORMULA('prop("Episodes Watched") / prop("Total Episodes") * 100'),
  "Score" SELECT('10 - Masterpiece', '9 - Great', '8 - Very Good', '7 - Good', '6 - Fine', '5 - Average', '4 - Bad', '3 - Very Bad', '2 - Horrible', '1 - Appalling'),
  "Genres" MULTI_SELECT('Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Sci-Fi', 'Slice of Life', 'Romance', 'Thriller', 'Mystery'),
  "Studio" RICH_TEXT,
  "Source" SELECT('Manga', 'Light Novel', 'Visual Novel', 'Original', 'Game', 'Other'),
  "Aired" DATE,
  "Related Notes" RELATION('notes-database-id'),
  "Cover Image" FILES
)
```

---

## Film & Movie Database

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Title | title | Movie title |
| Original Title | rich_text | Original language title |
| Status | select | Plan to Watch, Watching, Completed, Dropped |
| Type | select | Movie, Documentary, Short Film |
| Runtime | number | Duration in minutes |
| Minutes Watched | number | Your progress |
| Progress % | formula | `prop("Minutes Watched") / prop("Runtime") * 100` |
| Release Year | number | Year of release |
| Director | rich_text | Film director(s) |
| Cast | rich_text | Main actors |
| Genres | multi_select | Drama, Comedy, Action, etc. |
| Score | select | 1-10 rating |
| Platform | multi_select | Netflix, Crunchyroll, Theater, etc. |
| Related Notes | relation | Links to Notes database |
| Poster | files | Movie poster image |

### Notion DDL

```sql
CREATE TABLE "Film & Movie Watchlist" (
  "Title" TITLE,
  "Original Title" RICH_TEXT,
  "Status" SELECT('Plan to Watch', 'Watching', 'Completed', 'Dropped'),
  "Type" SELECT('Movie', 'Documentary', 'Short Film'),
  "Runtime" NUMBER,
  "Minutes Watched" NUMBER,
  "Progress %" FORMULA('prop("Minutes Watched") / prop("Runtime") * 100'),
  "Release Year" NUMBER,
  "Director" RICH_TEXT,
  "Cast" RICH_TEXT,
  "Genres" MULTI_SELECT('Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller'),
  "Score" SELECT('10 - Masterpiece', '9 - Great', '8 - Very Good', '7 - Good', '6 - Fine', '5 - Average', '4 - Bad', '3 - Very Bad', '2 - Horrible', '1 - Appalling'),
  "Platform" MULTI_SELECT('Netflix', 'Crunchyroll', 'Amazon Prime', 'Disney+', 'Hulu', 'HBO Max', 'Theater', 'Blu-ray/DVD', 'Other'),
  "Related Notes" RELATION('notes-database-id'),
  "Poster" FILES
)
```

---

## Example: Dr. Stone (ドクターストーン)

### Anime Information (Auto-Lookup Results)

**Japanese Title:** ドクターストーン  
**English Title:** Dr. Stone  
**Format:** TV Series  
**Total Seasons:** 4 (as of 2025)  
**Total Episodes:** 61+ episodes (ongoing)

#### Season Breakdown

| Season | Title | Episodes | Aired |
|--------|-------|----------|-------|
| Season 1 | Dr. Stone | 24 | Jul 5 - Dec 13, 2019 |
| Season 2 | Dr. Stone: Stone Wars | 11 | Jan 14 - Mar 25, 2021 |
| Special | Dr. Stone: Ryusui | 1 | Jul 10, 2022 |
| Season 3 | Dr. Stone: New World | 22 | Apr 6 - Dec 21, 2023 |
| Season 4 | Dr. Stone: Science Future | 3+ cours | Jan 2025 - ongoing |

**Studio:** TMS Entertainment  
**Source:** Manga (27 volumes)  
**Genres:** Adventure, Comedy, Sci-Fi, Shounen  
**Duration:** 24 min per episode  

### Notion Entry Example

```json
{
  "Title (Japanese)": "ドクターストーン",
  "Title (English)": "Dr. Stone",
  "Status": "Watching",
  "Format": "TV",
  "Seasons": 4,
  "Total Episodes": 61,
  "Episodes Watched": 24,
  "Progress %": 39.3,
  "Score": "8 - Very Good",
  "Genres": ["Adventure", "Comedy", "Sci-Fi", "Shounen"],
  "Studio": "TMS Entertainment",
  "Source": "Manga",
  "Aired": "2019-07-05 to 2025-ongoing"
}
```

---

## Automated Metadata Lookup

When adding a new anime or film entry, the agent should:

### Step 1: Search for Metadata

Use web search to find:
- Official title (Japanese and English)
- Episode count / runtime
- Number of seasons
- Studio/production company
- Genres
- Release dates
- Source material

### Step 2: Create Database Entry

Populate the Notion database with discovered metadata:

```json
{
  "query": "Dr. Stone anime episodes seasons count",
  "numResults": 3
}
```

### Step 3: Link to Related Content

After creating the entry:
- Search for existing notes about this anime
- Link to related projects (e.g., "Anime Review Project")
- Create a note for episode tracking if needed

### Step 4: Update Progress

As you watch:
- Update "Episodes Watched" or "Minutes Watched"
- Progress % calculates automatically
- Change Status when complete

---

## Template Setup Instructions

### Creating the Anime Watchlist

1. Create a new database in Notion
2. Use the DDL above to set up properties
3. Create views:
   - **All Anime** (table view)
   - **Currently Watching** (filter: Status = Watching)
   - **Completed** (filter: Status = Completed)
   - **Plan to Watch** (filter: Status = Plan to Watch)
   - **By Genre** (board view, group by Genres)
   - **By Score** (gallery view, sort by Score)

### Creating the Film Database

1. Create a new database in Notion
2. Use the DDL above to set up properties
3. Create views:
   - **All Films** (table view)
   - **Watchlist** (filter: Status = Plan to Watch)
   - **Watched** (filter: Status = Completed)
   - **By Genre** (board view)
   - **By Year** (calendar view, by Release Year)

### Integration with Second Brain

Link watchlist entries to:
- **Projects:** "Anime Review Blog", "Film Analysis Project"
- **Notes:** Episode reviews, character analysis, theories
- **Knowledge:** Scientific concepts from Dr. Stone, historical references
- **Areas:** Entertainment, Learning, Hobbies

---

## Quick Reference: Common Anime Metadata Sources

| Source | URL | Best For |
|--------|-----|----------|
| MyAnimeList | myanimelist.net | Episode counts, scores, genres |
| AniDB | anidb.net | Detailed episode lists |
| Wikipedia | wikipedia.org | Season information, air dates |
| Fandom Wiki | fandom.com | Character info, plot summaries |
| Crunchyroll | crunchyroll.com | Streaming availability |

---

## Related Files

- [database-patterns.md](database-patterns.md) - General database schemas
- [action-templates.md](action-templates.md) - How to add and update entries
- [linking-strategy.md](linking-strategy.md) - Connect watchlist to other content
