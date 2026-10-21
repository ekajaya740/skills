# Changelog

All notable changes to the second-brain-weekly-review skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- Weekly content is gathered with data-source queries instead of find/grep over files
- The review is saved as a Daily Notes row named <MONDAY>-<SUNDAY>-weekly-review
- The git commit/push step is gone - Notion holds the content
- The Obsidian Tasks dashboard is replaced by saved views (references/tasks-dashboard.md)
- The #type/task prefix is replaced by Task rows in the Tasks data source
- SKILL.md - Rewrite for the Notion API
