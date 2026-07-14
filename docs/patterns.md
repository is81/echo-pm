# 回响计划七大模式详解

本文档记录 EchoPM 从回响计划（Project Echo）中提取的七个核心设计模式。每个模式包括：来源文件、核心公式/算法、设计哲学、以及如何映射到项目管理。

---

## 模式 A：基因级不可变原则

**来源**：
- `F:/Project Echo/config/principles.yaml` — 3 条标记 `immutable: true` 的原则
- `F:/Project Echo/config/birth_inscription.txt` — 19 字出生铭文
- `F:/Project Echo/src/echo/config.py` — 原则加载器
- `F:/Project Echo/src/echo/memory/models.py` — birth memory 的 7 层 SQL+代码保护

**核心思想**：定义"什么永远不能变"比定义"什么应该做"更重要。项目的 DNA 需要 7 层冗余保护。

**映射到项目管理**：项目章程和不可变原则。见 `/project-charter`。

**Echo 的实现细节**：
- `source="birth"` 的记忆享有 7 层保护
- SQL WHERE 子句层 (`WHERE source != 'birth'`) + Python early-return 层 + 配置 immutable flag 层 + 系统提示排序层（identity before context）
- 原则可追加新条目，不可覆盖已有条目

---

## 模式 B：三因素乘法优先级

**来源**：
- `F:/Project Echo/src/echo/memory/models.py` L74-152

**核心公式**：
```
P = W_base × f_access × f_emotion × f_recency

f_access = 1.0 + log(1 + access_count) × 0.1    # 对数递减
f_emotion = 1.0 + |valence| × 0.3 + arousal × 0.2  # 强度信号
f_recency = 0.5 ^ (age_hours / half_life_hours)     # 指数衰减
```

**设计要点**：
- 乘法而非加法 — 单一弱项会拖垮总分
- base_weight 起始 0.5（不是 1.0）— 为新事项留增长空间
- half_life 因记忆而异 — 高唤醒记忆衰减减半
- 主动遗忘阈值 0.05 — 软删除，数据不丢失

**映射到项目管理**：backlog 优先级排序。见 `/priority-backlog`。

---

## 模式 C：睡眠期记忆整理

**来源**：
- `F:/Project Echo/src/echo/agent/core.py` L177-248 — `sleep()` 方法
- `F:/Project Echo/src/echo/memory/summarizer.py` — 记忆压缩器

**六个独立步骤**：
1. 锚点反思 — 更新自我认知
2. 模式结晶 — 从经验中提炼规律
3. 对话学习 — 提取事实性知识
4. 自主探索 — 主动搜索新知识（8h 冷却）
5. 记忆压缩 — 将旧细节分组 → LLM 摘要 → 存档原始
6. 主动遗忘 — priority < 0.05 的标记遗忘

**设计要点**：
- 每个步骤包裹在独立 try/except 中
- 超时保护（总 30s，自主探索 8h 冷却）
- 生命周期边界是维护的正确时机（不占用交互延迟预算）

**映射到项目管理**：阶段回顾和收尾。见 `/retrospective`。

---

## 模式 D：优雅降级链

**来源**：
- `F:/Project Echo/src/echo/llm/backend.py` L298-331 — LLM 后端优先级链
- `F:/Project Echo/src/echo/memory/store.py` L25-30 — numpy 可选导入
- `F:/Project Echo/src/echo/memory/store.py` L122-133 — sqlite-vec 可选导入
- `F:/Project Echo/src/echo/zim_reader.py` L191-220 — libzim 可选导入

**核心模式**：
```python
# 模块级 feature flag
try:
    import optional_dependency
    _FEATURE_AVAILABLE = True
except ImportError:
    _FEATURE_AVAILABLE = False

# 使用时检查 flag + 提供 fallback
if _FEATURE_AVAILABLE:
    result = use_feature()
else:
    result = fallback_implementation()  # 纯 Python 备选

# 多后端优先级链
for backend in [best, better, fallback]:
    try:
        return backend.try()
    except Exception:
        continue
return graceful_error_message()  # 永远不 crash
```

