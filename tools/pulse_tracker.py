#!/usr/bin/env python3
"""项目健康度追踪器。

源自回响计划 src/echo/agent/core.py 的 EmotionalState 模型：
二维 circumplex 模型（valence × arousal）+ 自然回归 + 启发式更新。

用法：
    python pulse_tracker.py --init          # 初始化状态文件
    python pulse_tracker.py --signal "..." --impact +0.15  # 记录信号
    python pulse_tracker.py --report        # 生成报告

依赖：Python 3.8+（零外部依赖）
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# 基线配置（对应 Echo EmotionalState 的默认值）
BASELINE_VALENCE = 0.0    # 中性
BASELINE_AROUSAL = 0.3    # 轻微活跃
REGRESSION_RATE = 0.02    # 每回归步长

# 健康区阈值
HEALTH_ZONES = {
    "hyperactive": {"arousal_min": 0.7, "label": "🔥 亢奋", "action": "建议减速，检查可持续性"},
    "healthy":     {"valence_min": 0.3, "arousal_max": 0.7, "arousal_min": 0.3, "label": "😊 健康", "action": "保持节奏"},
    "stagnant":    {"arousal_max": 0.1, "label": "😴 沉寂", "action": "检查阻塞因素"},
    "anxious":     {"valence_max": -0.2, "arousal_min": 0.5, "label": "😰 焦虑", "action": "建议沟通干预"},
    "crisis":      {"valence_max": -0.5, "label": "💀 危机", "action": "触发风险升级流程"},
    "neutral":     {"label": "😐 平稳", "action": "一切正常，继续观察"},
}


@dataclass
class ProjectState:
    """项目健康状态。对应 Echo 的 EmotionalState。"""
    valence: float = 0.3      # 项目士气 [-1.0, 1.0]
    arousal: float = 0.3      # 活动强度 [0.0, 1.0]
    last_event_at: float = None  # 上次事件时间戳
    signals: list[dict] = None   # 最近的信号列表

    def __post_init__(self):
        if self.last_event_at is None:
            self.last_event_at = datetime.now().timestamp()
        if self.signals is None:
            self.signals = []

    def clamp(self):
        """边界钳制。"""
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(0.0, min(1.0, self.arousal))

    def record_signal(self, description: str, valence_delta: float,
                      arousal_delta: float):
        """记录一个信号，启发式更新状态。——对应 Echo 的情感更新。"""
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
        # 只保留最近 50 条信号
        if len(self.signals) > 50:
            self.signals = self.signals[-50:]

    def apply_regression(self, hours_elapsed: float):
        """自然回归。——对应 Echo 的状态回归。"""
        steps = int(hours_elapsed)
        for _ in range(steps):
            self.valence += (BASELINE_VALENCE - self.valence) * REGRESSION_RATE
            self.arousal += (BASELINE_AROUSAL - self.arousal) * REGRESSION_RATE
        self.clamp()

    def zone(self) -> dict:
        """判断当前所属健康区。——对应 Echo 的 mood_label。"""
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
            "signals": self.signals[-20:],  # 仅保留最近 20 条
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
    """脉搏追踪器。对应 Echo 的整体健康管理。"""

    def __init__(self, state_file: str = ".echo-pm/pulse.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> ProjectState:
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            state = ProjectState.from_dict(data)
            # 恢复后先应用回归
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
        """获取当前脉搏。"""
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
        """记录一个信号。"""
        self.state.record_signal(description, valence_delta, arousal_delta)
        self.save()

    def generate_report(self) -> str:
        """生成脉搏报告。"""
        p = self.pulse()
        lines = [
            "# 项目脉搏报告",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 📊 健康仪表盘",
            f"  Valence:  {'█' * int(5 + p['valence'] * 5)}{'░' * int(5 - p['valence'] * 5)} {p['valence']:+.2f}",
            f"  Arousal:  {'█' * int(p['arousal'] * 10)}{'░' * int(10 - p['arousal'] * 10)} {p['arousal']:.2f}",
            f"  状态：{p['zone_label']}",
            "",
            f"💡 建议：{p['action']}",
            "",
        ]
        if p["recent_signals"]:
            lines.append("## 最近信号")
            for s in p["recent_signals"]:
                lines.append(f"- {s['time'][:16]} {s['description']} (V: {s['valence_delta']:+.2f} A: {s['arousal_delta']:+.2f})")

        return "\n".join(lines)


# 信号预设（常见项目管理事件 → valence/arousal 变化量）
SIGNAL_PRESETS = {
    "里程碑达成":     (+0.10, +0.05),
    "需求变更":       (-0.10, +0.05),
    "正面干系人反馈": (+0.15, +0.02),
    "负面干系人反馈": (-0.15, +0.05),
    "Bug 上升趋势":   (-0.08, +0.03),
    "加班增多":       (-0.12, +0.08),
    "发布日临近":     (+0.05, +0.20),
    "代码冻结":       (+0.02, -0.25),
    "团队离职":       (-0.30, +0.10),
    "新人入职":       (+0.05, +0.10),
    "技术债清理":     (+0.08, +0.05),
}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="项目健康度追踪器")
    parser.add_argument("--init", action="store_true", help="初始化状态文件")
    parser.add_argument("--signal", type=str, help="信号描述")
    parser.add_argument("--impact", type=float, default=0.0, help="Valence 变化量")
    parser.add_argument("--preset", type=str, choices=list(SIGNAL_PRESETS.keys()),
                        help="使用预设信号")
    parser.add_argument("--report", action="store_true", help="生成报告")
    parser.add_argument("--state-file", default=".echo-pm/pulse.json", help="状态文件路径")
    args = parser.parse_args()

    tracker = PulseTracker(args.state_file)

    if args.init:
        tracker.save()
        print(f"状态文件已初始化：{args.state_file}")

    if args.signal or args.preset:
        if args.preset:
            vd, ad = SIGNAL_PRESETS[args.preset]
            desc = args.preset
        else:
            vd, ad = args.impact, 0.02
            desc = args.signal
        tracker.signal(desc, vd, ad)
        print(f"信号已记录：{desc} (V: {vd:+.2f}, A: {ad:+.2f})")

    if args.report:
        print(tracker.generate_report())
