# Changelog

All notable changes to the second-brain-daily-note-curation skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- 01-Daily-Notes/ folder replaced by the Daily Notes data source
- Summary notes become Notes rows with a Project/Area relation and a Source relation
- Decisions become Decisions rows; the Decision.md index becomes a saved view
- Archiving creates an Archive row instead of mv into 07-Archive/01-Daily-Notes/
- Git commit and push steps removed - Notion holds the content
- SKILL.md - Rewrite for the Notion API
