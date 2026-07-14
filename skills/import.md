---
name: import
description: Import, deduplicate, and index project documents with content-hash idempotency and dry-run preview.
argument-hint: "[mode:import|dry-run|report] [--source <path>]"
---

# /import

## Purpose

This skill scans a directory, deduplicates documents by content hash, and builds a searchable knowledge index in `.echo-pm/knowledge-index.json`. Each unique document gets a hashed atom file in `.echo-pm/knowledge/`. The import is idempotent — running it twice produces no duplicates.

## Modes

### Mode 1: Import (default)

**What it does:**

1. **Determine the source:**
   - If the user specifies a path, use that
   - Otherwise, scan for common doc directories: `./docs/`, `./*.md` (root markdown files)
   - Use Glob to enumerate all files: `{source}/**/*.md`, `{source}/**/*.txt`, `{source}/**/*.yaml`, `{source}/**/*.json`

2. **Read and hash each file:**
   - Read file content (skip binary files, files > 1MB)
   - Compute SHA256 hash truncated to 16 hex chars for content identity
   - Track: file path, hash, size, modification time

3. **Deduplicate against existing index:**
   - If `.echo-pm/knowledge-index.json` exists, load it
   - For each candidate file:
     - **New** (hash not in index): add to import list
     - **Duplicate** (same hash, different path): skip, log path
     - **Updated** (same path, different hash): mark for update
     - **Unchanged** (same path and hash): skip

4. **Write the index and knowledge atoms:**
   - Create `.echo-pm/knowledge/` directory if needed
   - For each new/updated file:
     - Write a knowledge atom: `.echo-pm/knowledge/[hash].md` with frontmatter:
       ```markdown
       ---
       source: [original path]
       hash: [sha256[:16]]
       imported: [ISO8601 timestamp]
       size: [bytes]
       tags: [auto-detected tags]
       ---
       [original content]
       ```
   - Update `.echo-pm/knowledge-index.json`:
     ```json
     {
       "updated": "ISO8601",
       "total_documents": N,
       "documents": {
         "[hash]": {
           "source": "path",
           "size": N,
           "imported": "ISO8601",
           "tags": ["auto", "detected"]
         }
       }
     }
     ```

5. **Auto-detect tags** from content:
   - Scan first 50 lines for keywords matching common categories: "architecture", "api", "database", "deployment", "testing", "design", "requirements", "meeting", "decision"
   - Add the source directory name as a tag

6. **Report results:**
   ```
   Import complete:
   - N new documents imported
   - M documents updated
   - D duplicates skipped
   - S files unchanged
   Index now contains T total documents.
   ```

**Output:**
- `.echo-pm/knowledge-index.json` — master index
- `.echo-pm/knowledge/[hash].md` — per-document atoms

---

### Mode 2: Dry-Run

**What it does:**

Same as Import mode steps 1-3, but does NOT write any files.

**Write** `reports/import-preview.md`:
```markdown
# Import Preview — YYYY-MM-DD HH:MM
**Source:** [path]
**Files found:** N
**New:** X | **Updated:** Y | **Duplicate:** Z | **Unchanged:** W

## New Files
| # | Path | Size | Auto-tags |
|---|------|------|-----------|

## Updated Files
| # | Path | Old Hash | New Hash |
|---|------|----------|----------|

## Duplicates (skipped)
| # | Path | Duplicate of |
|---|------|--------------|
```

Ask: "Proceed with import? (If yes, re-run without --dry-run)"

**Output:** `reports/import-preview.md`

---

### Mode 3: Report

**What it does:**

1. **Read** `.echo-pm/knowledge-index.json`

2. **Analyze:**
   - Total documents and total size
   - Documents by source directory (pie chart as ASCII)
   - Import timeline (documents imported by date)
   - Stale detection: documents not imported/updated in 30+ days
   - Orphan detection: documents whose source files no longer exist (check with Bash: `test -f [source]`)
   - Tag distribution (most common tags)

3. **Write** `reports/knowledge-status.md`:
   ```markdown
   # Knowledge Base Status — YYYY-MM-DD
   **Total documents:** N | **Total size:** X KB | **Last import:** [date]

   ## Source Distribution
   docs/     ████████████ 12
   meetings/ ██████ 6
   designs/  ████ 4

   ## Import Timeline
   [date chart — documents per import session]

   ## Health Checks
   - Stale documents (>30d): N — [list]
   - Orphaned sources: N — [list]
   - Documents with no tags: N

   ## Top Tags
   architecture (8), api (6), meeting (5), ...
   ```

**Output:** `reports/knowledge-status.md`

---

## Mode Detection

| User says | Mode |
|-----------|------|
| "import/ingest/sync/load documents/knowledge/docs" | import |
| "preview/scan/dry-run what would be imported" | dry-run |
| "knowledge base status/stats/report", "import statistics" | report |

## Outputs

| File | Mode |
|------|------|
| `.echo-pm/knowledge-index.json` | import |
| `.echo-pm/knowledge/[hash].md` | import |
| `reports/import-preview.md` | dry-run |
| `reports/knowledge-status.md` | report |

## Trigger Conditions

Activate when the user says: "import documents", "ingest knowledge", "sync docs", "knowledge import", "build knowledge base", "scan and import", "preview import", "dry run import", "knowledge base status", "what's in our knowledge base".
