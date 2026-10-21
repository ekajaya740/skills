# Changelog

All notable changes to the email-to-vault-resource skill are documented here.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version in this file matches the version field in SKILL.md.

## [3.0.0] - 2026-10-21

Second-brain migration: the contract skill and the Notion API replace the old token path and the
`ntn` CLI.

### Changed

- Token now comes from NOTION_API_KEY in the workspace .env (or an exported env var); the old
  $HOME/.hermes/.env path is gone
- Notion-Version bumped to 2026-03-11
- The data-source id cache moved to $WORKSPACE/migration/ledger/notion_db_ids.json
- `ntn pages create/update/get` replaced by curl against POST /v1/pages, PATCH
  /v1/pages/{id}/markdown and GET /v1/pages/{id}
- The page body is written in the same request as the properties (markdown body param)
- Related skill: notion-second-brain (the contract)

## [2.0.0] - 2026-07-09

Notion-aware rewrite: outputs became Notion Notes rows instead of vault files.

### Added

- SKILL.md - Notion-native email-to-resource flow
