# CLAUDE.md — EchoPM Project Guide

## Project Overview

EchoPM (Echo Project Management) is a suite of Claude Code Skills that abstracts Project Echo's design patterns into project management tools covering all five PMBOK process groups. Core philosophy: projects are like living organisms — with genes, memory, pulse, and sleep.

## Project Structure

```
echo-pm/
├── skills/          # Claude Code Skills (core deliverables, 7 .md files)
├── templates/       # Companion templates (charter template, principles YAML, dashboard, etc.)
├── tools/           # Helper Python scripts (zero external dependencies)
├── examples/        # Usage examples (dogfooding records + sample projects)
└── docs/            # Theoretical docs (pattern details + PMBOK mapping + FAQ)
```

## Skill Development Standards

Every skill file must include the following sections:
1. **Trigger Conditions**: When to auto-activate
2. **PMBOK Alignment**: Mapped process numbers and names
3. **Echo Origins**: Specific Project Echo patterns and source files referenced
4. **Workflow**: Step-by-step concrete operations
5. **Deliverables**: Files generated after the skill runs
6. **Examples**: At least one usage scenario

## Key Constraints

- Skill core functionality has zero external dependencies (uses only Claude Code built-in capabilities)
- Helper scripts under `tools/` may introduce dependencies, but must document them in the file header comments
- Every skill must reference Project Echo source files as its pattern origin
- EchoPM manages its own development using EchoPM skills (dogfooding)

## Common Commands

```bash
# Verify all skill files have complete structure
grep -l "^## " skills/*.md

# Check PMBOK coverage
python tools/check_coverage.py
```

## Related Projects

- Project Echo: `F:\Project Echo` — The pattern source
- All patterns in this project are extracted from Echo's following files:
  - `src/echo/memory/models.py` — Three-factor priority formula
  - `src/echo/agent/core.py` — Sleep maintenance + dual-system retrieval
  - `src/echo/memory/store.py` — Idempotent import pipeline
  - `config/principles.yaml` — Immutable principles
  - `src/echo/zim_ingest.py` — Multi-strategy import pipeline
