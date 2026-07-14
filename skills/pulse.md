---
name: pulse
description: Monitor project health from git signals — valence/arousal scoring, anomaly detection, weekly reports.
argument-hint: "[mode:check|signal|report] [--event <description>]"
---

# /pulse

## Mode Detection

| User intent | Mode |
|-------------|------|
| "pulse/health check", "how's the project", "project status" | **check** |
| "record/log signal/event", "just happened" | **signal** |
| "pulse report/weekly/summary/trends" | **report** |

## Constants

`BASELINE_VALENCE = 0.0`  `BASELINE_AROUSAL = 0.3`  `REGRESSION_RATE = 0.02`

## Health Zones

```
arousal > 0.7                    → 🔥 Hyperactive (burnout risk)
valence > 0.3, arousal 0.3-0.7  → 😊 Healthy
arousal < 0.1                    → 😴 Stagnant
valence < -0.2, arousal > 0.5    → 😰 Anxious
valence < -0.5                    → 💀 Crisis
else                              → 😐 Stable
```

## Check Mode

1. Load `.echo-pm/pulse-state.json`. Apply regression: `V += (0.0 - V) * 0.02 * hrs`, `A += (0.3 - A) * 0.02 * hrs`.
2. Collect (last 7 days):
   - `git log --since="7 days ago" --oneline | wc -l`
   - `git log --since="7 days ago" --format="%s"`
   - `git log --since="7 days ago" --merges --oneline | wc -l`
   - `git log --since="7 days ago" --diff-filter=M --name-only | sort | uniq -c | sort -rn | head -10`
   - Grep `TODO|FIXME|HACK|XXX` (exclude `.git/`, `node_modules/`)
   - Check new lessons in `.echo-pm/lessons.json` this week
3. Score:

| Signal | VΔ | AΔ |
|--------|-----|-----|
| Commits > 14d avg +50% | — | +0.08 |
| Commits < 14d avg -50% | — | -0.10 |
| Each revert | -0.05 | — |
| Positive keywords (feature, add, improve, implement) per 3 | +0.01 | — |
| Negative keywords (fix, hotfix, bug, rollback, revert, emergency) each | -0.02 | +0.02 |
| Same file changed 5+ times | -0.03 | +0.05 |
| 3+ days no commits | -0.08 | -0.10 |
| TODO > 20 | -0.05 | — |
| FIXME > 5 | -0.08 | — |
| Each HACK/XXX | -0.03 | — |
| ≥3 new lessons this week | +0.05 | +0.03 |

   Clamp V∈[-1.0,1.0], A∈[0.0,1.0]. Determine zone.

4. Write `.echo-pm/pulse-state.json` (valence, arousal, zone, signals[], last_event_at). Write `reports/pulse-YYYY-MM-DD.md` (dashboard bar, signals, zone, recommendation).

## Signal Mode

Accept event description. Classify:

| Pattern | VΔ | AΔ |
|---------|-----|-----|
| shipped/released/delivered/launched/milestone | +0.10 | +0.05 |
| blocked/stuck/cannot proceed/blocker | -0.08 | +0.03 |
| overtime/burnout/exhausted/weekend work | -0.12 | +0.08 |
| departed/resigned/left | -0.20 | +0.05 |
| new hire/onboarded/joined | +0.05 | +0.08 |
| positive feedback/praise/stakeholder happy | +0.15 | +0.02 |
| negative feedback/complaint/escalation | -0.15 | +0.05 |
| tech debt/refactor/cleanup | +0.05 | +0.05 |
| incident/outage/downtime/P0 | -0.25 | +0.15 |

Update `.echo-pm/pulse-state.json`. Report new reading.

## Report Mode

Read state + all `reports/pulse-*.md`. Analyze: V/A 4-week trends (ASCII sparkline), zone transitions, top signal categories.
Alerts: V<-0.3×7d → stakeholder warning; A>0.8×3d → burnout; V<-0.3 AND A<0.1×5d → crisis.
Write `reports/pulse-weekly-YYYY-Www.md`.

## Outputs

- `.echo-pm/pulse-state.json` (check, signal)
- `reports/pulse-YYYY-MM-DD.md` (check)
- `reports/pulse-weekly-YYYY-Www.md` (report)
