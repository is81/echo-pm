# /project-pulse — Project Pulse

## Trigger Conditions

Activate when the user says "project status", "health check", "pulse", "how's the project going", "risk assessment", "progress report", "team status", "dashboard", "project health check", "weekend report".

## PMBOK Alignment

- **4.4 Monitor Project Work**: Track, review, and report overall project progress
- **6.7 Control Schedule**: Monitor schedule variance, take corrective action
- **7.4 Control Costs**: Monitor cost variance, manage budget changes
- **11.6 Control Risks**: Track identified risks, monitor residual risks, identify new risks

## Echo Origins

Project Echo's two-dimensional emotional state model + dynamic parameter modulation (see `docs/patterns.md` for details):

- `src/echo/agent/core.py` L30-81: `EmotionalState` class — valence × arousal 2D vector
- `src/echo/agent/core.py` L1009-1031: Dynamic temperature formula — health state influences behavioral parameters
- Natural regression mechanism: automatically regresses toward baseline when no events occur for a long time (prevents historical noise)
- Heuristic updates: No LLM needed, pure computational methods

Core insight: **Use low-dimensional continuous state (2D) to modulate multiple downstream behaviors (reports, alerts, recommendations). Project health is not binary (good/bad) — it's a continuous thought-space.**

---

## Workflow

### Step 1: Build the Two-Dimensional Project Health Model

Referencing Echo's valence × arousal model, build the project management version:

| Dimension | Range | Baseline | Meaning |
|-----------|-------|----------|---------|
| **Valence (Project Morale)** | [-1.0, 1.0] | 0.3 | Team satisfaction, stakeholder confidence, requirement stability |
| **Arousal (Activity Intensity)** | [0.0, 1.0] | 0.3 | Commit frequency, PR merge velocity, meeting density, change frequency |

#### Valence Signal Sources (Positive ↑ / Negative ↓)

| Signal | Impact | Weight |
|--------|--------|--------|
| PR merged smoothly (no revert) | +0.03 | Low |
| Positive stakeholder feedback received | +0.15 | High |
| Frequent requirement changes | -0.10 | High |
| Rising bug count trend | -0.08 | Medium |
| Increasing team overtime | -0.12 | High |
| Milestone delivered on time | +0.10 | High |

#### Arousal Signal Sources (Active ↑ / Calm ↓)

| Signal | Impact | Weight |
|--------|--------|--------|
| Daily commit count | +0.02 × count | Low |
| PR merge frequency | +0.05 × daily avg | Medium |
| Meeting hours | +0.03 × hours | Low |
| 3 consecutive days without commits | -0.15 | Medium |
| Approaching release date | +0.20 | High |
| Code freeze period | -0.25 | High |

### Step 2: Configure Natural Regression

**Key design**: When no events occur for a long time, state automatically regresses toward baseline.

```python
# Every hour without events → one regression step toward baseline
REGRESSION_RATE = 0.02  # Regression amount per step
BASELINE = (0.0, 0.3)   # (valence_baseline, arousal_baseline)

def natural_regression(state, hours_since_last_event):
    steps = hours_since_last_event  # One step per hour
    for _ in range(steps):
        state.valence += (BASELINE[0] - state.valence) * REGRESSION_RATE
        state.arousal += (BASELINE[1] - state.arousal) * REGRESSION_RATE
    return state
```

**Design rationale**: Prevents a crisis from two years ago from permanently affecting today's project health reading.

### Step 3: Define Health → Behavior Mapping

| Health Zone | Valence | Arousal | Interpretation | Suggested Action |
|-------------|---------|---------|----------------|------------------|
| 🔥 Hyperactive | — | > 0.7 | Pace too fast, burnout risk | Suggest slowing down, check sustainability |
| 😊 Healthy | > 0.3 | 0.3–0.7 | Positive and active | Maintain pace |
| 😴 Stagnant | — | < 0.1 | Project stalled | Check blocking factors |
| 😰 Anxious | < -0.2 | > 0.5 | High pressure, high intensity | Suggest communication intervention |
| 💀 Crisis | < -0.5 | — | Serious issues | Trigger risk escalation |

### Step 4: Generate Weekly Project Pulse Report

Referencing Echo's idle_initiate pattern (selecting different behavior types based on state):

**Report structure**:

```
Project Pulse Weekly — 2026-W28
══════════════════════════════

📊 Health Dashboard
  Valence:  ████████░░ +0.45  (↑ 0.08 vs last week)
  Arousal:  ██████░░░░  0.52  (↓ 0.03 vs last week)
  Status: 😊 Healthy — Maintain pace

📈 Key Signals (This Week)
  ✅ Milestone M3 delivered on time (+0.10)
  ⚠️ 3 requirement changes (-0.30 cumulative)
  ✅ Positive stakeholder feedback (+0.15)

🔮 Trend Forecast
  • Release date approaching next week → arousal expected to rise
  • 3 unresolved tech debts accumulating → downward risk on valence

💡 Recommended Actions
  1. Schedule a tech debt assessment before release
  2. Stakeholder feedback consistently positive → consider increasing communication frequency
```

### Step 5: Set Up Automatic Alerts

Referencing Echo's dynamic temperature (state influencing output parameters):

- **Valence < -0.3 sustained for 7 days** → Trigger stakeholder communication recommendation
- **Arousal > 0.8 sustained for 3 days** → Trigger burnout warning
- **Both low (V < -0.3 AND A < 0.1) sustained for 5 days** → Trigger project health crisis alert

---

## Deliverables

| File | Description |
|------|-------------|
| `PULSE.md` | Latest pulse report |
| `tools/pulse_tracker.py` | Health tracker |
| `templates/pulse-dashboard.md` | Pulse dashboard template |

---

## Usage Example

```bash
# Check current health
/project-pulse

# Generate weekly report
/project-pulse --report weekly

# Manually record a signal
/project-pulse --signal "Received positive customer feedback" --impact +0.15

# View trends
/project-pulse --trend 30d

# The AI will:
# 1. Auto-collect signals from git log, PR records, etc.
# 2. Calculate current valence and arousal
# 3. Output health dashboard + trend forecast + recommended actions
```
