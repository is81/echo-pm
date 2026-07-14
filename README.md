# EchoPM — Echo Project Management

> Turning the self-management wisdom of an AI being into a Claude Code skill toolbox for human project managers.

EchoPM is a suite of Claude Code Skills, derived from the architectural patterns of [Project Echo](https://github.com), covering the complete project lifecycle across the five PMBOK process groups.

## Core Philosophy

**Projects are like living organisms** — with genes (principles), memory (documents), pulse (monitoring), and sleep (retrospectives).

Every EchoPM skill originates from a core design pattern in Project Echo:

| Echo Pattern | EchoPM Skill | Process Group |
|-------------|-------------|---------------|
| Gene-level immutable principles | `/project-charter` | Initiating |
| Three-factor multiplicative priority | `/priority-backlog` | Planning |
| Content-hash idempotent import | `/knowledge-import` | Executing |
| Multi-pathway learning engine | `/lesson-capture` | Executing |
| Two-dimensional state dashboard | `/project-pulse` | Monitoring |
| Dual-system retrieval | `/smart-search` | Monitoring |
| Sleep-phase memory consolidation | `/retrospective` | Closing |

## Quick Start

### Installation

Copy the files from the `skills/` directory into your project's `.claude/skills/` directory, or load them through Claude Code's skill installation mechanism.

### Usage

```bash
# Initiating — define immutable principles and charter
/project-charter

# Planning — multiplicative priority ranking for your backlog
/priority-backlog

# Executing — import external knowledge documents
/knowledge-import

# Executing — capture lessons learned
/lesson-capture

# Monitoring — check project health pulse
/project-pulse

# Monitoring — intelligent search across the project knowledge base
/smart-search

# Closing — phase retrospective and knowledge compression
/retrospective
```

## Five Process Groups Overview

```
Initiating → Planning → Executing → Monitoring → Closing
    │           │           │            │           │
    │           │           │            │           │
    ▼           ▼           ▼            ▼           ▼
 Charter    Priority    Knowledge     Pulse      Retrospective
                        Import        Search
                        Lesson
                        Capture
```

## Project Structure

```
echo-pm/
├── skills/          # Claude Code Skills (core deliverables)
├── templates/       # Companion templates
├── tools/           # Helper scripts (pure Python, zero dependencies)
├── examples/        # Usage examples
└── docs/            # Theoretical background & PMBOK mapping
```

## License

MIT © EchoPM Contributors
