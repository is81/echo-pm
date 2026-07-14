---
name: import
description: Import documents with content-hash dedup, dry-run preview, and knowledge base reporting.
argument-hint: "[mode:import|dry-run|report] [--source <path>]"
---

# /import

## Mode Detection

| User intent | Mode |
|-------------|------|
| "import/ingest/sync documents", "build knowledge base" | **import** |
| "preview/scan/dry-run", "what would be imported" | **dry-run** |
| "knowledge base status/stats" | **report** |

## Import Mode

1. Determine source from user path or Glob `docs/**/*.md`, `*.md`.
2. For each file: `SHA256(content)[:16]` hash. Skip binary, >1MB.
3. Load `.echo-pm/knowledge-index.json` if exists. Classify: NEW (hash not in index), DUPLICATE (same hash, different path), UPDATED (same path, different hash), UNCHANGED (skip).
4. Write `.echo-pm/knowledge/[hash].md` per new/updated file — YAML frontmatter: `source, hash, imported, size, tags`, then original content.
5. Update `.echo-pm/knowledge-index.json`: `{updated, total_documents, documents: {hash: {source, size, imported, tags}}}`.
6. Auto-tag from content keywords: architecture, api, database, deployment, testing, design, requirements, meeting, decision. Add source dir name as tag.
7. Report: N new, M updated, D skipped, S unchanged. Total T.

## Dry-Run Mode

Same steps 1-3, write nothing. Output `reports/import-preview.md` with file lists by status. Ask "Proceed?"

## Report Mode

Read `.echo-pm/knowledge-index.json`. Analyze: total docs/size, source distribution, import timeline, stale (>30d), orphans (source file gone), tag distribution. Write `reports/knowledge-status.md`.

## Outputs

- `.echo-pm/knowledge-index.json`, `.echo-pm/knowledge/[hash].md` (import)
- `reports/import-preview.md` (dry-run)
- `reports/knowledge-status.md` (report)
