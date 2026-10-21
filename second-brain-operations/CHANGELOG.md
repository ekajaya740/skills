# Changelog

All notable changes to the second-brain-operations skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [1.0.0] - 2026-10-21

Notion migration: this skill now drives the Notion API instead of the local Obsidian vault.

### Changed

- The PARA folder tree is replaced by the nine Notion data sources
- The Obsidian Tasks plugin dashboard is replaced by saved views over the Tasks data source
- Search is now data-source queries and Notion search - no index, no reindex
- The vault git workflow is replaced by "no commit for second-brain content" (the skills repo is
  still versioned)
- The skill table now includes the twelve Notion-driven skills plus notion-second-brain
- SKILL.md - Rewrite for the Notion API
