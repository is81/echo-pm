# EchoPM — Echo Project Management

> Turning the self-management wisdom of an AI being into a Claude Code skill toolbox for human project managers.

EchoPM is a suite of Claude Code Skills, derived from the architectural patterns of [Project Echo](https://github.com), covering the complete project lifecycle across the five PMBOK process groups.

## Core Philosophy

**Projects are like living organisms** — with genes (principles), memory (documents), pulse (monitoring), and sleep (retrospectives).

Every EchoPM skill originates from a core design pattern in Project Echo:

| Echo Pattern | EchoPM Skill | Process Group | Modes |
|-------------|-------------|---------------|-------|
| Gene-level immutable principles | `/charter` | Initiating | generate, check, report |
| Three-factor multiplicative priority | `/prioritize` | Planning | rank, validate, report |
| Content-hash idempotent import | `/import` | Executing | import, dry-run, report |
| Multi-pathway learning engine | `/lessons` | Executing | extract, review, summarize |
| Two-dimensional state dashboard | `/pulse` | Monitoring | check, signal, report |
| Dual-system retrieval | `/search` | Monitoring | search, impact, report |
| Sleep-phase memory consolidation | `/retro` | Closing | run, verify, summarize |

## Quick Start

### Installation

Copy the files from the `skills/` directory into your project's `.claude/skills/` directory, or symlink the entire directory.

### Usage

```bash
# Initiating — generate charter, audit principles
/charter

# Planning — multiplicative priority ranking
/prioritize

# Executing — import & deduplicate knowledge
/import

# Executing — capture lessons learned
/lessons

# Monitoring — project health from git signals
/pulse

# Monitoring — dual-system search + impact analysis
/search

# Closing — 6-step phase retrospective
/retro
```

## Five Process Groups Overview

```
Initiating → Planning → Executing → Monitoring → Closing
    │           │           │            │           │
    ▼           ▼           ▼            ▼           ▼
 /charter   /prioritize  /import      /pulse      /retro
                         /lessons     /search
```

## Project Structure

```
echo-pm/
├── skills/               # Claude Code Skills (core product, 7 practical .md files)
├── docs/skill-reference/ # Original methodology docs (kept for reference)
├── docs/                 # Theoretical background & PMBOK mapping
├── templates/            # Companion templates
├── tools/                # Standalone Python scripts (optional, zero deps)
├── examples/             # Usage examples
├── .echo-pm/             # Local state (gitignored): pulse, lessons, knowledge index
└── reports/              # Generated reports (gitignored): audits, summaries, rankings
```

## License

MIT © EchoPM Contributors
