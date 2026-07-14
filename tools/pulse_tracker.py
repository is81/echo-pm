#!/usr/bin/env python3
"""Project health tracker.

Derived from Project Echo's src/echo/agent/core.py EmotionalState model:
two-dimensional circumplex model (valence × arousal) + natural regression + heuristic updates.

Usage:
    python pulse_tracker.py --init          # Initialize state file
    python pulse_tracker.py --signal "..." --impact +0.15  # Record a signal
    python pulse_tracker.py --report        # Generate report

Dependencies: Python 3.8+ (zero external dependencies)
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Baseline configuration (corresponds to Echo EmotionalState defaults)
BASELINE_VALENCE = 0.0    # Neutral
BASELINE_AROUSAL = 0.3    # Slightly active
REGRESSION_RATE = 0.02    # Per regression step

# Health zone thresholds
HEALTH_ZONES = {
    "hyperactive": {"arousal_min": 0.7, "label": "🔥 Hyperactive", "action": "Suggest slowing down, check sustainability"},
    "healthy":     {"valence_min": 0.3, "arousal_max": 0.7, "arousal_min": 0.3, "label": "😊 Healthy", "action": "Maintain pace"},
    "stagnant":    {"arousal_max": 0.1, "label": "😴 Stagnant", "action": "Check blocking factors"},
    "anxious":     {"valence_max": -0.2, "arousal_min": 0.5, "label": "😰 Anxious", "action": "Suggest communication intervention"},
    "crisis":      {"valence_max": -0.5, "label": "💀 Crisis", "action": "Trigger risk escalation process"},
    "neutral":     {"label": "😐 Stable", "action": "All normal, continue observing"},
}


@dataclass
class ProjectState:
    """Project health state. Corresponds to Echo's EmotionalState."""
    valence: float = 0.3      # Project morale [-1.0, 1.0]
    arousal: float = 0.3      # Activity intensity [0.0, 1.0]
    last_event_at: float = None  # Timestamp of last event
    signals: list[dict] = None   # Recent signal list

    def __post_init__(self):
        if self.last_event_at is None:
            self.last_event_at = datetime.now().timestamp()
        if self.signals is None:
            self.signals = []

    def clamp(self):
        """Clamp bounds."""
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(0.0, min(1.0, self.arousal))

    def record_signal(self, description: str, valence_delta: float,
                      arousal_delta: float):
        """Record a signal, heuristically update state. — Corresponds to Echo's emotional update."""
        self.valence += valence_delta
        self.arousal += arousal_delta
        self.last_event_at = datetime.now().timestamp()
        self.clamp()

        self.signals.append({
            "time": datetime.now().isoformat(),
            "description": description,
            "valence_delta": valence_delta,
            "arousal_delta": arousal_delta,
        })
        # Keep only the most recent 50 signals
        if len(self.signals) > 50:
            self.signals = self.signals[-50:]

    def apply_regression(self, hours_elapsed: float):
        """Natural regression. — Corresponds to Echo's state regression."""
        steps = int(hours_elapsed)
        for _ in range(steps):
            self.valence += (BASELINE_VALENCE - self.valence) * REGRESSION_RATE
            self.arousal += (BASELINE_AROUSAL - self.arousal) * REGRESSION_RATE
        self.clamp()

    def zone(self) -> dict:
        """Determine the current health zone. — Corresponds to Echo's mood_label."""
        v, a = self.valence, self.arousal

        if a > 0.7:
            return HEALTH_ZONES["hyperactive"]
        if v > 0.3 and 0.3 <= a <= 0.7:
            return HEALTH_ZONES["healthy"]
        if a < 0.1:
            return HEALTH_ZONES["stagnant"]
        if v < -0.2 and a > 0.5:
            return HEALTH_ZONES["anxious"]
        if v < -0.5:
            return HEALTH_ZONES["crisis"]
        return HEALTH_ZONES["neutral"]

    def to_dict(self) -> dict:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "last_event_at": self.last_event_at,
            "signals": self.signals[-20:],  # Keep only the most recent 20
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectState":
        return cls(
            valence=d["valence"],
            arousal=d["arousal"],
            last_event_at=d.get("last_event_at"),
            signals=d.get("signals", []),
        )


