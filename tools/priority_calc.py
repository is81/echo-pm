#!/usr/bin/env python3
"""Three-factor multiplicative priority calculator.

Derived from Project Echo's src/echo/memory/models.py compute_priority() formula.

Usage:
    python priority_calc.py --items items.json --output report.md

Dependencies: Python 3.8+ (zero external dependencies)
"""

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class BacklogItem:
    """A backlog item to rank. Corresponds to Project Echo's Memory model."""
    id: str
    title: str
    description: str = ""

    # Scoring inputs
    value_score: float = 0.5        # [0, 1] Business value
    urgency_score: float = 0.0      # [0, 1] Urgency
    feasibility_score: float = 0.5  # [0, 1] Technical feasibility
    stakeholder_weight: float = 1.0 # [0.5, 1.5] Stakeholder weight

    # State tracking
    base_weight: float = 0.5        # Starts at 0.5, leaves room for growth
    access_count: int = 0           # Number of times referenced
    last_accessed: float = field(default_factory=lambda: datetime.now().timestamp())
    half_life_days: float = 7.0     # Half-life in days

    # Thresholds
    FORGET_THRESHOLD: float = 0.05   # Archive below this score
    ATTENTION_THRESHOLD: float = 0.15  # Flag "needs attention" below this score

    def compute_priority(self) -> float:
        """Compute multiplicative priority score.

        P = W_base × f_value × f_urgency × f_feasibility × f_stakeholder × f_recency

        Each factor at 1.0 = neutral. Multiplication ensures a single weakness
        drags down the total score.
        """
        # Access frequency factor (logarithmic decay)
        f_access = 1.0 + math.log(max(1, 1 + self.access_count)) * 0.1

        # Value factor
        f_value = 1.0 + self.value_score * 0.3

        # Urgency factor
        f_urgency = 1.0 + self.urgency_score * 0.4

        # Feasibility factor (min 0.5, never reaches zero — infeasible ≠ worthless)
        f_feasibility = 0.5 + self.feasibility_score * 0.5

        # Stakeholder factor
        f_stakeholder = self.stakeholder_weight

        # Recency factor (exponential decay)
        hours_since_access = (
            datetime.now().timestamp() - self.last_accessed
        ) / 3600.0
        half_life_hours = self.half_life_days * 24.0
        f_recency = 0.5 ** (hours_since_access / half_life_hours)

        return (
            self.base_weight
            * f_access
            * f_value
            * f_urgency
            * f_feasibility
            * f_stakeholder
            * f_recency
        )

    def record_access(self):
        """Record an access, triggering reinforcement. — Corresponds to Echo's record_access()"""
        self.last_accessed = datetime.now().timestamp()
        self.access_count += 1
        self.base_weight = min(1.0, self.base_weight + 0.02)
        # Frequent access → extended half-life (cap 28 days)
        if self.access_count > 3:
            self.half_life_days = min(
                28.0,
                self.half_life_days * (1.02 ** self.access_count)
            )

    def status(self) -> str:
        """Return item status."""
        p = self.compute_priority()
        if p < self.FORGET_THRESHOLD:
            return "Archive"
        elif p < self.ATTENTION_THRESHOLD:
            return "Needs Attention"
        elif p > 0.70:
            return "High Priority"
        else:
            return "Normal"


def rank_items(items: list[BacklogItem]) -> list[tuple[BacklogItem, float]]:
    """Rank a list of items, returns (item, score) sorted descending."""
    scored = [(item, item.compute_priority()) for item in items]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def generate_report(ranked: list[tuple[BacklogItem, float]],
                    output_path: str = "priority-report.md"):
    """Generate priority ranking report."""
    lines = [
        "# Priority Ranking Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total items: {len(ranked)}",
        "",
        "## Top Items",
        "",
    ]

    active = [(item, score) for item, score in ranked if score >= 0.05]
    archived = [(item, score) for item, score in ranked if score < 0.05]

    for i, (item, score) in enumerate(active, 1):
        status_flag = "⚠️" if score < 0.15 else ("🔥" if score > 0.70 else "")
        lines.append(
            f"{i}. {status_flag} [P={score:.3f}] **{item.title}** "
            f"— {item.status()}"
        )

    if archived:
        lines.append("")
        lines.append("## Archive Candidates (P < 0.05)")
        lines.append("")
        for item, score in archived:
            lines.append(f"- [P={score:.3f}] {item.title} — Recommend archiving")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report generated: {output_path}")
    print(f"Active items: {len(active)}, Archive candidates: {len(archived)}")


def batch_recalc_sql(table: str = "backlog_items") -> str:
    """Generate SQL for batch recalculation. — Corresponds to Echo store.py's _recalc_all_priorities()"""
    return f"""
UPDATE {table}
SET priority_score = base_weight
    * (1.0 + LOG(MAX(1, 1 + access_count)) * 0.1)
    * (1.0 + value_score * 0.3)
    * (1.0 + urgency_score * 0.4)
    * (0.5 + feasibility_score * 0.5)
    * stakeholder_weight
    * POW(0.5,
        (UNIXEPOCH() - last_accessed) / 3600.0
        / (half_life_days * 24.0)
    )
WHERE status = 'open'
  AND source != 'charter';  -- Charter items never decay
"""


# Demo
if __name__ == "__main__":
    sample_items = [
        BacklogItem(id="1", title="User Login Module Refactor",
                    value_score=0.9, urgency_score=0.7, feasibility_score=0.8,
                    access_count=12, last_accessed=datetime.now().timestamp() - 86400 * 3),
        BacklogItem(id="2", title="API Rate Limiting Implementation",
                    value_score=0.8, urgency_score=0.9, feasibility_score=0.7,
                    access_count=5),
        BacklogItem(id="3", title="2024 Technology Research",
                    value_score=0.3, urgency_score=0.0, feasibility_score=0.9,
                    access_count=0,
                    last_accessed=datetime.now().timestamp() - 86400 * 180),
    ]

    ranked = rank_items(sample_items)
    generate_report(ranked)

    print("\n--- Batch Recalc SQL ---")
    print(batch_recalc_sql())
