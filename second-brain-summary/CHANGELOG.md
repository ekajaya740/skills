# Changelog

All notable changes to the second-brain-summary skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- Retrieval via data-source queries and Notion search replaces grep over markdown files
- Confidential guard reads the Confidential checkbox instead of frontmatter tags
- The #type/task prefix is replaced by Task rows in the Tasks data source
- SKILL.md - Rewrite for the Notion API
