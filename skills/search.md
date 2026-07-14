---
name: search
description: Dual-system search (Grep + optional LLM re-rank) with change impact analysis.
argument-hint: "[mode:search|impact|report] <query or target>"
---

# /search

## Mode Detection

| User intent | Mode |
|-------------|------|
| "search/find/look up [query]", "deep search" | **search** |
| "impact of changing X", "what depends on Y", "what would break" | **impact** |
| "search status", "index health" | **report** |

## Search Mode

1. **System 1**: Tokenize query → Grep corpus (`.echo-pm/knowledge/*.md`, `docs/*.md`, `CHARTER.md`, `reports/*.md`, root `*.md`) with `-i -C 2`. Score: keyword_match_ratio × 10 + recency_bonus. Return top 20.
2. **System 2** (conditional): If System 1 > 5 AND (user said "deep" OR query is natural-language question), read top-10 (first 500 chars) and LLM re-rank. On failure → silent fallback.
3. Record each surfaced result in `.echo-pm/access-log.json`: `{doc_id, accessed_at, query}`.
4. Write `reports/search-results.md`: ranked results with snippet, source, tags, score.

## Impact Mode

1. Extract targets from query: file paths, module names, concept keywords.
2. Grep each target across project (exclude `.git/`, `node_modules/`, `.echo-pm/`) in `*.md, *.py, *.js, *.ts, *.yaml, *.json`.
3. Classify matches: DIRECT (imports/requires/calls target), INDIRECT (discusses/mentions), DOCUMENTATION (describes behavior), TEST (paths matching `test|spec|__test__`).
4. Write `reports/impact-analysis.md`: summary counts, impact tables with risk levels, suggested change order.

## Report Mode

Read `.echo-pm/knowledge-index.json` + `.echo-pm/access-log.json`. Write `reports/search-dashboard.md`: total docs, top-10 accessed, recent queries, knowledge gaps (tags < 2 docs), untagged docs.

## Outputs

- `reports/search-results.md` (search)
- `reports/impact-analysis.md` (impact)
- `reports/search-dashboard.md` (report)
- `.echo-pm/access-log.json` (updated on search)
