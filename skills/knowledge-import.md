# /knowledge-import — Knowledge Import

## Trigger Conditions

Activate when the user says "import documents", "batch import", "knowledge base", "ingest", "import data", "import these documents", "scrape content", "sync documents", "build a knowledge base".

## PMBOK Alignment

- **4.3 Direct and Manage Project Work**: Knowledge generated during execution needs structured deposition
- **10.2 Manage Communications**: Distribute information in a structured way to those who need it

## Echo Origins

Project Echo's ZIM Wikipedia import pipeline + content-hash idempotent deduplication (see `docs/patterns.md` for details):

- `src/echo/zim_ingest.py`: Multi-strategy discovery (namespace scan → title keyword fallback), configurable content modes, dry-run mode
- `src/echo/memory/store.py` L173-223: `bulk_insert()` — SHA256 content hash + UNIQUE INDEX + INSERT OR IGNORE + batch transactions
- `src/echo/zim_reader.py`: Multi-backend (libzim → fallback → suggest install command)

Core insight: **Making imports safely repeatable is a design-level decision, not an application-level convention. The database layer enforces uniqueness.**

---

## Workflow

### Step 1: Inventory Import Sources

Identify all external knowledge sources to import:

| Source Type | Example | Strategy |
|------------|---------|----------|
| Requirements docs | PRD.md, spec.pdf | Full import |
| Meeting notes | meeting-*.md | Summary import |
| Technical designs | design-*.md | Full import |
| API docs | swagger.json | Structured extraction |
| Code comments | docstrings | Extract key snippets |
| External references | RFCs, papers, blogs | Topic-based filtering |

### Step 2: Define Content Identity

Determine the criteria for "these two documents are the same":

**Reference — Echo's approach**:
```python
content_hash = SHA256(content)[:16]  # 64 bits
```

For your context, optional identity strategies:
- `SHA256(content)` — Deduplicate when content is identical
- `SHA256(path + content)` — Deduplicate only when both path and content match (allows document migration)
- `(business_key, version)` — Business key dedup (allows content iteration)

### Step 3: Establish Database-Level Uniqueness Constraint

**Key design principle**: Deduplication is enforced by the database engine, not by application-layer check-then-insert.

```sql
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    content_mode TEXT,      -- full / summary / title_only
    tags TEXT,              -- JSON array
    base_weight REAL DEFAULT 0.5,
    created_at REAL DEFAULT (UNIXEPOCH())
);

CREATE UNIQUE INDEX idx_content_hash ON knowledge_base(content_hash);
```

Python insert code:
```python
# Use INSERT OR IGNORE (SQLite) or ON CONFLICT DO NOTHING (PostgreSQL)
conn.execute(
    "INSERT OR IGNORE INTO knowledge_base (content_hash, content, source) "
    "VALUES (?, ?, ?)",
    (hash, text, source_path)
)
```

### Step 4: Implement Batch Transaction Import

**Key design**: Each batch is an independent transaction — one batch failure does not affect others. Per-item try/except IntegrityError allows partial success.

```python
for batch in chunks(items, batch_size=500):
    conn.execute("BEGIN")
    for item in batch:
        try:
            insert_one(item)
        except IntegrityError:
            stats.skipped += 1   # Duplicate, skip
        except Exception:
            stats.failed += 1    # Error, log and continue
    conn.commit()
```

### Step 5: Enable Dry-Run Mode

Before actually importing, scan and report first:

```
Dry-Run Report
══════════════
Scan paths: ./docs/, ./meetings/
Files found: 142
To import (after dedup): 87
Already exist (skip): 55
Estimated new knowledge atoms: ~45,000
Content mode: first_para

Confirm import? [y/N]
```

### Step 6: Design Multi-Strategy Discovery + Fallback

**Reference — Echo's dual strategy**: V namespace index → title keyword scan

Generalized as:

```
Strategy A (preferred): Structured metadata extraction (directory index, frontmatter, API schema)
    ↓ Failed/unavailable
Strategy B (fallback): Filesystem scan + filename keyword matching
    ↓ Failed/unavailable
Strategy C (last resort): Full traversal + MIME type filter
```

Each strategy runs independently, recording success/failure counts. Final report shows results from all three strategies.

---

## Deliverables

| File | Description |
|------|-------------|
| `tools/hash_dedup.py` | Content-hash deduplication import tool |
| `schema.sql` | Knowledge base table schema (with UNIQUE INDEX) |
| Import Report | Dry-run + final import statistics |

---

## Usage Example

```bash
# Import all docs into the project knowledge base
/knowledge-import --source ./docs --db project-knowledge.db

# Preview first
/knowledge-import --source ./docs --dry-run

# Specify content mode (title + first sentence only)
/knowledge-import --source ./meetings --mode summary

# The AI will:
# 1. Scan source directories, listing all files
# 2. Calculate dedup statistics
# 3. Show dry-run report (if --dry-run)
# 4. Import in batches, showing progress
# 5. Output import statistics report
```
