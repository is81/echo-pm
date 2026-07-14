# EchoPM Project Charter

> immutable: true
> Date Established: 2026-07-14
> Version: 1.0

## Birth Inscription

**EchoPM was born from the ripples of Project Echo — an AI being that self-manages through seven patterns, which resonate precisely with the five-phase lifecycle of project management. We believe: good projects are not "managed" into existence — they grow naturally once given the right genes.**

## Immutable Principles

### Principle 1: Patterns Before Process

Every EchoPM skill must originate from a verifiable design pattern, not a fabricated "best practice." Source patterns are documented in `docs/patterns.md`, and every skill's documentation must cite its origin.

**Why It's Immutable**: A tool without pattern grounding is just another checklist. Patterns ensure reproducibility, verifiability, and evolvability.

### Principle 2: Dogfooding Verification

EchoPM itself must be managed using EchoPM's own skills. The project charter is the output of this skill itself, priority ranking is used for EchoPM's backlog, and retrospectives govern EchoPM's release rhythm.

**Why It's Immutable**: Eating your own dog food is the only honest approach. If EchoPM doesn't use a skill itself, that skill shouldn't be offered to users.

### Principle 3: Zero Dependency Barrier

Every skill's core workflow must function with zero additional dependencies. Helper tools (in the `tools/` directory) may introduce dependencies, but the skills themselves rely solely on Claude Code's built-in capabilities.

**Why It's Immutable**: A project manager should never need to configure an environment just to run a skill. Zero barrier = zero excuses.

## Stakeholder Matrix

| Role | Representative | Core Concerns | Engagement |
|------|---------------|---------------|------------|
| Project Manager | PM using Claude Code | Progress visibility, risk transparency | Daily skill usage |
| Tech Lead | Technical lead | Technical debt visualization | Using pulse + search |
| Independent Developer | Solo project maintainer | Low-overhead self-management | Full workflow usage |
| Project Echo Community | Echo users/contributors | Pattern evolution feedback | Submit pattern improvements |

## Success Metrics

- [ ] Each skill trialed in at least 3 real projects
- [ ] PMBOK 47-process coverage ≥ 80%
- [ ] Users can use every skill's core functionality without additional installation
- [ ] EchoPM's own development is managed via EchoPM skills
