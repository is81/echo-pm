---
name: prioritize
description: Rank backlog items with multiplicative priority scoring, validate quality, report trends.
argument-hint: "[mode:rank|validate|report] [--source <file or 'gh'>]"
---

# /prioritize

## Mode Detection

| User intent | Mode |
|-------------|------|
| "prioritize/rank/sort backlog", "what should I do first" | **rank** |
| "check/validate/audit priorities" | **validate** |
| "priority report/dashboard/summary/trends" | **report** |

## Priority Formula

```
P = base_weight × f_value × f_urgency × f_feasibility × f_recency × f_access

f_value       = 1.0 + value_score × 0.3
f_urgency     = 1.0 + urgency_score × 0.4
f_feasibility = 0.5 + feasibility_score × 0.5
f_recency     = 0.5 ^ (days_since_access / 7)
f_access      = 1.0 + log(max(1, 1 + access_count)) × 0.1
```

Classification: P>0.70→🔥HIGH, 0.15-0.70→Normal, 0.05-0.15→⚠️LOW, <0.05→🗄ARCHIVE

## Score Inference

**value_score [0,1]**: P0/critical/blocker→1.0, P1/high→0.8, P2→0.5, P3/low→0.3, wontfix→0.1. Else from text: "critical/urgent/important"→higher, "someday/maybe"→lower.

**urgency_score [0,1]**: past deadline→1.0, ASAP/immediately→0.9, this week→0.7, this month→0.5, later→0.2, none→0.0.

**feasibility_score [0,1]**: trivial/quick→0.9, straightforward→0.7, (none)→0.5, complex/large→0.3, research/unknown→0.1.

Mark inferred scores with "(estimated)".

## Rank Mode

1. Find backlog: `--source <file>` (Read), `--source gh` (`gh issue list --state open --limit 100 --json title,labels,body,createdAt,updatedAt`), or Glob for `BACKLOG.md, TODO.md, issues.md, roadmap.md`.
2. Parse each item. Infer scores. Load `.echo-pm/access-log.json` for base_weight/access_count (new items=0.5).
3. Compute P per item. Sort descending. Classify.
4. Write `reports/priority-ranking.md`: ranked table (rank|item|P|value|urgency|feasibility|status), archive candidates, top-5 score breakdown.
5. Update `.echo-pm/access-log.json` for each surfaced item.

## Validate Mode

Read backlog + latest ranking. Check:

| Issue | Severity |
|-------|----------|
| Items with all estimated scores (no real indicators) | WARNING |
| Past-deadline items ranked Normal | ERROR |
| HIGH items not accessed in 7+ days | WARNING |
| Item labeled "urgent" ranked below non-urgent items | ERROR |
| P<0.05 items not archived | INFO |
| All scores within ±0.1 (no differentiation) | INFO |

Write `reports/priority-audit.md`.

## Report Mode

Read ranking history. Analyze: score movement, distribution histogram, dominant factor analysis, items stuck LOW for 3+ rankings. Write `reports/priority-dashboard.md`.

## Outputs

- `reports/priority-ranking.md` (rank)
- `reports/priority-audit.md` (validate)
- `reports/priority-dashboard.md` (report)
- `.echo-pm/access-log.json` (rank, updated)
