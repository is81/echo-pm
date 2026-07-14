#!/usr/bin/env python3
"""三因素乘法优先级计算器。

源自回响计划 src/echo/memory/models.py 的 compute_priority() 公式。

用法：
    python priority_calc.py --items items.json --output report.md

依赖：Python 3.8+（零外部依赖）
"""

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class BacklogItem:
    """待排序事项。对应回响计划的 Memory 模型。"""
    id: str
    title: str
    description: str = ""

    # 评分输入
    value_score: float = 0.5        # [0, 1] 业务价值
    urgency_score: float = 0.0      # [0, 1] 紧迫性
    feasibility_score: float = 0.5  # [0, 1] 技术可行性
    stakeholder_weight: float = 1.0 # [0.5, 1.5] 干系人权重

    # 状态追踪
    base_weight: float = 0.5        # 起始 0.5，留增长空间
    access_count: int = 0           # 被引用次数
    last_accessed: float = field(default_factory=lambda: datetime.now().timestamp())
    half_life_days: float = 7.0     # 半衰期（天）

    # 阈值
    FORGET_THRESHOLD: float = 0.05  # 低于此分归档
    ATTENTION_THRESHOLD: float = 0.15  # 低于此分标记"需关注"

    def compute_priority(self) -> float:
        """计算乘法优先级得分。

        P = W_base × f_value × f_urgency × f_feasibility × f_stakeholder × f_recency

        每个因子 1.0 = 中性。乘法确保单一弱项拖垮总分。
        """
        # 访问频率因子（对数递减）
        f_access = 1.0 + math.log(max(1, 1 + self.access_count)) * 0.1

        # 价值因子
        f_value = 1.0 + self.value_score * 0.3

        # 紧迫性因子
        f_urgency = 1.0 + self.urgency_score * 0.4

        # 可行性因子（最低 0.5，不归零——不可行不等于没价值）
        f_feasibility = 0.5 + self.feasibility_score * 0.5

        # 干系人因子
        f_stakeholder = self.stakeholder_weight

        # 新鲜度因子（指数衰减）
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
        """记录一次访问，触发强化。——对应 Echo 的 record_access()"""
        self.last_accessed = datetime.now().timestamp()
        self.access_count += 1
        self.base_weight = min(1.0, self.base_weight + 0.02)
        # 频繁访问 → 半衰期延长（上限 28 天）
        if self.access_count > 3:
            self.half_life_days = min(
                28.0,
                self.half_life_days * (1.02 ** self.access_count)
            )

    def status(self) -> str:
        """返回事项状态。"""
        p = self.compute_priority()
        if p < self.FORGET_THRESHOLD:
            return "归档"
        elif p < self.ATTENTION_THRESHOLD:
            return "需关注"
        elif p > 0.70:
            return "高优先"
        else:
            return "正常"


def rank_items(items: list[BacklogItem]) -> list[tuple[BacklogItem, float]]:
    """对事项列表排序，返回 (事项, 得分) 降序列表。"""
    scored = [(item, item.compute_priority()) for item in items]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def generate_report(ranked: list[tuple[BacklogItem, float]],
                    output_path: str = "priority-report.md"):
    """生成优先级排序报告。"""
    lines = [
        "# 优先级排序报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"事项总数：{len(ranked)}",
        "",
        "## Top 事项",
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
        lines.append("## 归档候选（P < 0.05）")
        lines.append("")
        for item, score in archived:
            lines.append(f"- [P={score:.3f}] {item.title} —— 建议归档")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"报告已生成：{output_path}")
    print(f"活跃事项：{len(active)}，归档候选：{len(archived)}")


def batch_recalc_sql(table: str = "backlog_items") -> str:
    """生成批量重算的 SQL 语句。——对应 Echo store.py 的 _recalc_all_priorities()"""
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
  AND source != 'charter';  -- 章程事项永不衰减
"""


# 演示
if __name__ == "__main__":
    sample_items = [
        BacklogItem(id="1", title="用户登录模块重构",
                    value_score=0.9, urgency_score=0.7, feasibility_score=0.8,
                    access_count=12, last_accessed=datetime.now().timestamp() - 86400 * 3),
        BacklogItem(id="2", title="API 限流实现",
                    value_score=0.8, urgency_score=0.9, feasibility_score=0.7,
                    access_count=5),
        BacklogItem(id="3", title="2024技术预研",
                    value_score=0.3, urgency_score=0.0, feasibility_score=0.9,
                    access_count=0,
                    last_accessed=datetime.now().timestamp() - 86400 * 180),
    ]

    ranked = rank_items(sample_items)
    generate_report(ranked)

    print("\n--- 批量重算 SQL ---")
    print(batch_recalc_sql())
