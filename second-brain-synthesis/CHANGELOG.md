# Changelog

All notable changes to the second-brain-synthesis skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- 3-layer retrieval becomes property query -> global search -> page body read
- Wiki-link citations replaced by <mention-page> mentions plus a Sources list with page ids
- Confidential guard reads the Confidential checkbox instead of frontmatter tags
- Gap analysis, query routing and anti-patterns kept
- SKILL.md - Rewrite for the Notion API
