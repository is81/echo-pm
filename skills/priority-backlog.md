# /priority-backlog — Priority Ranking

## Trigger Conditions

Activate when the user says "prioritize", "backlog too many items", "what should I do first", "requirement ranking", "priority scoring", "priority", "how to sort", "help me sort", "too many tasks".

## PMBOK Alignment

- **5.1 Plan Scope Management**: Define how to manage project scope and requirements
- **6.2 Define Activities**: Decompose WBS work packages into concrete activities
- **11.3 Perform Qualitative Risk Analysis**: Assess risk probability and impact, prioritize
- **11.4 Perform Quantitative Risk Analysis**: Numerically analyze risk impact on project objectives

## Echo Origins

Project Echo's three-factor multiplicative memory priority (see `docs/patterns.md` for details):

- `src/echo/memory/models.py` L74-152: `compute_priority()` formula
- `src/echo/memory/store.py` L476-495: SQL batch recalculation `_recalc_all_priorities()`
- Formula: **P = W_base × f_access × f_emotion × f_recency**
- Key design: base_weight starts at 0.5 (leaving room for growth), forget threshold at 0.05 (soft delete)

Core insight: **In multiplicative scoring, every dimension matters — a single weakness drags down the total score, unlike additive scoring where strengths can compensate for weaknesses.**

---

## Workflow

### Step 1: Select Ranking Dimensions

Choose 3–5 dimensions applicable to the current context from this library:

| Dimension | Meaning | Best For |
|-----------|---------|----------|
| **Value** | Business/user value magnitude | All scenarios |
| **Urgency** | Time sensitivity | Deadline-driven scenarios |
| **Feasibility** | Technical implementation difficulty (inverted) | Technical solution selection |
| **Risk** | Risk of NOT doing this item | Risk-driven projects |
| **Dependency** | How many other items depend on this | Platform/infrastructure projects |
| **Recency** | Time since last attention | Maintenance backlogs |
| **Stakeholder Weight** | Proposer's influence | Conflicting multi-stakeholder demands |

### Step 2: Design Factor Formulas

For each selected dimension, design a **multiplicative factor** that satisfies:
- Neutral value = 1.0 (no effect on total score)
- Favorable value > 1.0 (amplifies total score)
- Unfavorable value in (0, 1.0) range (shrinks but never zeroes out)
- Cumulative factors use logarithmic decay, temporal factors use exponential decay

**Reference — Echo's factor design**:

```
f_access = 1.0 + log(1 + count) × 0.1    # Logarithmic decay, diminishing returns per access
f_emotion = 1.0 + |valence| × 0.3 + arousal × 0.2  # Emotional intensity, max 1.5×
f_recency = 0.5 ^ (age_hours / half_life_hours)     # Exponential decay, weight halves after one half-life
```

**Generic factor templates**:

```
f_value = 1.0 + value_score × 0.3        # value_score ∈ [0, 1]
f_urgency = 1.0 + (deadline_proximity) × 0.4  # Higher as deadline approaches
f_feasibility = 0.5 + feasibility_score × 0.5  # Minimum 0.5, never reaches zero
```

### Step 3: Set base_weight

**Key design**: base_weight does NOT start at 1.0, but at **0.3–0.5**.

Rationale:
- Leaves room for growth (naturally rises when frequently referenced)
- New items are not inherently important
- Time-tested items naturally float to the top

### Step 4: Set the Forget Threshold

Define the score below which items are soft-deleted/archived:

- **Archive threshold** (Echo: 0.05): Items below this score disappear from the active view but remain in the database
- **Cooldown period** (Echo: 168h = 7 days): How long of inactivity before decay begins

### Step 5: Generate the Calculation Engine

Generate `tools/priority_calc.py`, providing two calculation paths:

**Path A — Single-item calculation** (on add/update):
```python
def compute_priority(item, context):
    """Compute priority score for a single backlog item."""
    f_value = 1.0 + item.value_score * 0.3
    f_urgency = 1.0 + urgency_factor(item.deadline) * 0.4
    f_recency = 0.5 ** (hours_since(item.last_accessed) / item.half_life_hours)
    return item.base_weight * f_value * f_urgency * f_recency
```

**Path B — Batch recalculation** (periodic maintenance, single SQL statement):
```sql
UPDATE backlog_items
SET priority_score = base_weight
    * (1.0 + value_score * 0.3)
    * (1.0 + CASE WHEN deadline IS NOT NULL
        THEN MAX(0, 1.0 - days_to_deadline / 30.0) * 0.4
        ELSE 0 END)
    * POW(0.5, hours_since_last_access / half_life_hours)
WHERE status = 'open';
```

### Step 6: Run and Output Report

Run with real project data and generate a ranking report:

```
Priority Ranking Report
═══════════════════════
Ranking Dimensions: Value, Urgency, Feasibility, Recency
Forget Threshold: 0.05
Generated: 2026-07-14

Top 10:
1. [P=0.89] User Login Module Refactor  ← High value + pending for 3 weeks
2. [P=0.76] API Rate Limiting Implementation
3. [P=0.71] Database Migration Script
...
Archive Candidates (P < 0.05):
42. [P=0.04] 2024 Technology Research — Recommend archiving
```

---

## Deliverables

| File | Description |
|------|-------------|
| `PRIORITY.md` | Ranking formula documentation + dimension descriptions |
| `tools/priority_calc.py` | Python calculation engine |
| `templates/priority-matrix.md` | Priority matrix template |
| Ranking Report | Current backlog ranking results |

---

## Usage Example

```bash
# Facing a backlog of 50+ items
/priority-backlog

# The AI will guide you through:
# 1. "What dimensions do you want to rank by? (Value/Urgency/Feasibility/Risk/Recency)"
# 2. "Are there any particularly urgent deadlines?"
# 3. "Below what score should items be archived?"
# 4. Compute and output the ranking report
# 5. Flag archive candidates
```
