# Changelog

All notable changes to the second-brain-clipping-processor skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- Clippings are Inbox rows (Kind=Clipping, Source URL) and are filed as Notes rows
- 04-Resources/<slug>.md destinations replaced by standalone Notes rows (Option A) or Notes rows
  related to a Project/Area (Option B)
- Frontmatter templates replaced by the Notion property set
- Duplicate detection queries the Notes data source and compares Source URL values
- vault-conventions-check.md replaced by notion-conventions-check.md
- SKILL.md - Rewrite for the Notion API
