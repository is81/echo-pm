---
name: lessons
description: Extract, deduplicate, and review lessons learned from conversations, debugging sessions, and project artifacts.
argument-hint: "[mode:extract|review|summarize] [--input <text or file>]"
---

# /lessons

## Purpose

This skill captures lessons learned as small, self-contained, retrievable atoms. In extract mode, it reads text (conversation, meeting notes, debugging log) and uses low-temperature LLM extraction to produce standalone lesson statements. Each lesson is content-hash deduplicated and appended to `.echo-pm/lessons.json`. In review mode, it audits the lesson base for staleness, duplicates, and contradictions. In summarize mode, it produces a narrative of what was learned in a given period.

## Modes

### Mode 1: Extract (default)

**What it does:**

1. **Get the input text:**
   - If user provides `--input <file>`, Read that file
   - If user provides inline text (quoted or pasted), use that directly
   - If no input is given, ask: "What should I extract lessons from? (Paste text, point me to a file, or describe what happened.)"

2. **Extract lesson atoms (LLM, low temperature 0.1-0.2):**
   - Use the following extraction prompt internally:
     ```
     Extract standalone, factual lessons learned from the following text.
     Rules:
     - Each lesson must be self-contained (understandable without context)
     - Each lesson must be ≤ 200 words
     - Do not retell the process — extract only "what was learned"
     - Classify each lesson into one channel:
       "reflection" — insight from discussion/thinking
       "practice" — learned from doing/debugging/building
       "exploration" — discovered by investigating/researching
     - Assign 1-3 tags from: technical-decision, process, communication, tooling,
       architecture, debugging, deployment, testing, design, requirement, risk, performance
     - Output format: one JSON object per line (JSONL)

     Input text:
     [user's text]
     ```
   - Cap extraction: ≤ 8 lessons per session (reflection), ≤ 5 (practice/exploration)
   - Channel detection: if input mentions "debug", "fix", "error", "deploy" → practice; if "meeting", "discussion", "decided" → reflection; if "research", "investigate", "explore" → exploration

3. **Deduplicate:**
   - For each extracted lesson, compute `SHA256(content)[:16]`
   - If `.echo-pm/lessons.json` exists, check each hash against existing entries
   - Skip duplicates silently; count them for the report

4. **Store:**
   - Append new lessons to `.echo-pm/lessons.json` (one JSON object per line):
     ```json
     {"content_hash":"a1b2c3d4e5f6a7b8","content":"...","channel":"practice","base_weight":0.45,"tags":["debugging","deployment"],"extracted_at":"2026-07-14T15:30:00","access_count":0,"last_accessed":null}
     ```
   - Channel weights: reflection=0.4, practice=0.45, exploration=0.35

5. **Report:**
   ```
   Extraction complete:
   - 5 new lessons captured
   - 2 duplicates skipped
   - Lesson base now contains 47 total lessons.
   ```

**Output:** `.echo-pm/lessons.json` (incremental append)

---

### Mode 2: Review

**What it does:**

1. **Read** `.echo-pm/lessons.json`

2. **Audit for issues:**

   | Check | Method | Severity |
   |-------|--------|----------|
   | Stale lessons | `last_accessed` is null or > 90 days ago | WARNING |
   | Near-duplicates | Content similarity via keyword overlap > 70% | WARNING |
   | Contradictions | Lessons with opposite sentiment on same topic (e.g., "use X" vs "avoid X") | ERROR |
   | Low-evidence | `base_weight < 0.2` and `access_count = 0` | INFO |
   | Untagged | `tags` array is empty | INFO |
   | Pattern candidates | ≥ 3 lessons share the same tag — suggest crystallization | SUGGESTION |

3. **Write** `reports/lessons-audit.md`:
   ```markdown
   # Lesson Base Audit — YYYY-MM-DD
   **Total lessons:** N | **Last extraction:** [date]

   ## Errors (N)
   - Contradiction: "Use PostgreSQL for all projects" vs "SQLite is sufficient in most cases"
     → [lesson IDs]

   ## Warnings (N)
   - Stale: M lessons not accessed in >90 days
   - Near-duplicates: P pairs with >70% similarity

   ## Suggestions (N)
   - Pattern candidate: "Docker deployment" — 4 related lessons, consider crystallizing into a pattern doc
   - N lessons have no tags — auto-tag recommended

   ## Info
   - M low-evidence lessons (single occurrence, unverified)
   ```

**Output:** `reports/lessons-audit.md`

---

### Mode 3: Summarize

**What it does:**

1. **Read** `.echo-pm/lessons.json`, filter by date range:
   - Default: last 14 days
   - If user specifies "--sprint N" or "--since YYYY-MM-DD", use that range

2. **Group by channel and tags:**
   - Channel breakdown: N from reflection, M from practice, P from exploration
   - Tag clusters: group lessons sharing tags

3. **Generate narrative summary (LLM, medium temperature 0.4):**
   - For each tag cluster with ≥ 3 lessons, write a 2-3 sentence synthesis
   - Identify the "story of this period" — the overarching thread connecting lessons

4. **Write** `reports/lessons-summary-YYYY-MM-DD.md`:
   ```markdown
   # Lessons Summary — [period]
   **Period:** YYYY-MM-DD to YYYY-MM-DD
   **Total new lessons:** N

   ## Channel Breakdown
   - 📝 Reflection: N lessons
   - 🔧 Practice: M lessons
   - 🔍 Exploration: P lessons

   ## Key Themes
   ### Deployment (4 lessons)
   [2-3 sentence synthesis of what we learned about deployment]

   ### Debugging (3 lessons)
   [2-3 sentence synthesis]

   ## Narrative: What We Learned This [Sprint/Week]
   [Overall narrative connecting the key themes — what patterns emerged,
    what surprised us, what we should act on]

   ## Top Lessons by Weight
   1. (w=0.52) [Lesson content]
   2. ...
   ```

**Output:** `reports/lessons-summary-YYYY-MM-DD.md`

---

## Mode Detection

| User says | Mode |
|-----------|------|
| "capture/record/extract/save lesson/learned/remember this" | extract |
| "review/audit/check lessons", "stale lessons", "duplicate lessons" | review |
| "lesson summary/summarize", "what did we learn this sprint/week", "lesson report" | summarize |

## Outputs

| File | Mode |
|------|------|
| `.echo-pm/lessons.json` | extract |
| `reports/lessons-audit.md` | review |
| `reports/lessons-summary-YYYY-MM-DD.md` | summarize |

## Trigger Conditions

Activate when the user says: "record a lesson", "capture this lesson", "lesson learned", "what did we learn", "remember this", "extract lessons from", "review lessons", "audit lesson base", "stale lessons", "lesson summary", "summarize lessons", "what have we learned this sprint".
