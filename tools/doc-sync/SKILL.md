---
name: doc-sync
description: "Use this internal maintenance skill when you need to check what changed in the published Rhino Health SDK docs since the current repo snapshot, generate a structured diff report, and then curate updates into context/. Trigger on requests like 'sync SDK docs', 'what changed in the SDK docs', 'refresh the Rhino SDK references', or 'compare current repo docs to latest Rhino docs'."
argument-hint: "[optional scope or SDK version]"
metadata:
  author: rhino-health
  version: "0.2.0"
---

# Rhino SDK Internal Tool — Doc Sync

Internal maintenance skill for refreshing this repo when the published Rhino Health SDK docs change.

## Goal

Compare the latest published docs against the repo's current `context/` files, surface the exact differences, and then make curated updates without dumping raw HTML into the repo.

## Sources of Truth

Read these files before acting:

1. `context/sdk_reference.md`
2. `context/metrics_reference.md`
3. `context/patterns_and_gotchas.md`
4. `context/examples/INDEX.md`
5. `tools/doc-sync/doc_sync.py`

For historical/raw source material, consult:

6. `../RhinoSkill/reference/`
7. `../RhinoSkill/examples/from_github/`

## Script Workflow

Use the backing script first. Run from the repo root:

```bash
python3 tools/doc-sync/doc_sync.py --report
```

This will:

- fetch the published Rhino SDK docs and GitHub examples listing
- cache raw responses under `tools/doc-sync/.cache/`
- compare the scrape against the current `context/` files
- write a markdown report under `tools/doc-sync/reports/`

Useful modes:

- `--scrape` to refresh the cache only
- `--diff` to diff the cached snapshot against `context/`
- `--report` to scrape + diff + write the report
- `--apply` to perform safe metadata updates such as SDK version bumps before manual curation

## Operating Procedure

Follow this sequence every time:

1. Run `python3 tools/doc-sync/doc_sync.py --report`.
2. Read the generated report in full.
3. For each changed section, inspect the matching source:
   - published docs cache under `tools/doc-sync/.cache/`
   - current curated files under `context/`
   - Phase 1 raw reference material in `../RhinoSkill/reference/` when extra structure is needed
4. Update `context/` files manually and editorially:
   - keep existing headings and writing style
   - summarize API changes clearly
   - do not paste HTML
   - preserve import path guidance and gotchas
5. If examples changed, update:
   - `context/examples/INDEX.md`
   - the relevant files under `context/examples/`
6. Run `./scripts/sync-context.sh` after any `context/` edits.
7. If the SDK version changed, verify these files stay aligned:
   - `context/sdk_reference.md`
   - `SKILL.md`
   - any skill text that mentions a specific SDK version
8. Re-run `python3 tools/doc-sync/doc_sync.py --report` and confirm the remaining diff is understood.

## Editing Rules

- `context/` is the only source of truth to edit first
- `references/` must be refreshed via `./scripts/sync-context.sh`, not by hand
- treat `patterns_and_gotchas.md` as curated guidance, not a direct scrape target
- if the published docs add new modules but there is no clear user-facing value, note them in the report before deciding to add them

## Expected Output

When reporting back after running this skill, include:

1. the scraped SDK version
2. the changed sections/modules/metrics/examples
3. which repo files need edits
4. whether the changes are safe metadata-only or require real content curation
5. what was updated after validation
