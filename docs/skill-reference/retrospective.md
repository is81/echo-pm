# /retrospective — Retrospective

## Trigger Conditions

Activate when the user says "project retrospective", "postmortem", "retrospective", "phase summary", "sprint retrospective", "experience summary", "release retrospective", "closing", "project end", "close project".

## PMBOK Alignment

- **4.6 Close Project or Phase**: Complete activities across all process groups, formally close the project/phase
- **12.4 Close Procurements**: Complete contract closeout and knowledge transfer for each procurement

## Echo Origins

Project Echo's sleep-phase memory consolidation (see `docs/patterns.md` for details):

- `src/echo/agent/core.py` L177-248: `sleep()` method — 6 independent maintenance steps
- `src/echo/memory/summarizer.py`: Group → LLM summary → archive original details
- Each step wrapped in independent try/except, one stuck step does not block others
- Cooldown protection (8h) + timeout protection (30s total)
- Hot-warm-cold data tiering: active → archived (weight 0.1) → forgotten (weight 0)

Core insight: **Closing is not a single meeting — it's a multi-step, independently isolated maintenance process. Steps are isolated from each other, ensuring one failed step does not block the entire closeout. Hot-cold tiering preserves raw data while surfacing summaries first.**

---

## Workflow

### Step 1: Preparation Phase

Before executing the six steps:

1. Define the closing scope (Sprint? Phase? Full project?)
2. Collect all data sources generated during the period (git log, meeting notes, PRs, lesson entries, pulse history)
3. Set a total timeout (recommended 30 minutes, prevents infinite loops)
4. Create the retrospective output directory (`retrospectives/YYYY-MM-DD-phase-name/`)

### Step 2: Execute Six Independent Steps

Each step must:
- Be wrapped in an independent try/except
- Have timeout protection (≤ 5 minutes per step)
- Have its own success/failure log
- On step failure → record error + continue to next step

---

#### Step 1/6: Anchor Review

```
Input: Target anchors from CHARTER.md at the start of the phase
Operation:
  1. List every goal set at the start of the phase
  2. Compare against actual achievement
  3. Mark completion rate (%)
  4. Analyze causes of positive and negative deviations
Output: Anchor achievement report
Error handling: If phase-start goals cannot be found → record "goals undefined" and skip
```

#### Step 2/6: Pattern Crystallization

```
Input: This phase's commit log + PRs + lesson-capture entries
Operation:
  1. Identify recurring success patterns (≥3 similar practices)
  2. Identify recurring anti-patterns (≥2 times stepping on the same rake)
  3. Use LLM to distill scattered lessons into reusable pattern descriptions
  4. Update or create pattern documents
Output: New/updated pattern docs + anti-pattern list
Error handling: Insufficient lessons (<10) → skip, note "insufficient lesson accumulation for crystallization"
```

#### Step 3/6: Conversational Learning

```
Input: This phase's meeting notes + PR review discussions
Operation:
  1. Invoke /lesson-capture's extraction engine
  2. Batch extract all lesson atoms from discussions
  3. Deduplicate and write to lesson DB
  4. Tag as source="retrospective"
Output: N new lesson atoms
Error handling: No meeting notes → skip, mark "no conversational material to extract"
```

#### Step 4/6: Gap Exploration

```
Input: All pulse signals + risk log for this phase
Operation:
  1. Review health dashboard historical trends
  2. Identify topics that "should have been watched but weren't"
  3. Scan project documents for TODO/FIXME/HACK
  4. List unresolved open risks
Output: Gap list + remediation suggestions
Error handling: No data → skip
```

#### Step 5/6: Memory Compression

```
Input: All scattered records from this phase (communications, decisions, changes)
Operation:
  1. Group by day (referencing Echo summarizer's date clustering)
  2. Call LLM per group to generate 3–5 sentence narrative summaries
  3. Merge daily summaries into a phase narrative (≤ 500 words)
  4. Archive original records, mark archived=True
Output: Phase narrative summary + archive batch
Error handling: Too many records → compress in batches, each batch independently protected
```

#### Step 6/6: Archive and Forget

```
Input: All items marked as "archivable"
Operation:
  1. Scan knowledge base for entries with base_weight < 0.05
  2. Scan for records not accessed in 30+ days
  3. Mark as archived (soft delete, retained in database)
  4. Generate archive manifest
  5. Provide "unarchive" command
Output: Archive manifest + cold data location
Error handling: None → report "nothing to archive"
```

### Step 3: Generate Retrospective Report

Integrate results from all six steps into a narrative-style (not bullet-list) retrospective report:

```
Project Phase Retrospective Report
══════════════════════════════════
Phase: [Name]
Period: YYYY-MM-DD → YYYY-MM-DD

📌 Anchor Achievement
  [Narrative description of goal achievement]

🧩 Patterns Discovered
  [Narrative description of patterns found]

📖 What We Learned
  [Narrative description of key lessons]

⚠️ Gaps and Risks
  [Items still requiring attention]

📦 Phase Narrative
  [≤500 word overall narrative summary]

🗄 Archive Manifest
  [X records archived, location: ...]
```

### Step 4: Hot-Cold Tiering

Post-closeout data tiering strategy (referencing Echo's three-tier state):

```
Hot Data (active, priority > 0.15)
  → Retained in primary search view
  → Participates in future searches

Warm Data (archived, priority > 0.05)
  → archived=True, base_weight=0.1
  → Retrievable but not surfaced proactively

Cold Data (forgotten, priority < 0.05)
  → forgotten=True
  → Visible only on explicit query
  → Retained in database, recoverable anytime
```

---

## Deliverables

| File | Description |
|------|-------------|
| `retrospectives/YYYY-MM-DD-name/README.md` | Retrospective report |
| `retrospectives/YYYY-MM-DD-name/anchor-review.md` | Anchor achievement report |
| `retrospectives/YYYY-MM-DD-name/patterns.md` | New patterns discovered |
| `retrospectives/YYYY-MM-DD-name/narrative.md` | Phase narrative summary |
| `retrospectives/YYYY-MM-DD-name/archive-log.md` | Archive manifest |

---

## Usage Example

```bash
# Sprint retrospective
/retrospective --scope sprint-14

# Full project closeout
/retrospective --scope project

# The AI will:
# 1. Confirm closeout scope, collect all data from that period
# 2. Execute 6 steps sequentially (showing progress for each)
# 3. Clearly report and continue on any step failure
# 4. Generate the integrated report
# 5. Trigger archive process, showing hot-cold tiering statistics
```
