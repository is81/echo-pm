---
name: prioritize
description: Rank backlog items using multiplicative priority scoring, validate ranking quality, and generate priority reports.
argument-hint: "[mode:rank|validate|report] [--source <file or 'gh'>]"
---

# /prioritize

## Purpose

This skill ranks a list of tasks/items using a multiplicative priority formula derived from Project Echo's memory model. Unlike additive ranking (where strengths compensate for weaknesses), multiplicative scoring ensures a single weak dimension (e.g., "high value but completely infeasible") drags down the total score. In validate mode, it audits ranking quality for anomalies. In report mode, it shows priority trends over time.

## Modes

### Mode 1: Rank (default)

**What it does:**

1. **Find or accept the backlog source:**
   - If user specifies `--source <file>`, Read that file
   - If user says `--source gh`, run `gh issue list --state open --limit 100 --json title,labels,body,createdAt,updatedAt` to fetch GitHub issues
   - Otherwise, Glob for common backlog files: `BACKLOG.md`, `TODO.md`, `issues.md`, `roadmap.md` in project root
   - If nothing found, ask: "Where's your backlog? (Point me to a file, paste a list, or say 'gh' for GitHub issues.)"

2. **Parse each item:**
   - Extract: title, description/body
   - Infer `value_score` [0,1] from indicators:
     - Labels like "P0/critical/blocker" → 1.0
     - "P1/high/important" → 0.8
     - "P2/medium" → 0.5
     - "P3/low/nice-to-have" → 0.3
     - "wontfix/declined" → 0.1
     - Otherwise, estimate from description context (words like "critical", "urgent", "important" → higher; "someday", "maybe", "if time" → lower)
   - Infer `urgency_score` [0,1] from deadline indicators:
     - Explicit dates in the past → 1.0
     - "ASAP/urgent/immediately" → 0.9
     - "this week/sprint" → 0.7
     - "this month" → 0.5
     - "next quarter/someday/later" → 0.2
     - No deadline mention → 0.0
   - Infer `feasibility_score` [0,1] from complexity indicators:
     - "trivial/simple/quick/one-line" → 0.9
     - "straightforward/small" → 0.7
     - (no indicator) → 0.5
     - "complex/large/effort" → 0.3
     - "research/spike/unknown/risky" → 0.1
   - Note assumptions clearly — mark scores inferred from text with "(estimated)"

3. **Load access history:**
   - Read `.echo-pm/access-log.json` if it exists
   - For each item, determine: `access_count` (how many times surfaced), `last_accessed` (timestamp), `base_weight` (starts at 0.5, +0.02 per prior access, cap 1.0)
   - Items new to the system get base_weight=0.5

4. **Compute priority for each item:**

   ```
   P = base_weight × f_value × f_urgency × f_feasibility × f_recency × f_access

   Where:
     f_value     = 1.0 + value_score × 0.3
     f_urgency   = 1.0 + urgency_score × 0.4
     f_feasibility = 0.5 + feasibility_score × 0.5    (min 0.5 — infeasible ≠ worthless)
     f_recency   = 0.5 ^ (days_since_access / half_life_days)
     f_access    = 1.0 + log(max(1, 1 + access_count)) × 0.1
   ```

   Default `half_life_days` = 7.

5. **Sort by score descending and classify:**
   - P > 0.70: 🔥 HIGH PRIORITY
   - P 0.15-0.70: Normal
   - P 0.05-0.15: ⚠️ NEEDS ATTENTION (low score — why is it still here?)
   - P < 0.05: 🗄 ARCHIVE CANDIDATE

6. **Write** `reports/priority-ranking.md`:
   ```markdown
   # Priority Ranking Report — YYYY-MM-DD
   **Source:** BACKLOG.md | **Items:** N | **Dimensions:** Value, Urgency, Feasibility, Recency, Access

   ## Top Priority (P > 0.70)
   | # | Item | P-Score | Value | Urgency | Feasibility | Status |
   |---|------|---------|-------|---------|-------------|--------|
   | 1 | User auth refactor | 0.89 | 0.9 | 0.7 | 0.8 | 🔥 HIGH |

   ## Normal Priority (P 0.15-0.70)
   ...

   ## Needs Attention (P 0.05-0.15)
   ...

   ## Archive Candidates (P < 0.05)
   ...

   ## Score Breakdown
   [For top-5 items, show how each factor contributed to the score]
   ```