class PulseTracker:
    """Pulse tracker. Corresponds to Echo's overall health management."""

    def __init__(self, state_file: str = ".echo-pm/pulse.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> ProjectState:
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            state = ProjectState.from_dict(data)
            # Apply regression after recovery
            hours_elapsed = (
                datetime.now().timestamp() - state.last_event_at
            ) / 3600.0
            if hours_elapsed > 0:
                state.apply_regression(hours_elapsed)
            return state
        return ProjectState()

    def save(self):
        self.state_file.write_text(
            json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def pulse(self) -> dict:
        """Get current pulse."""
        zone = self.state.zone()
        return {
            "valence": self.state.valence,
            "arousal": self.state.arousal,
            "zone_label": zone["label"],
            "action": zone["action"],
            "recent_signals": self.state.signals[-5:],
        }

    def signal(self, description: str, valence_delta: float = 0.0,
               arousal_delta: float = 0.0):
        """Record a signal."""
        self.state.record_signal(description, valence_delta, arousal_delta)
        self.save()

    def generate_report(self) -> str:
        """Generate a pulse report."""
        p = self.pulse()
        lines = [
            "# Project Pulse Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 📊 Health Dashboard",
            f"  Valence:  {'█' * int(5 + p['valence'] * 5)}{'░' * int(5 - p['valence'] * 5)} {p['valence']:+.2f}",
            f"  Arousal:  {'█' * int(p['arousal'] * 10)}{'░' * int(10 - p['arousal'] * 10)} {p['arousal']:.2f}",
            f"  Status: {p['zone_label']}",
            "",
            f"💡 Recommendation: {p['action']}",
            "",
        ]
        if p["recent_signals"]:
            lines.append("## Recent Signals")
            for s in p["recent_signals"]:
                lines.append(f"- {s['time'][:16]} {s['description']} (V: {s['valence_delta']:+.2f} A: {s['arousal_delta']:+.2f})")

        return "\n".join(lines)


# Signal presets (common project management events → valence/arousal deltas)
SIGNAL_PRESETS = {
    "Milestone achieved":          (+0.10, +0.05),
    "Requirement change":          (-0.10, +0.05),
    "Positive stakeholder feedback": (+0.15, +0.02),
    "Negative stakeholder feedback": (-0.15, +0.05),
    "Bug count rising":            (-0.08, +0.03),
    "Overtime increasing":         (-0.12, +0.08),
    "Release date approaching":    (+0.05, +0.20),
    "Code freeze":                 (+0.02, -0.25),
    "Team member departure":       (-0.30, +0.10),
    "New team member onboarding":  (+0.05, +0.10),
    "Tech debt cleanup":           (+0.08, +0.05),
}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Project health tracker")
    parser.add_argument("--init", action="store_true", help="Initialize state file")
    parser.add_argument("--signal", type=str, help="Signal description")
    parser.add_argument("--impact", type=float, default=0.0, help="Valence delta")
    parser.add_argument("--preset", type=str, choices=list(SIGNAL_PRESETS.keys()),
                        help="Use a preset signal")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--state-file", default=".echo-pm/pulse.json", help="State file path")
    args = parser.parse_args()

    tracker = PulseTracker(args.state_file)

    if args.init:
        tracker.save()
        print(f"State file initialized: {args.state_file}")

    if args.signal or args.preset:
        if args.preset:
            vd, ad = SIGNAL_PRESETS[args.preset]
            desc = args.preset
        else:
            vd, ad = args.impact, 0.02
            desc = args.signal
        tracker.signal(desc, vd, ad)
        print(f"Signal recorded: {desc} (V: {vd:+.2f}, A: {ad:+.2f})")

    if args.report:
        print(tracker.generate_report())