**映射到项目管理**：所有 skills 核心功能零依赖。辅助工具放在 `tools/` 可选使用。

---

## 模式 E：双系统检索

**来源**：
- `F:/Project Echo/src/echo/agent/core.py` L518-559 — `_retrieve_memories()`
- `F:/Project Echo/src/echo/memory/store.py` L411-457 — 向量相似度搜索（含回退）

**架构**：
```
查询 → System 1 (快速关键词, 始终可用)
      → System 2 (LLM 语义重排, try/except 包裹)
      → 返回结果 + record_access() 正反馈闭环
```

**设计要点**：
- System 1 必须 < 100ms、离线可用、绝不返回空
- System 2 是可选增强，任何失败 → 静默回退到 System 1 原始结果
- 向量搜索作为中间层（sqlite-vec → Python cosine → 纯文本，层层回退）
- 检索即强化 — 被检索到的记忆自动提升权重

**映射到项目管理**：项目知识库智能搜索。见 `/smart-search`。

---

## 模式 F：锚点自模型

**来源**：
- `F:/Project Echo/src/echo/consciousness/anchors.py` — SoulAnchor / AnchorRegistry
- `F:/Project Echo/config/anchors.yaml` — 18 个灵魂锚点定义（4 个维度）
- `F:/Project Echo/src/echo/consciousness/crystallize.py` — CrystallizationEngine

**核心思想**：定义**问题**作为基因，让**答案**在学习中演化。

18 个预定义问题分布在：
- 身份维度（我是谁？我的起源是什么？）
- 价值观维度（我相信什么？什么是不可接受的？）
- 认知维度（我如何思考？我的局限是什么？）
- 关系维度（我与他人的关系？我的责任是什么？）

每个锚点的答案有 confidence score [0, 1]，CrystallizationEngine 每 10 次交互 tick，选择最不确定的锚点进行反思更新。

**映射到项目管理**：项目章程中的锚点（成功度量 + 不可变原则）。见 `/project-charter` + `/retrospective`。

---

## 模式 G：内容哈希幂等导入

**来源**：
- `F:/Project Echo/src/echo/memory/store.py` L173-223 — `bulk_insert()`
- `F:/Project Echo/src/echo/zim_ingest.py` — ZIM 导入管道
- `F:/Project Echo/src/echo/zim_reader.py` — 多策略内容发现

**核心设计**：
```sql
CREATE UNIQUE INDEX idx_content_hash ON memories(content_hash);

-- 幂等插入
INSERT OR IGNORE INTO memories (...) VALUES (...);
```

**设计要点**：
- content_hash = SHA256(content)[:16] — 16 个十六进制字符（64 bits）
- 去重由 SQLite UNIQUE INDEX 强制执行（不是应用层 check-then-insert）
- 分批事务 + 逐条 IntegrityError 处理 → 部分成功
- 预演模式（dry-run）：先扫描报告，确认再导入
- 内容模式可配置：titles / first_para / full
- 多策略发现：主策略 → 备用策略 → 兜底策略

**映射到项目管理**：知识导入管道。见 `/knowledge-import`。

---

## 模式交叉引用

```
模式 A (不可变原则) ──────────────────────→ /project-charter
模式 B (三因素优先级) ────────────────────→ /priority-backlog
模式 C (睡眠期整理) ──────────────────────→ /retrospective
模式 D (优雅降级) ───────────→ 所有 skills 的基础设计原则
模式 E (双系统检索) ──────────────────────→ /smart-search
模式 F (锚点自模型) ────────→ /project-charter + /retrospective
模式 G (幂等导入) ────────────────────────→ /knowledge-import
                                           /lesson-capture（也用到 G 的去重）
                       模式 C + E + D ──→ /project-pulse
```
