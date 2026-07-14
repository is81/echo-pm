---
name: retro
description: Run phase retrospectives — collect data, execute 6 isolated steps, produce complete report with archive.
argument-hint: "[mode:run|verify|summarize] [--scope <name>] [--since YYYY-MM-DD] [--until YYYY-MM-DD]"
---

# /retro

## Mode Detection

| User intent | Mode |
|-------------|------|
| "retro/retrospective/postmortem/sprint retro/phase close" | **run** |
| "check/verify/validate retro", "audit retrospective" | **verify** |
| "retro summary/executive summary/quick retro" | **summarize** |

Default run if `--scope`, `--since`, or `--until` provided.

## Run Mode

### Phase 0: Collect

Determine scope or ask. Create `retrospectives/YYYY-MM-DD-[scope]/`. Collect:
- `git log --since=<s> --until=<e> --format="%h %s %an %ad" --date=short`
- `git log --since=<s> --until=<e> --merges --format="%h %s %ad" --date=short`
- `git diff --stat <s>..<e>`
- Read `CHARTER.md`, `.echo-pm/pulse-state.json`, filter `.echo-pm/lessons.json` by date, Glob `reports/pulse-*.md`

Execute 6 steps independently. Each wrapped in try/catch — failure in one does not block others.

### Step 1: Anchor Review
Compare CHARTER success metrics against deliverables. Status each: NOT_STARTED/IN_PROGRESS/DONE/UNKNOWN. Analyze deviations. Write `retrospectives/[dir]/anchor-review.md`. If no CHARTER, write "skipped" and continue.

### Step 2: Pattern Crystallization
Analyze commits: ≥3 similar = pattern candidate. "revert" commits = anti-pattern. Analyze lessons: ≥3 sharing a tag = pattern candidate. LLM distill into named patterns (description, evidence, recommendation). Write `retrospectives/[dir]/patterns.md`. If <10 commits, write "insufficient data" and continue.

### Step 3: Lesson Extraction
Feed commit messages + period reports through lesson extractor (same logic as `/lessons` extract). Dedup. Append new with `source: "retrospective"`, `retro_scope: "[scope]"`. Write count to retro dir.

### Step 4: Gap Exploration
Grep `TODO|FIXME|HACK|XXX` (exclude `.git/`, `node_modules/`). Check pulse for sustained negative signals. Compare previous retro gaps. List open questions, unresolved risks. Write `retrospectives/[dir]/gaps.md`.

### Step 5: Memory Compression
Group data by week. Per week, LLM (temp 0.4) produce 3-5 sentence narrative. Merge into ≤500 words. Write `retrospectives/[dir]/narrative.md`.

### Step 6: Archive
Scan `.echo-pm/lessons.json` for `base_weight < 0.05`. Scan `.echo-pm/knowledge-index.json` for docs not accessed >30d. Mark `archived: true, archived_at: ISO8601` (NEVER delete). Write `retrospectives/[dir]/archive-log.md`.

### Final Assembly
Write `retrospectives/[dir]/README.md`: executive summary, anchor results, patterns found, lessons captured, gaps, narrative link, archive count, next steps.

## Verify Mode

Read most recent retro directory. Validate: all 6 step files present, CHARTER metrics addressed, pulse alerts investigated, archive justified (spot-check 3). Write `reports/retro-audit.md`.

## Summarize Mode

Read retro `README.md` + `narrative.md`. Condense: 1-paragraph executive summary + key stats (completion%, lessons, patterns, archives, open risks, top action). Write `reports/retro-summary.md`.

## Outputs

- `retrospectives/[dir]/README.md`, `anchor-review.md`, `patterns.md`, `gaps.md`, `narrative.md`, `archive-log.md` (run)
- `reports/retro-audit.md` (verify)
- `reports/retro-summary.md` (summarize)
