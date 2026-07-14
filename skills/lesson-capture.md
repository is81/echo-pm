# /lesson-capture — Lesson Capture

## Trigger Conditions

Activate when the user says "record lessons", "what did we learn", "pitfalls log", "lesson learned", "knowledge deposition", "summarize experience", "postmortem", "remember this pitfall", "write this down".

## PMBOK Alignment

- **9.3 Manage Project Team**: Team experience needs to be captured and transmitted
- **13.3 Manage Stakeholder Engagement**: Stakeholder feedback converted into traceable lessons
- **8.2 Perform Quality Assurance**: Lessons learned converted into quality improvement measures

## Echo Origins

Project Echo's three-pathway learning engine (see `docs/patterns.md` for details):

- `src/echo/agent/core.py` L686-804: Three independent learning pathways sharing one `_extract_knowledge()` engine
- Conversational reflection (`_learn_from_conversations`): Extract factual knowledge from discussions
- Tool learning (inline in `respond_stream`): Extract knowledge from tool execution results
- Autonomous exploration (`_explore_and_learn`): Proactively search for new knowledge
- Each source has a different base_weight (0.4 / 0.45 / 0.35)

Core insight: **Diverse input sources share a single low-temperature extraction engine. Each lesson is an independent, retrievable atom — not a monolithic document that's hard to pinpoint.**

---

## Workflow

### Step 1: Establish Three Lesson Capture Channels

#### Channel A — Conversational Reflection 📝

**Trigger timing**: End of day, end of sprint, or after significant discussions

**Capture targets**:
- Key decisions from meetings and their rationale
- Trade-off reasoning from technical discussions
- Implicit assumptions from requirement clarifications
- Conflict resolution approaches and processes

**Weight**: 0.4 (high frequency, lower per-item influence)

#### Channel B — Tool/Practice Learning 🔧

**Trigger timing**: Immediate — record right after stepping on a rake

**Capture targets**:
- Configuration/environment issues and resolution steps
- Hidden API limitations
- Toolchain best practices
- Undocumented behavior discovered during debugging

**Weight**: 0.45 (practice yields truth, slightly higher weight)

#### Channel C — Autonomous Exploration 🔍

**Trigger timing**: Periodic (weekly/per sprint), avoid exceeding 8-hour cooldown

**Capture targets**:
- Technical topics worth deep-diving, identified from project progress
- Unresolved risk signals
- Trends the team ignores but may be important
- Learnable points from competitor/industry movements

**Weight**: 0.35 (autonomous exploration signals are weaker than direct experience)

### Step 2: Run the Shared Knowledge Extraction Engine

Raw text captured from all three channels is fed into a unified extraction engine:

**Extraction rules** (mapping to Echo's `_extract_knowledge()`):
1. Run LLM at low temperature (0.1–0.2), pursuing facts over creativity
2. Output format: one lesson per line, self-contained, no context dependency
3. Each lesson ≤ 200 words (ensuring retrievable granularity)
4. Quantity caps: conversational reflection ≤ 8 per session, tool learning ≤ 3 per session, autonomous exploration ≤ 5 per session

```
System prompt:
You are a project lesson extractor. Extract standalone, factual lessons learned from the following text.
Each lesson must be self-contained (understandable without context).
Do not retell the process — extract only "what was learned".
Format: one lesson per line, starting with "- ".
```

### Step 3: Tag Source and Weight

Each extracted lesson is annotated with:

```yaml
source: "reflection" | "practice" | "exploration"
tags: ["lesson-learned", "technical-decision", "2026-Q3"]
base_weight: 0.4 | 0.45 | 0.35
extracted_at: "2026-07-14T15:30:00"
related_to: ["module-name", "decision-id"]
```

### Step 4: Deduplicate and Store

Use `content_hash` for deduplication (sharing the same dedup infrastructure as `/knowledge-import`):

- Same lesson captured repeatedly → INSERT OR IGNORE silently skips
- Similar but not identical lessons → keep both (their subtle differences may be valuable)

### Step 5: Periodic Review and Consolidation

At the end of each week/sprint:
1. List all new lessons captured this period
2. Use LLM to identify duplicate or conflicting lessons
3. Upgrade weight for lessons with sufficient evidence (`base_weight += 0.1`)
4. Mark outdated lessons as `archived=True` (soft delete)

---

## Deliverables

| File | Description |
|------|-------------|
| `LESSONS.md` | Lesson library index (organized by time and module) |
| `tools/capture.py` | Lesson capture helper (invokes LLM extraction + storage) |
| Lesson DB (SQLite) | Shares the `knowledge_base` table with knowledge import |

---

## Usage Example

```bash
# End-of-day wrap-up
/lesson-capture --channel reflection --input today-notes.md

# Immediate pitfall recording
/lesson-capture --channel practice --input "How we solved the K8s PVC not releasing issue..."

# Weekly exploration
/lesson-capture --channel exploration

# The AI will:
# 1. Read the input text
# 2. Call LLM at low temperature to extract lesson atoms
# 3. Deduplicate and write to lesson DB
# 4. Output "Captured 5 new lessons, 3 duplicates skipped this session"
# 5. If multiple lessons point to the same pattern, suggest "Consider consolidating into a pattern document"
```
