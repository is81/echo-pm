# Priority Scoring Matrix

## Formula

```
P = W_base × f_value × f_urgency × f_feasibility × f_recency
```

## Current Dimension Definitions

| Factor | Meaning | Formula | Range |
|--------|---------|---------|-------|
| `W_base` | Base weight | Starts at 0.5, +0.02 per reference (cap 1.0) | [0.05, 1.0] |
| `f_value` | Business value | `1.0 + value_score × 0.3` | [1.0, 1.3] |
| `f_urgency` | Urgency | `1.0 + deadline_proximity × 0.4` | [1.0, 1.4] |
| `f_feasibility` | Feasibility | `0.5 + feasibility_score × 0.5` | [0.5, 1.0] |
| `f_recency` | Recency | `0.5 ^ (days_since_access / half_life_days)` | [0.0, 1.0] |

## Thresholds

- **Forget threshold**: P < 0.05 → Auto-archive (soft delete)
- **Attention threshold**: P < 0.15 → Flag as "needs attention"
- **High priority**: P > 0.70 → Enter Top-N view

## Parameter Tuning Table

| Parameter | Default | Raising it means | Lowering it means |
|-----------|---------|-----------------|-------------------|
| `half_life_days` | 7 | Items survive longer | Items decay faster |
| `base_weight` | 0.5 | New items start with higher priority | New items need more validation |
| `forget_threshold` | 0.05 | Fewer items archived | More items archived |
