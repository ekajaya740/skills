# Changelog

All notable changes to the second-brain-cross-linker skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- Orphan and weak-connection detection now query the Notes data source and count relations
- [[wikilinks]] replaced by the Related relation property plus optional <mention-page> mentions
- Relations are set on one side only - Notion mirrors them
- SKILL.md - Rewrite for the Notion API
