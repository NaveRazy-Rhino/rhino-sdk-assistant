# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Internal `tools/doc-sync/` maintenance workflow with `doc_sync.py`, report output, and an operator skill for refreshing SDK docs against the published Rhino documentation site
- Internal `tools/feedback-loop/` maintenance workflow with a feedback-processing skill, JSON schema, inbox, and append-only feedback log scaffold
- Experimental bundled plugin MCP configs for all Rhino environments via `mcp.json` and `.mcp.json`, with every server entry marked `disabled: true` for install-flow testing

## [0.2.0] - 2026-03-31

### Added

- Cursor plugin support via `.cursor-plugin/plugin.json`
- Cursor hook config in `hooks/hooks-cursor.json`
- Unified `rhino-sdk` repo layout that ships Claude Code plugin, Cursor plugin, and Agent Skills from one codebase
- Shared `agents/sdk-reviewer.md` agent for Claude Code and Cursor

### Changed

- Merged the former `rhino-sdk-plugin` and `rhino-sdk-skills` repos into a single repository
- Rebased the root portable skill on the merged repo root as `SKILL.md`
- Renamed granular skills to short names: `guide`, `write`, `plan`, `debug`, `metrics`, `harmonize`, `example`
- Updated granular skills to load shared references through per-skill `references` symlinks
- Updated repository metadata to point to `NaveRazy-Rhino/rhino-sdk-assistant`
- Updated `scripts/sync-context.sh` to sync `context/` into the root `references/` bundle

### Removed

- Duplicate validator script copy under the former self-contained skill directory
- Separate plugin-vs-skills repo split

## [0.1.0] - 2026-03-11

### Added

- 7 skills: guide, write, plan, debug, metrics, harmonize, example
- sdk-reviewer agent for automatic code review of `rhino_health` imports and patterns
- validate-imports hook for catching wrong import paths on file save
- Context files: sdk_reference.md (648 lines), patterns_and_gotchas.md (610 lines), metrics_reference.md (427 lines)
- 11 annotated working examples from official Rhino Health GitHub repository
