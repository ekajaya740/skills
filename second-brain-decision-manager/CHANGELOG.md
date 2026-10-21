# Changelog

All notable changes to the second-brain-decision-manager skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- 05-Decisions/ folder replaced by the Decisions data source
- The Decision.md checkbox index replaced by a saved view (POST /v1/views)
- Superseding uses the Supersedes relation plus a body mention - there is no superseded_by property
- The decision template is now the page body written as enhanced markdown
- SKILL.md - Rewrite for the Notion API
