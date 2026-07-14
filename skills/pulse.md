---
name: pulse
description: Monitor project health via git signals — compute valence/arousal, detect anomalies, and generate pulse reports.
argument-hint: "[mode:check|signal|report] [--event <description>]"
---

# /pulse

## Purpose

This skill reads project signals directly from git history and the filesystem to compute a two-dimensional health score: **Valence** (project morale, [-1.0, 1.0]) and **Arousal** (activity intensity, [0.0, 1.0]). It detects health zones (Healthy, Hyperactive, Stagnant, Anxious, Crisis) and generates actionable reports. A natural regression mechanism prevents old events from permanently poisoning the reading.

## Modes

### Mode 1: Check (default)

**What it does:**

1. **Load previous state:**
   - If `.echo-pm/pulse-state.json` exists, load it
   - Apply natural regression based on elapsed time since last event:
     - `valence += (BASELINE_VALENCE - valence) * 0.02 * hours_elapsed`
     - `arousal += (BASELINE_AROUSAL - arousal) * 0.02 * hours_elapsed`
     - BASELINE_VALENCE = 0.0, BASELINE_AROUSAL = 0.3

2. **Collect signals from git (last 7 days):**

   ```bash
   # Commit volume
   git log --since="7 days ago" --oneline | wc -l

   # Commit sentiment — look for positive vs negative keywords
   git log --since="7 days ago" --format="%s"

   # File churn — files changed most frequently
   git log --since="7 days ago" --diff-filter=M --name-only | sort | uniq -c | sort -rn | head -10

   # Merge frequency
   git log --since="7 days ago" --merges --oneline | wc -l

   # Days since last commit
   git log -1 --format="%ad" --date=unix
   ```

3. **Collect signals from filesystem:**

   - Grep for `TODO|FIXME|HACK|XXX` in project files (exclude `.git/`, `node_modules/`), count by severity:
     - `TODO`: low concern
     - `FIXME`: medium concern
     - `HACK/XXX`: high concern
   - Check `.echo-pm/lessons.json` for lessons captured this week — more lessons = higher arousal (active learning)

4. **Apply signal scoring:**

   | Signal | Valence Δ | Arousal Δ |
   |--------|-----------|-----------|
   | Commit count > 14-day avg + 50% | — | +0.08 |
   | Commit count < 14-day avg - 50% | — | -0.10 |
   | Merge count > 3 | +0.03 | +0.05 |
   | Revert count > 0 | -0.05 per revert | — |
   | Positive keywords in commits (feature, add, improve, implement, support) | +0.01 per 3 | — |
   | Negative keywords (fix, hotfix, bug, rollback, revert, emergency) | -0.02 per occurrence | +0.02 per occurrence |
   | File churn: same file changed 5+ times | -0.03 | +0.05 |
   | 3+ days without commits | -0.08 | -0.10 |
   | TODO count > 20 | -0.05 | — |
   | FIXME count > 5 | -0.08 | — |
   | HACK/XXX count > 0 | -0.03 per occurrence | — |
   | New lessons captured this week (≥ 3) | +0.05 | +0.03 |
   | CHARTER.md modified (signals active governance) | +0.05 | +0.02 |

   Clamp valence to [-1.0, 1.0] and arousal to [0.0, 1.0] after all signals are applied.

5. **Determine health zone:**

   | Zone | Condition | Label |
   |------|-----------|-------|
   | 🔥 Hyperactive | arousal > 0.7 | Pace too fast, burnout risk |
   | 😊 Healthy | valence > 0.3, arousal 0.3-0.7 | Positive and active |
   | 😐 Stable | default | All normal |
   | 😴 Stagnant | arousal < 0.1 | Project stalled |
   | 😰 Anxious | valence < -0.2, arousal > 0.5 | High pressure |
   | 💀 Crisis | valence < -0.5 | Serious issues |

