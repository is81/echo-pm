---
name: search
description: Dual-system search (fast Grep + optional LLM re-rank) across the project knowledge base, with change impact analysis.
argument-hint: "[mode:search|impact|report] <query or target>"
---

# /search

## Purpose

This skill searches the project's knowledge base using a two-tier approach. System 1 uses Grep for fast keyword matching (always available, < 1s). System 2 uses LLM semantic re-ranking when there are many candidates and the user wants deeper results. It also supports change impact analysis — "what would break if I change X?"

## Modes

### Mode 1: Search (default)

**What it does:**

1. **Run System 1 — Fast keyword search:**
   - Tokenize the user's query into keywords
   - Run Grep across the search corpus:
     - `.echo-pm/knowledge/*.md` (imported knowledge atoms)
     - `docs/*.md` (project documentation)
     - `CHARTER.md` (project charter)
     - `reports/*.md` (past reports)
     - `*.md` in project root (README, etc.)
   - Use `Grep` with `output_mode: "content"`, `-C 2` (2 lines context), `-i` (case-insensitive)
   - Score each result by: (keyword matches / total keywords) × 10 + (recency bonus if in knowledge index)
   - Return top 20 results

2. **Run System 2 — LLM semantic re-rank (conditional):**
   - Triggered when: System 1 returns > 5 results AND the user asked for "deep search" or the query is a natural language question (not just keywords)
   - Read the content of top-10 System 1 results (first 500 chars each)
   - Re-rank by semantic relevance to the query
   - If LLM call fails for any reason → silently return System 1 results (graceful degradation)

3. **Record access for reinforcement:**
   - For each result surfaced to the user, update `.echo-pm/access-log.json`:
     ```json
     {"doc_id": "[hash]", "accessed_at": "ISO8601", "query": "[query]"}
     ```

4. **Write** `reports/search-results.md`:
   ```markdown
   # Search: "[query]" — YYYY-MM-DD HH:MM
   **Results:** N | **Method:** System 1 [+ System 2]

   ## Results
   ### 1. [Title/First line] (score: X.X)
   **Source:** [file path] | **Tags:** [...]
   > [Snippet with match highlighted]

   ### 2. ...
   ```

**Output:** `reports/search-results.md`

---

### Mode 2: Impact Analysis

**What it does:**

1. **Extract search targets from the query:**
   - File names: parse anything that looks like a path (e.g., `auth.py`, `src/login.ts`)
   - Module names: parse CamelCase or snake_case identifiers
   - Concepts: the remaining natural language

2. **Search for all references:**
   - For each target, run Grep across the entire project (excluding `.git/`, `node_modules/`, `.echo-pm/knowledge/`):
     - `Grep pattern="[target]" output_mode="content" -C 1`
     - Search in: `*.md`, `*.py`, `*.js`, `*.ts`, `*.yaml`, `*.json`, `*.yml`
   - Also search the knowledge index: check `.echo-pm/knowledge-index.json` for documents tagged with related topics

3. **Classify each match:**
   - **Direct impact**: the file imports/requires/configures the target (look for keywords: `import`, `require`, `reference`, `depends on`, `calls`)
   - **Indirect impact**: the file discusses/mentions the target but doesn't directly depend on it
   - **Documentation impact**: the file describes or documents behavior related to the target
   - **Test impact**: test files that reference the target (paths matching `test`, `spec`, `__test__`)

4. **Write** `reports/impact-analysis.md`:
   ```markdown
   # Impact Analysis: [target] — YYYY-MM-DD

   ## Summary
   - Directly impacted: N files
   - Indirectly impacted: M files
   - Documentation to update: D files
   - Tests to update: T files

   ## Direct Impacts
   | # | File | Why | Risk |
   |---|------|-----|------|
   | 1 | src/auth.py | imports target directly | HIGH |

   ## Indirect Impacts
   ...

   ## Suggested Change Order
   1. [First thing to change]
   2. [Then...]
   ```

**Output:** `reports/impact-analysis.md`

---

### Mode 3: Report

**What it does:**

1. **Read** `.echo-pm/knowledge-index.json` and `.echo-pm/access-log.json`

2. **Analyze:**
   - Total searchable documents
   - Most-accessed documents (top 10)
   - Recent search queries (from access log)
   - Knowledge gaps: tags with very few documents
   - Untagged documents

3. **Write** `reports/search-dashboard.md`:
   ```markdown
   # Search Dashboard — YYYY-MM-DD

   ## Index Health
   - Indexed documents: N
   - Total size: X KB
   - Last import: [date]

   ## Top Accessed
   1. [hash] (N accesses) — [source path]

   ## Recent Queries
   - "[query]" (YYYY-MM-DD) — N results

   ## Gaps & Suggestions
   - Tag "deployment" has only 1 document — consider importing more
   - N documents have no tags — auto-tagging recommended
   ```

**Output:** `reports/search-dashboard.md`

---

## Mode Detection

| User says | Mode |
|-----------|------|
| "search/find/look up/where is/has anyone mentioned [query]" | search |
| "deep search [query]" | search (with System 2 forced) |
| "impact/affected by/change impact/what depends on/what would break if [target]" | impact |
| "search status/index health/searchable/what's indexed" | report |

## Outputs

| File | Mode |
|------|------|
| `reports/search-results.md` | search |
| `reports/impact-analysis.md` | impact |
| `reports/search-dashboard.md` | report |
| `.echo-pm/access-log.json` | search (side effect) |

## Trigger Conditions

Activate when the user says: "search for", "find", "look up", "where is", "has anyone mentioned", "grep for", "search the knowledge base", "deep search", "change impact", "what depends on X", "what would break if", "impact analysis", "search status", "index health".
