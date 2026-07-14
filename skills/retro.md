---
name: retro
description: Run phase retrospectives — auto-collect data, execute 6 isolated steps, and produce a complete retrospective report with archive.
argument-hint: "[mode:run|verify|summarize] [--scope <sprint-N|phase-N|project>] [--since YYYY-MM-DD] [--until YYYY-MM-DD]"
---

# /retro

## Purpose

This skill runs a full phase retrospective by auto-collecting all relevant data (git log, pulse history, lessons, charter), executing six independently-isolated steps, and producing a complete retrospective report. Each step is wrapped in independent error handling — one failing does not block others. In verify mode, it checks retrospective completeness. In summarize mode, it produces an executive summary.

## Modes

### Mode 1: Run (default)

**What it does:**

#### Phase 0: Data Collection

1. **Determine scope:**
   - If `--scope sprint-N` or `--scope phase-N`: use conventional naming
   - If `--since` and `--until`: use explicit dates
   - If no scope given, ask: "What are we retrospecting? (e.g., 'sprint-14', 'phase-2', 'full project', or give me a date range)"

2. **Create output directory:** `retrospectives/YYYY-MM-DD-[scope-name]/`

3. **Collect all data sources:**

   ```bash
   # Git history for the period
   git log --since=<start> --until=<end> --format="%h %s %an %ad" --date=short

   # Merge commits only
   git log --since=<start> --until=<end> --merges --format="%h %s %ad" --date=short

   # Changed files summary
   git diff --stat <start>..<end>
   ```

   - Read `CHARTER.md` for anchor goals and success metrics
   - Read `.echo-pm/pulse-state.json` for health history
   - Read `.echo-pm/lessons.json` filtered by date range
   - Glob `reports/pulse-*.md` in the period
   - Grep for decision records, RFCs, ADRs created in the period

#### Step 1/6: Anchor Review

1. **Read** CHARTER.md → extract success metrics (checkbox items)
2. **Compare** against actual deliverables (from git log, merged PRs)
3. **Compute** completion rate per metric: NOT_STARTED / IN_PROGRESS / DONE / UNKNOWN
4. **Analyze** positive and negative deviations — what caused each?
5. **Write** `retrospectives/[dir]/anchor-review.md`:
   ```markdown
   # Anchor Review — [scope]
   ## Metric Completion
   | Metric | Status | Evidence | Deviation Analysis |
   |--------|--------|----------|-------------------|
   | [Metric 1] | ✅ DONE | [evidence from git/docs] | On track |
   | [Metric 2] | 🔄 IN PROGRESS | [partial evidence] | Blocked by [reason] |

   ## Overall Achievement: X/Y complete (Z%)
   ## Key Deviations
   - Positive: [what went better than expected and why]
   - Negative: [what fell short and root cause]
   ```
6. **Error handling**: If CHARTER.md missing → write "No charter found — anchor review skipped" and continue

#### Step 2/6: Pattern Crystallization

1. **Analyze** git log for recurring patterns:
   - Same type of commit appearing ≥ 3 times → pattern
   - Commits with "revert" → anti-pattern
   - Hotfix frequency → process gap
2. **Analyze** `.echo-pm/lessons.json` for tag clusters (≥ 3 lessons sharing a tag) → candidate pattern
3. **Use LLM** to distill findings into named patterns with:
   - Pattern name
   - Description (2-3 sentences)
   - Evidence (list of commits/lessons)
   - Recommendation (adopt / refine / avoid)
4. **Write** `retrospectives/[dir]/patterns.md`
5. **Error handling**: If < 10 commits in period → write "Insufficient data for pattern crystallization" and continue

#### Step 3/6: Lesson Extraction

1. **Feed** all commit messages and any textual reports from the period into the lesson extraction engine (same logic as `/lessons` extract mode)
2. **Deduplicate** against existing `.echo-pm/lessons.json`
3. **Append** new lessons tagged with `source: "retrospective"` and `retro_scope: "[scope]"`
4. **Write summary** to `retrospectives/[dir]/` — count of new lessons extracted
5. **Error handling**: If extraction fails → write "Lesson extraction skipped: [error]" and continue

#### Step 4/6: Gap Exploration

1. **Grep** for `TODO|FIXME|HACK|XXX` across all project files (excluding `.git/`, `node_modules/`, `.echo-pm/`)
2. **Read** pulse state — any sustained negative signals in the period?
3. **Compare** against previous retrospective's gap list (if exists) — were prior gaps addressed?
4. **List** open questions, unresolved risks, missed topics
5. **Write** `retrospectives/[dir]/gaps.md`:
   ```markdown
   # Gap Analysis — [scope]
   ## Unresolved from Previous Retro
   - [Item] — status: [still open / partially addressed / resolved]

   ## TODO/FIXME/HACK Scan
   - N TODOs, M FIXMEs, P HACKs found
   - Oldest: [file] — [date]

   ## Missed Topics
   - [Topic that should have been discussed but wasn't]

   ## Open Risks
   - [Risk] — severity: [HIGH/MEDIUM/LOW]
   ```

#### Step 5/6: Memory Compression

1. **Group** all collected data by week within the period
2. **Per week**, use LLM (medium temperature 0.4) to produce a 3-5 sentence narrative summary
3. **Merge** weekly summaries into a phase narrative (≤ 500 words total)
4. **Write** `retrospectives/[dir]/narrative.md`:
   ```markdown
   # Phase Narrative — [scope]
   **Period:** YYYY-MM-DD → YYYY-MM-DD

   [Coherent narrative of what happened in this phase — key events,
    decisions, turning points, and the overall arc. Not a list of facts,
    but a story of the phase.]

   ## Week-by-Week
   ### Week 1 (MM/DD-MM/DD)
   [3-5 sentence summary]

   ### Week 2 (MM/DD-MM/DD)
   [3-5 sentence summary]
   ```
