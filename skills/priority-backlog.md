# /priority-backlog — 优先级排序

## 触发条件

当用户说"排优先级"、"backlog 太多了"、"先做哪个"、"需求排序"、"优先级评分"、"priority"、"怎么排序"、"帮我排一下"、"太多任务了"时激活。

## 对齐 PMBOK

- **5.1 规划范围管理**：定义如何管理项目范围和需求
- **6.2 定义活动**：将 WBS 工作包分解为具体活动
- **11.3 实施定性风险分析**：评估风险概率和影响，排定优先级
- **11.4 实施定量风险分析**：数值化分析风险对项目目标的影响

## 源自回响

Project Echo 的三因素乘法记忆优先级（详见 `docs/patterns.md`）：

- `src/echo/memory/models.py` L74-152：`compute_priority()` 公式
- `src/echo/memory/store.py` L476-495：SQL 批量重算 `_recalc_all_priorities()`
- 公式：**P = W_base × f_access × f_emotion × f_recency**
- 关键设计：base_weight 起始 0.5（留增长空间）、遗忘阈值 0.05（软删除）

核心洞察：**乘法评分中每个维度都重要——单一弱项拖垮总分，不像加法评分中强项可以弥补弱项。**

---

## 工作流

### 第一步：选择排序维度

从以下维度库中选择 3-5 个适用于当前场景的维度：

| 维度 | 含义 | 适用场景 |
|------|------|---------|
| **价值 (value)** | 业务/用户价值大小 | 所有场景 |
| **紧迫性 (urgency)** | 时间敏感程度 | 有 deadline 的场景 |
| **可行性 (feasibility)** | 技术实现难度（取倒数） | 技术方案选择 |
| **风险 (risk)** | 不做这件事的风险 | 风险驱动的项目 |
| **依赖性 (dependency)** | 被多少其他事项依赖 | 平台/基础设施项目 |
| **新鲜度 (recency)** | 上次关注距今多久 | 维护类 backlog |
| **干系人权重 (stakeholder)** | 提出者的影响力 | 多方需求冲突时 |

### 第二步：设计因子公式

对每个选定维度，设计一个**乘法因子**，满足：
- 中性值 = 1.0（不影响总分）
- 有利值 > 1.0（放大总分）
- 不利值在 (0, 1.0) 区间（缩小但不归零）
- 累积型因子用对数递减，时间型因子用指数衰减

**参考 Echo 的因子设计**：

```
f_access = 1.0 + log(1 + count) × 0.1    # 对数递减，每次访问收益递减
f_emotion = 1.0 + |valence| × 0.3 + arousal × 0.2  # 情绪强度，最大 1.5 倍
f_recency = 0.5 ^ (age_hours / half_life_hours)     # 指数衰减，半衰期后权重减半
```

**通用因子模板**：

```
f_value = 1.0 + value_score × 0.3        # value_score ∈ [0, 1]
f_urgency = 1.0 + (deadline_proximity) × 0.4  # 越接近截止日越高
f_feasibility = 0.5 + feasibility_score × 0.5  # 最低 0.5，不归零
```

### 第三步：设定 base_weight

**关键设计**：base_weight 不从 1.0 开始，而是从 **0.3-0.5** 开始。

理由：
- 留出增长空间（被频繁引用时自动上升）
- 新事项不天然等于重要事项
- 经过时间验证的事项自然浮到顶部

### 第四步：设定遗忘阈值

定义得分低于多少时软删除/归档：

- **归档阈值**（Echo: 0.05）：低于此分的事项不再出现在活跃视野中，但保留在数据库
- **冷却期**（Echo: 168h = 7 天）：多久不活跃后开始衰减

### 第五步：生成计算引擎

生成 `tools/priority_calc.py`，提供两种计算路径：

**路径 A — 单条计算**（新增/更新时）：
```python
def compute_priority(item, context):
    """计算单条事项的优先级得分。"""
    f_value = 1.0 + item.value_score * 0.3
    f_urgency = 1.0 + urgency_factor(item.deadline) * 0.4
    f_recency = 0.5 ** (hours_since(item.last_accessed) / item.half_life_hours)
    return item.base_weight * f_value * f_urgency * f_recency
```

**路径 B — 批量重算**（定期维护，SQL 一条语句完成）：
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

### 第六步：运行并输出报告

用实际项目数据跑一遍，生成排序报告：

```
优先级排序报告
═══════════════
排序维度：价值、紧迫性、可行性、新鲜度
遗忘阈值：0.05
生成时间：2026-07-14

Top 10：
1. [P=0.89] 用户登录模块重构  ← 高价值 + pending 3 周
2. [P=0.76] API 限流实现
3. [P=0.71] 数据库迁移脚本
...
归档候选 (P < 0.05)：
42. [P=0.04] 2024年技术预研 —— 建议归档
```

---

## 产出物

| 文件 | 说明 |
|------|------|
| `PRIORITY.md` | 排序公式文档 + 维度说明 |
| `tools/priority_calc.py` | Python 计算引擎 |
| `templates/priority-matrix.md` | 优先级矩阵模板 |
| 排序报告 | 当前 backlog 的排序结果 |

---

## 使用示例

```bash
# 面对 50+ 条需求的 backlog
/priority-backlog

# AI 会引导你：
# 1. "你想用什么维度排序？（价值/紧迫性/可行性/风险/新鲜度）"
# 2. "有没有特别紧急的 deadline？"
# 3. "多少分以下的事项可以归档？"
# 4. 计算并输出排序报告
# 5. 标记归档候选
```
