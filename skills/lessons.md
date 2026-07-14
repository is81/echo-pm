---
name: lessons
description: Extract lessons from text, deduplicate, audit for issues, and summarize by period.
argument-hint: "[mode:extract|review|summarize] [--input <text or file>]"
---

# /lessons

## Mode Detection

| User intent | Mode |
|-------------|------|
| "capture/record/extract lesson", "remember this" | **extract** |
| "review/audit/check lessons", "stale/duplicate lessons" | **review** |
| "lesson summary", "what did we learn this sprint" | **summarize** |

## Extract Mode

1. Get text from `--input <file>` (Read), inline text, or ask user.
2. LLM extraction (temperature 0.1-0.2):
   ```
   Extract standalone, factual lessons. Each ≤200 words, self-contained.
   Channel: "reflection" (discussion), "practice" (doing/building), "exploration" (research).
   Tags (1-3): technical-decision, process, communication, tooling, architecture, debugging, deployment, testing, design, requirement, risk, performance.
   Cap ≤8 lessons. Output one JSON object per line (JSONL).
   ```
3. Per lesson: `SHA256(content)[:16]` → check against `.echo-pm/lessons.json`. Skip duplicates.
4. Append new to `.echo-pm/lessons.json` (JSONL): `{content_hash, content, channel, base_weight, tags, extracted_at, access_count: 0}`.
   Weights: reflection=0.4, practice=0.45, exploration=0.35.
5. Report: N new, M duplicates skipped. Total T.

## Review Mode

1. Read `.echo-pm/lessons.json`.
2. Audit: stale (>90d unaccessed) → WARNING, near-duplicates (keyword overlap >70%) → WARNING, contradictions (opposite sentiment on same topic) → ERROR, low-evidence (weight <0.2, access=0) → INFO, untagged → INFO, pattern candidates (≥3 same tag) → SUGGESTION.
3. Write `reports/lessons-audit.md`.

## Summarize Mode

1. Read `.echo-pm/lessons.json`, filter by date (default: last 14 days, or `--since`).
2. Group by channel + tags. For tag clusters ≥3, LLM-synthesize 2-3 sentence summary (temp 0.4).
3. Write `reports/lessons-summary-YYYY-MM-DD.md`: channel breakdown, key themes with synthesis, top lessons by weight, overall narrative.

## Outputs

- `.echo-pm/lessons.json` (extract)
- `reports/lessons-audit.md` (review)
- `reports/lessons-summary-YYYY-MM-DD.md` (summarize)
