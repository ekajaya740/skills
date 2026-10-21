# Changelog

All notable changes to the second-brain-inbox-curation skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- 00-Inbox/ folder replaced by the Inbox data source (Status=Untriaged)
- PARA destinations are now data sources: Projects, Areas, Notes, Decisions, Archive
- "Move" becomes create-destination + set Inbox Status (Notion has no move endpoint)
- Frontmatter rules replaced by the Notion property set; the Decision.md index is a saved view
- Git commit/push removed - Notion holds the content
- SKILL.md - Rewrite for the Notion API
