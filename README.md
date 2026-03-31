# Rhino SDK Skills

Unified AI tooling for the [Rhino Health](https://www.rhinohealth.com/) Python SDK (`rhino-health`).

Repository name: `rhino-sdk-skills`  
Installed plugin/skill name: `rhino-sdk`

This repo now ships through **three channels**:

- **Claude Code plugin**: granular skills + `sdk-reviewer` agent + import validation hook
- **Cursor plugin**: granular skills + `sdk-reviewer` agent + import validation hook
- **Agent Skills repo**: portable install via `npx skills add` for Cursor, Codex, Gemini CLI, GitHub Copilot, Windsurf, and more

## What You Get

- **Workflow planning**: phased SDK execution plans for federated analytics, code objects, harmonization, SQL ingestion, and multi-pipeline workflows
- **Code generation**: production-ready Python with validation against common Rhino SDK pitfalls
- **Metric selection**: 40+ federated metrics including `KaplanMeier`, `Cox`, `TTest`, `ChiSquare`, `RocAuc`, and epidemiology metrics
- **Data harmonization**: OMOP, FHIR, and custom target-model guidance
- **Error diagnosis**: SDK-specific error-to-fix mapping
- **Working examples**: 11 verified examples from the official Rhino Health examples repo
- **SDK review agent**: `sdk-reviewer` catches common import, nesting, and async mistakes
- **Write-time validation hook**: flags bad imports and plaintext passwords in edited Python files

## Install

### Claude Code

For the full Claude Code experience:

```bash
claude plugin install NaveRazy-Rhino/rhino-sdk-skills
```

This gives you:

- 7 granular plugin skills
- `sdk-reviewer` agent
- import-validation hook on file writes

### Cursor

For the full Cursor experience, install it as a Cursor plugin.

**Local development install:**

```bash
ln -s /absolute/path/to/rhino-sdk-skills ~/.cursor/plugins/local/rhino-sdk
```

Then reload Cursor.

**Marketplace install:** use the Cursor Marketplace once the plugin is published there.

This gives you:

- 7 granular plugin skills
- `sdk-reviewer` agent
- import-validation hook on file edits

### Any Agent via `npx skills add`

For the portable Agent Skills install:

```bash
npx skills add NaveRazy-Rhino/rhino-sdk-skills
```

Recommended: select the top-level **`rhino-sdk`** skill for the self-contained all-in-one experience.

You can also target a specific agent:

```bash
npx skills add NaveRazy-Rhino/rhino-sdk-skills -a cursor
npx skills add NaveRazy-Rhino/rhino-sdk-skills -a codex
npx skills add NaveRazy-Rhino/rhino-sdk-skills -a gemini-cli
npx skills add NaveRazy-Rhino/rhino-sdk-skills -a github-copilot
```

## Skills

| Skill | Purpose |
|-------|---------|
| `rhino-sdk` | Self-contained all-in-one planner, code generator, debugger, and SDK guide |
| `guide` | SDK API questions and concept explanations |
| `write` | Single-script code generation with validation |
| `plan` | Multi-step workflow decomposition and planning |
| `debug` | SDK error diagnosis and fix suggestions |
| `metrics` | Federated metric selection and configuration |
| `harmonize` | Data harmonization pipeline guidance |
| `example` | Find and present working SDK examples |

## Repository Layout

```text
rhino-sdk-skills/
├── .claude-plugin/            # Claude Code manifest + marketplace metadata
├── .cursor-plugin/            # Cursor plugin manifest
├── SKILL.md                   # Self-contained all-in-one skill for npx installs
├── references/                # Bundled copy used by the root skill
├── skills/                    # 7 granular skills shared by Claude + Cursor + npx
├── agents/                    # Shared sdk-reviewer agent
├── hooks/                     # Claude + Cursor hook configs + shared validator script
├── context/                   # Source of truth for docs/examples
└── scripts/sync-context.sh    # Sync context/ -> references/
```

## Path Strategy

- The top-level `SKILL.md` is **self-contained** and always reads from `references/`
- The granular skills use `references -> ../../context` symlinks so Claude Code and Cursor can share the same source-of-truth files without duplicating them in every skill directory
- `context/` is the editable source of truth
- `references/` is the bundled copy for the portable root skill

## Development

After updating files in `context/`, refresh the self-contained root skill bundle:

```bash
./scripts/sync-context.sh
```

## Internal Tools

This repo now includes two internal maintenance tools under `tools/` for keeping the skill pack accurate over time.

### `tools/doc-sync/`

Use this when you want to compare the repo's current Rhino SDK knowledge against the latest published SDK docs and examples.

Main entrypoint:

```bash
python3 tools/doc-sync/doc_sync.py --report
```

Key outputs:

- raw scrape cache under `tools/doc-sync/.cache/`
- markdown diff reports under `tools/doc-sync/reports/`
- safe metadata-only updates via `--apply`

Human workflow:

1. Run `python3 tools/doc-sync/doc_sync.py --report`
2. Review the generated report
3. Curate updates into `context/`
4. Run `./scripts/sync-context.sh`

The AI-facing wrapper lives in `tools/doc-sync/SKILL.md`.

### `tools/feedback-loop/`

Use this when you get feedback about generated code quality, missing SDK knowledge, bad patterns, hook false positives, or weak skill UX.

Supported input sources:

- pasted chat feedback
- GitHub issues
- dropped files under `tools/feedback-loop/inbox/`

Key files:

- `tools/feedback-loop/SKILL.md`
- `tools/feedback-loop/feedback_schema.json`
- `tools/feedback-loop/feedback_log.jsonl`

Human workflow:

1. Normalize the feedback into the schema
2. Validate whether the complaint is real
3. Trace the root cause to `context/`, `skills/`, `hooks/`, or `agents/`
4. Apply the narrowest useful fix
5. Append the resolution to `tools/feedback-loop/feedback_log.jsonl`

## Compatibility Notes

- **Claude Code** and **Cursor** get the full plugin experience: skills + agent + hook
- **Other tools** get the skills via the Agent Skills standard
- The base Agent Skills spec does not ship agents or hooks, so those remain plugin-only features
- The public repo is named `rhino-sdk-skills` to avoid confusion with the actual Rhino Python SDK, but the installed plugin/skill namespace remains `rhino-sdk`

## License

MIT
