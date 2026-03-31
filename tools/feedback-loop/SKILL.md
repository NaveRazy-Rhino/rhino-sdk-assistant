---
name: feedback-loop
description: "Use this internal maintenance skill when feedback comes in about the Rhino SDK skills, examples, hook behavior, or generated code quality. It ingests feedback from chat, GitHub issues, or local files, traces the likely root cause in the repo, validates the complaint against the SDK docs and repo behavior, and proposes or applies targeted fixes."
argument-hint: "[feedback text, issue URL/number, or inbox filename]"
metadata:
  author: rhino-health
  version: "0.2.0"
---

# Rhino SDK Internal Tool — Feedback Loop

Internal maintenance skill for turning feedback into validated repo improvements.

## Goal

Take incoming feedback, understand what actually went wrong, verify it against the repo and current SDK docs, and make the smallest high-value change that improves the skill pack.

## Accepted Inputs

This skill supports three entry paths:

1. **Chat feedback**
   The user pastes the complaint directly in the conversation.

2. **GitHub issue**
   The user gives an issue URL or issue number for this repo.

3. **Local inbox file**
   Feedback is stored under `tools/feedback-loop/inbox/`.

## Files to Read First

Always read:

1. `tools/feedback-loop/feedback_schema.json`
2. `tools/feedback-loop/feedback_log.jsonl`
3. `README.md`
4. `SKILL.md`

Then read the most relevant implementation files based on the feedback category:

- `context/sdk_reference.md`
- `context/patterns_and_gotchas.md`
- `context/metrics_reference.md`
- `skills/*/SKILL.md`
- `agents/sdk-reviewer.md`
- `hooks/validate_sdk_imports.py`
- `context/examples/INDEX.md`
- `context/examples/*.py`
- `tools/doc-sync/doc_sync.py` if the complaint may be caused by stale docs

## Intake Workflow

### 1. Normalize the feedback

Convert the raw input into the schema in `feedback_schema.json`.

- For chat feedback: extract the structured fields yourself
- For GitHub issues: use `gh issue view <number or url>` and normalize the result
- For inbox files: read the file and normalize it

If critical fields are missing, infer what you can and mark the rest as unknown rather than blocking.

### 2. Categorize it

Use one category:

- `wrong_output`
- `missing_knowledge`
- `bad_pattern`
- `skill_ux`
- `hook_false_positive`
- `other`

## Investigation Workflow

### 3. Reproduce or verify

Do not trust the complaint blindly.

- If the feedback is about generated SDK code, compare the complaint against:
  - `context/sdk_reference.md`
  - `context/patterns_and_gotchas.md`
  - matching examples under `context/examples/`
- If it is about hook behavior, inspect and test `hooks/validate_sdk_imports.py`
- If it is about stale knowledge, run:

```bash
python3 tools/doc-sync/doc_sync.py --report
```

and check whether the published docs changed

### 4. Trace the root cause

Identify the exact file and section that caused the bad outcome.

Common mappings:

- stale API or enum knowledge -> `context/sdk_reference.md`
- wrong recommended workflow -> `context/patterns_and_gotchas.md`
- wrong metric guidance -> `context/metrics_reference.md`
- poor prompting/routing -> `SKILL.md` or `skills/*/SKILL.md`
- false validator warning -> `hooks/validate_sdk_imports.py`
- weak review behavior -> `agents/sdk-reviewer.md`
- mismatch between docs and examples -> `context/examples/`

### 5. Choose the fix

Prefer the narrowest fix that removes the failure mode:

- update a context section
- tighten or expand a skill instruction
- add a warning or gotcha
- add or update an example
- adjust the validator regex/logic
- improve routing between doc-sync and feedback-loop

## Validation Rules

Before applying a fix:

1. confirm the complaint is real or partially real
2. verify the proposed fix against current SDK docs or examples
3. check for likely regressions in nearby flows
4. if you changed `context/`, run `./scripts/sync-context.sh`
5. log the result in `tools/feedback-loop/feedback_log.jsonl`

## Logging Format

Append one JSON object per processed item with:

- timestamp
- source
- category
- short description
- root cause
- fix summary
- files changed
- verification summary

Keep the log concise and append-only.

## Response Format

When reporting back after using this skill, structure the result as:

1. **Feedback summary** — what the user reported
2. **Validation** — whether the complaint was confirmed
3. **Root cause** — exact repo file/section responsible
4. **Fix plan or fix applied** — what changed or should change
5. **Verification** — how you tested or cross-checked it
6. **Log entry** — confirm whether it was appended to `feedback_log.jsonl`