6. **Write outputs:**
   - `.echo-pm/pulse-state.json`:
     ```json
     {
       "valence": 0.45, "arousal": 0.52,
       "last_event_at": 1720000000.0,
       "zone": "😊 Healthy",
       "signals": [{"time":"...", "description":"...", "valence_delta":0.10, "arousal_delta":0.05}]
     }
     ```
   - `reports/pulse-YYYY-MM-DD.md`:
     ```markdown
     # Project Pulse — YYYY-MM-DD
     ## Dashboard
     Valence:  ████████░░ +0.45  (↑ 0.08)
     Arousal:  ██████░░░░  0.52  (↓ 0.03)
     Status: 😊 Healthy — Maintain pace

     ## Signals This Week
     ✅ 12 commits this week (+0.05 arousal)
     ⚠️ 3 reverts detected (-0.15 valence)
     ✅ 5 new lessons captured (+0.05 valence)

     ## Alerts
     - [None / List triggered alerts]

     ## Recommendation
     [Zone-specific action]
     ```

**Output:**
- `.echo-pm/pulse-state.json` — persistent state
- `reports/pulse-YYYY-MM-DD.md` — daily pulse report

---

### Mode 2: Signal (manual input)

**What it does:**

1. **Accept an event description** from the user (natural language)

2. **Classify the event** and infer deltas:

   | Keyword Pattern | Valence Δ | Arousal Δ |
   |-----------------|-----------|-----------|
   | "shipped", "released", "delivered", "launched", "milestone" | +0.10 | +0.05 |
   | "blocked", "stuck", "cannot proceed", "blocker" | -0.08 | +0.03 |
   | "overtime", "burnout", "exhausted", "weekend work" | -0.12 | +0.08 |
   | "team member left", "departed", "resigned" | -0.20 | +0.05 |
   | "new hire", "onboarded", "joined" | +0.05 | +0.08 |
   | "positive feedback", "praise", "stakeholder happy" | +0.15 | +0.02 |
   | "negative feedback", "complaint", "escalation" | -0.15 | +0.05 |
   | "tech debt", "refactor", "cleanup" | +0.05 | +0.05 |
   | "incident", "outage", "downtime", "P0" | -0.25 | +0.15 |

   If no pattern matches, use the valence/arousal deltas the user provides, or ask if uncertain.

3. **Update** `.echo-pm/pulse-state.json` with the new signal

4. **Report** the new pulse reading

**Output:** Updated `.echo-pm/pulse-state.json`

---

### Mode 3: Report

**What it does:**

1. **Read** `.echo-pm/pulse-state.json` and all `reports/pulse-*.md` history

2. **Analyze trends:**
   - Valence trend over last 4 weeks (ASCII sparkline)
   - Arousal trend over last 4 weeks
   - Zone transitions (e.g., "Stable → Healthy at W28")
   - Most common signal categories (deployment, people, quality, process)

3. **Check alerts:**
   - V < -0.3 sustained for 7 days → Stakeholder communication needed
   - A > 0.8 sustained for 3 days → Burnout risk
   - V < -0.3 AND A < 0.1 for 5 days → Project health crisis

4. **Write** `reports/pulse-weekly-YYYY-Www.md`:
   ```markdown
   # Weekly Pulse Report — Week YYYY-Www
   ## Current State
   Valence: +0.45 | Arousal: 0.52 | Zone: 😊 Healthy

   ## Trends
   Valence:  ░░█░░█░░█░█░ (+0.05/week)
   Arousal:  █░█░░░░░█░░ (stable)

   ## Zone History
   W24: 😐 Stable → W26: 😊 Healthy → present

   ## Top Signals This Period
   1. ...

   ## Alert Status
   - Burnout: ✅ Normal

   ## Recommendations
   1. ...
   ```

**Output:** `reports/pulse-weekly-YYYY-Www.md`

---

## Mode Detection

| User says | Mode |
|-----------|------|
| "pulse/health check/how's the project/status" | check |
| "record/log signal/event", "just happened", "notify" | signal |
| "pulse report/weekly/summary/trends/history" | report |

If the user provides an event description without explicitly saying "pulse" or "check", infer signal mode. Default to check mode otherwise.

## Outputs

| File | Mode |
|------|------|
| `.echo-pm/pulse-state.json` | check, signal |
| `reports/pulse-YYYY-MM-DD.md` | check |
| `reports/pulse-weekly-YYYY-Www.md` | report |

## Trigger Conditions

Activate when the user says: "project pulse", "health check", "how's the project", "pulse check", "check pulse", "project status", "record a signal", "log this event", "pulse report", "weekly health", "project trends", "health dashboard".
