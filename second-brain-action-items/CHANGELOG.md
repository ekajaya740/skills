# Changelog

All notable changes to the second-brain-action-items skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- Vault path resolution and file writes replaced by the Notion API contract in notion-second-brain
- Tasks are rows in the Tasks data source; the Obsidian "#type/task" prefix is gone
- Decisions are rows in the Decisions data source
- Output format kept; task rows now carry Status, Priority, Due and a Source relation
- SKILL.md - Rewrite for the Notion API