5. **Error handling**: If data is too sparse → write a shorter summary noting the sparsity

#### Step 6/6: Archive

1. **Scan** `.echo-pm/lessons.json` for items with `base_weight < 0.05`
2. **Scan** `.echo-pm/knowledge-index.json` for documents not accessed in 30+ days
3. **Mark** as archived (add `archived: true` and `archived_at: "ISO8601"` to the JSON entries — NEVER delete)
4. **Write** `retrospectives/[dir]/archive-log.md`:
   ```markdown
   # Archive Log — [scope]
   ## Archived Lessons (N)
   | Hash | Content (truncated) | Reason |
   |------|---------------------|--------|
   | a1b2... | "Always use X for Y" | weight < 0.05 |

   ## Archived Knowledge (M)
   | Hash | Source | Reason |
   |------|--------|--------|
   | c3d4... | docs/old-spec.md | 45 days unaccessed |

   ## Recovery
   To restore any item, remove the `archived: true` flag in the source JSON file.
   ```

#### Final Assembly

7. **Write** `retrospectives/[dir]/README.md` — integrated report pulling together all 6 steps:
   ```markdown
   # Retrospective: [scope]
   **Period:** YYYY-MM-DD → YYYY-MM-DD
   **Generated:** YYYY-MM-DD

   ## Executive Summary
   [3-4 sentence overview of the entire retrospective]

   ## Anchor Achievement: X/Y (Z%)
   [Brief summary + link to anchor-review.md]

   ## Patterns Discovered: N
   [List pattern names + link to patterns.md]

   ## Lessons Captured: N new
   [Top 3 lessons + link to lessons summary]

   ## Gaps Identified: N
   [Top gaps + link to gaps.md]

   ## Phase Narrative
   [Link to narrative.md]

   ## Archive: N items
   [Count + link to archive-log.md]

   ## Next Steps
   1. [Actionable item derived from this retro]
   2. ...
   ```

**Output (6 files):**
- `retrospectives/[dir]/README.md` — integrated report
- `retrospectives/[dir]/anchor-review.md` — metric completion
- `retrospectives/[dir]/patterns.md` — crystallized patterns
- `retrospectives/[dir]/gaps.md` — gap analysis
- `retrospectives/[dir]/narrative.md` — phase narrative
- `retrospectives/[dir]/archive-log.md` — archive manifest

---

### Mode 2: Verify

**What it does:**

1. **Read** the most recent retrospective directory

2. **Validate completeness:**
   - Are all 6 step output files present?
   - Does anchor-review.md address ALL CHARTER.md success metrics?
   - Were all pulse alerts from the period investigated? (cross-reference pulse reports)
   - Are there gaps in the date range? (check if any weeks have no data)
   - Are archive decisions justified? (spot-check 3 archived items)

3. **Write** `reports/retro-audit.md`:
   ```markdown
   # Retrospective Audit — [scope]
   ## Step Completion
   | Step | File | Status | Notes |
   |------|------|--------|-------|
   | 1. Anchor Review | ✅ | Complete | All 4 metrics addressed |
   | 2. Patterns | ✅ | Complete | 2 patterns found |
   | ... | | | |

   ## Quality Issues
   - Narrative exceeds 500 words (currently 620)
   - 2 CHARTER metrics not addressed in anchor review
   - Archive decision for [hash] seems premature (accessed 2 weeks ago)

   ## Overall: X/6 steps complete, Y quality issues
   ```

**Output:** `reports/retro-audit.md`

---

### Mode 3: Summarize

**What it does:**

1. **Read** an existing retrospective's `README.md` and `narrative.md`

2. **Condense** into a 1-paragraph executive summary + key stats:
   - Anchor completion %
   - Lessons captured
   - Patterns found
   - Items archived
   - Top action item

3. **Write** `reports/retro-summary.md`:
   ```markdown
   # Retro Summary: [scope]
   [One paragraph executive summary — suitable for stakeholders]

   **By the numbers:**
   - Goals achieved: X/Y (Z%)
   - Lessons captured: N
   - Patterns crystallized: M
   - Items archived: P
   - Open risks: Q

   **Key takeaway:** [Single most important insight]

   **Recommended action:** [Top priority next step]
   ```

**Output:** `reports/retro-summary.md`

---

## Mode Detection

| User says | Mode |
|-----------|------|
| "retrospective/retro/postmortem/sprint retro/phase close/close project/run retro" | run |
| "check retro/validate retrospective/audit retro/verify closing" | verify |
| "retro summary/executive summary/retro overview/quick retro" | summarize |

If `--scope`, `--since`, or `--until` is provided, default to run mode.

## Outputs

| File | Mode |
|------|------|
| `retrospectives/[dir]/README.md` | run |
| `retrospectives/[dir]/anchor-review.md` | run |
| `retrospectives/[dir]/patterns.md` | run |
| `retrospectives/[dir]/gaps.md` | run |
| `retrospectives/[dir]/narrative.md` | run |
| `retrospectives/[dir]/archive-log.md` | run |
| `reports/retro-audit.md` | verify |
| `reports/retro-summary.md` | summarize |

## Trigger Conditions

Activate when the user says: "retrospective", "run a retro", "sprint retrospective", "postmortem", "phase retrospective", "close this phase", "project closeout", "run the retrospective", "verify retrospective", "check retro completeness", "retro summary", "executive summary of retro".
