# Project Pulse Dashboard

> Update frequency: Daily / per `/project-pulse` invocation
> Data sources: git log, PR activity, manual signal input

---

## Current Status

| Metric | Current | Last Week | Trend |
|--------|---------|-----------|-------|
| Valence (Morale) | | | — |
| Arousal (Activity Intensity) | | | — |
| Health Zone | | | — |
| Active Items | | | — |
| PRs Merged This Week | | | — |

---

## Trend Chart

```
Valence
+1.0 │
     │
  0  │──────────────────── Baseline
     │
-1.0 │
     └────────────────────────── Time →

Arousal
 1.0 │
     │
 0.3 │──────────────────── Baseline
     │
 0.0 │
     └────────────────────────── Time →
```

---

## Signal Log

| Time | Event | V Δ | A Δ |
|------|-------|-----|-----|
| | | | |
| | | | |

---

## Alert Rules

| Condition | Status | Last Triggered |
|-----------|--------|----------------|
| V < -0.3 sustained for 7 days | ✅ Normal | — |
| A > 0.8 sustained for 3 days | ✅ Normal | — |
| V < -0.3 AND A < 0.1 sustained for 5 days | ✅ Normal | — |
