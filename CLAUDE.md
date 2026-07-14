# CLAUDE.md — EchoPM Project Guide

## Project Overview

EchoPM (Echo Project Management) is a suite of Claude Code Skills that abstracts Project Echo's design patterns into practical project management tools covering all five PMBOK process groups. Core philosophy: projects are like living organisms — with genes, memory, pulse, and sleep.

## Project Structure

```
echo-pm/
├── skills/               # Claude Code Skills — the core product (7 practical .md files)
├── docs/skill-reference/ # Original methodology docs (patterns, PMBOK alignment, kept for reference)
├── docs/                 # Theoretical docs (pattern details + PMBOK mapping + FAQ)
├── templates/            # Companion templates (charter template, principles YAML, dashboard, etc.)
├── tools/                # Standalone Python scripts (optional, zero external dependencies)
├── examples/             # Usage examples (dogfooding records + sample projects)
├── .echo-pm/             # Local state (gitignored) — pulse, lessons, knowledge index
└── reports/              # Generated reports (gitignored) — audits, summaries, rankings
```

## Active Skills (`skills/`)

To install: copy `skills/` into your project's `.claude/skills/` directory, or symlink it.

Each skill has 2-3 modes: generate/check/report. They do real work — read files, compute results, write reports.

| Skill | Purpose | Key Modes |
|-------|---------|-----------|
| `/charter` | Project charter generation & validation | generate, check, report |
| `/import` | Knowledge base import & dedup | import, dry-run, report |
| `/search` | Dual-system knowledge search & impact analysis | search, impact, report |
| `/lessons` | Lesson capture, audit & summarization | extract, review, summarize |
| `/pulse` | Project health monitoring via git signals | check, signal, report |
| `/prioritize` | Multiplicative backlog priority ranking | rank, validate, report |
| `/retro` | Phase retrospective with 6-step process | run, verify, summarize |

## Skill Design Principles

1. **Every skill has multiple modes** — generate (create), check (validate), report (summarize)
2. **Skills describe what the AI does**, not what the user should do
3. **Zero external dependencies** — all modes use Claude Code built-in tools (Glob, Grep, Read, Write, Bash)
4. **Data stored in `.echo-pm/`** — simple JSON files (gitignored), no databases
5. **Every mode follows "read → compute → write"** — concrete inputs, concrete outputs
6. **Graceful degradation** — any step that fails is handled independently, never blocks the rest

## Common Commands

```bash
# Verify all skill files exist
ls .claude/skills/

# Check PMBOK coverage (from reference docs)
cat docs/pmbok-mapping.md

# View EchoPM's own pulse
cat .echo-pm/pulse-state.json 2>/dev/null || echo "No pulse data yet — run /pulse first"
```

## Related Projects

- Project Echo: `F:\Project Echo` — The pattern source
- All patterns in this project are extracted from Echo's following files:
  - `src/echo/memory/models.py` — Three-factor priority formula
  - `src/echo/agent/core.py` — Sleep maintenance + dual-system retrieval
  - `src/echo/memory/store.py` — Idempotent import pipeline
  - `config/principles.yaml` — Immutable principles
  - `src/echo/zim_ingest.py` — Multi-strategy import pipeline