7. **Record access** for feedback loop:
   - Update `.echo-pm/access-log.json` with an entry for each item surfaced in this ranking

**Output:**
- `reports/priority-ranking.md`
- `.echo-pm/access-log.json` (updated)

---

### Mode 2: Validate

**What it does:**

1. **Read** the backlog source and the latest `reports/priority-ranking.md`

2. **Run validation checks:**

   | Check | Severity | What to look for |
   |-------|----------|-----------------|
   | Unscored items | WARNING | Items with no value/urgency indicators — flag as "needs estimation" |
   | Deadline passed | ERROR | Items with deadlines in the past still ranked as "normal" |
   | Stale high-priority | WARNING | Items ranked HIGH (P>0.7) but not accessed/modified in 7+ days |
   | Inconsistency | ERROR | Item labeled "urgent/critical" but ranked below non-urgent items |
   | Overdue archive | INFO | Items below forget threshold (P<0.05) that haven't been archived |
   | Flat distribution | INFO | All items have similar scores (±0.1) — ranking not differentiating |
   | Missing dimension | WARNING | Feasibility not estimable for technical items — needs input |

3. **Write** `reports/priority-audit.md`:
   ```markdown
   # Priority Audit — YYYY-MM-DD
   **Backlog size:** N | **Last ranked:** [date]

   ## Errors (N)
   | # | Item | Issue | Fix |
   ...

   ## Warnings (N)
   ...

   ## Info (N)
   ...
   ```

**Output:** `reports/priority-audit.md`

---

### Mode 3: Report

**What it does:**

1. **Read** all `reports/priority-ranking.md` history (Glob `reports/priority-ranking*.md`)

2. **Analyze trends:**
   - Score movement: which items are climbing (gaining priority) vs falling?
   - Distribution histogram: how many HIGH/NORMAL/LOW/ARCHIVE per ranking
   - Dimension contribution: which factor (value, urgency, feasibility, recency) is driving most scores?
   - Average scores over time

3. **Write** `reports/priority-dashboard.md`:
   ```markdown
   # Priority Dashboard — YYYY-MM-DD
   **Tracking since:** [first ranking date]

   ## Score Distribution
   🔥 HIGH (P>0.7):   ██████ 6
      NORMAL (0.15-0.7): ██████████████ 14
   ⚠️ LOW (0.05-0.15):   ████ 4
   🗄 ARCHIVE (<0.05):    ██ 2

   ## Trends
   [ASCII chart showing score distribution over last 4 rankings]

   ## Dimension Analysis
   Value is the dominant factor for 60% of top-10 items.
   Recency is dragging down 8 items — consider if they need attention.

   ## Items to Watch
   - [Item]: was HIGH (0.82) two rankings ago, now NORMAL (0.45) — losing relevance?
   - [Item]: has been LOW for 3 consecutive rankings — decide: invest or archive?
   ```

**Output:** `reports/priority-dashboard.md`

---

## Mode Detection

| User says | Mode |
|-----------|------|
| "prioritize/rank/sort/order backlog/items/tasks", "what should I do first" | rank |
| "check/validate/audit priorities/backlog", "are my priorities right", "priority quality" | validate |
| "priority report/dashboard/summary/trends/overview" | report |

## Outputs

| File | Mode |
|------|------|
| `reports/priority-ranking.md` | rank |
| `reports/priority-audit.md` | validate |
| `reports/priority-dashboard.md` | report |
| `.echo-pm/access-log.json` | rank (updated) |

## Trigger Conditions

Activate when the user says: "prioritize", "rank my backlog", "what should I work on first", "priority ranking", "sort these tasks", "backlog priority", "validate priorities", "check backlog health", "priority audit", "priority report", "priority dashboard", "backlog trends".
