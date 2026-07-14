# /smart-search — 智能检索

## 触发条件

当用户说"找一下"、"搜索"、"之前有个文档"、"有没有人提过"、"查一下"、"search"、"grep"、"find"、"这个被谁改过"、"变更影响"、"誰が"时激活。

## 对齐 PMBOK

- **10.3 控制沟通**：确保项目信息可追溯、可检索
- **13.4 控制干系人参与**：追踪干系人关注点和历史交互
- **4.5 实施整体变更控制**：变更前检索所有受影响的文档和模块

## 源自回响

Project Echo 的双系统检索（详见 `docs/patterns.md`）：

- `src/echo/agent/core.py` L518-559：`_retrieve_memories()` — 双系统架构
- System 1：SQL `ORDER BY priority_score DESC` + 关键词重叠评分
- System 2：LLM 语义重排 System 1 的 top-K 候选
- 回退链：向量相似度（sqlite-vec）→ Python cosine → 纯关键词
- 检索后 `record_access()` 正反馈闭环

核心洞察：**廉价的始终可用的快速通道 + 可选的提升质量的重排器。昂贵通道永远不会阻塞结果返回。检索即强化。**

---

## 工作流

### 第一步：设计 System 1 — 快速通道

System 1 的要求：
- ✅ 离线可用（不依赖外部 API）
- ✅ 100ms 内完成
- ✅ 有相关结果时绝不返回空
- ✅ 零依赖

**参考实现**（基于 SQLite FTS5 或简单关键词重叠）：

```python
def system1_search(query: str, limit: int = 20) -> list[SearchResult]:
    """快速关键词检索。始终可用，始终返回结果。"""
    # 方案 A：SQLite FTS5 全文索引
    results = conn.execute("""
        SELECT *, snippet(knowledge_fts, 0, '<mark>', '</mark>', '...', 32)
        FROM knowledge_fts
        WHERE knowledge_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (fts5_query(query), limit)).fetchall()

    # 方案 B：如果 FTS5 不可用，回退到 LIKE 查询
    if not results:
        keywords = query.split()
        results = conn.execute("""
            SELECT *, 0 as rank FROM knowledge_base
            WHERE """ + " OR ".join(["content LIKE ?"] * len(keywords)),
            [f"%{kw}%" for kw in keywords]
        ).fetchall()

    return results
```

**评分**：`score = keyword_overlap × 0.1 + base_weight`

### 第二步：设计 System 2 — 语义重排器

System 2 是可选增强，从来不是必需的：

```python
def system2_rerank(query: str, candidates: list[SearchResult],
                   top_k: int = 5) -> list[SearchResult]:
    """LLM 语义重排。失败时静默返回原始结果。"""
    try:
        # 构建 prompt：query + top-20 candidates
        response = llm_call(
            system="你是项目知识检索器。从候选中选出与查询最相关的 top-K 结果。",
            user=f"查询：{query}\n候选：\n{format_candidates(candidates)}",
            temperature=0.1,  # 低温，追求准确
        )
        reranked = parse_response(response)
        if reranked:  # 解析成功才替换
            return reranked[:top_k]
    except Exception:
        pass  # 任何失败 → 静默回退

    return candidates[:top_k]  # fallback
```

### 第三步：连接回退链

完整的检索链（从最优到最差，每层失败自动下一层）：

```
用户查询
    ↓
System 1: FTS5 全文搜索
    ↓ (结果数 > 5 AND LLM 可用?)
System 2: LLM 语义重排（可选，try/except）
    ↓ (失败?)
System 1 原始结果（fallback，始终可用）
    ↓
返回结果 + 记录访问（正反馈闭环）
```

### 第四步：构建正反馈闭环

每次检索后调用 `record_access()`：

```python
def retrieve(query: str) -> list[SearchResult]:
    results = _do_search(query)

    # 检索即强化：被找到的文档权重上升
    for r in results:
        record_access(r.id)
        # base_weight += 0.02（上限 1.0）
        # access_count += 1
        # 如果 access_count > 3: half_life 延长

    return results
```

**效果**：频繁被找到的文档自然获得更高优先级，形成"这个文档很有用 → 更多人找到它 → 它排得更靠前"的良性循环。

### 第五步：进阶 — 变更影响分析

当用户说"改这个会影响什么？"时：

1. 提取变更关键词（文件名、函数名、模块名）
2. System 1 搜索所有提及这些关键词的文档
3. System 2 按"受影响程度"重排
4. 输出影响分析报告，标注直接/间接影响

---

## 产出物

| 文件 | 说明 |
|------|------|
| `tools/search.py` | 双系统检索引擎 |
| 搜索配置 | System 2 开关、top-K、FTS5 参数 |

---

## 使用示例

```bash
# 快速搜索（只看 System 1 结果）
/smart-search "数据库迁移方案" --fast

# 深度搜索（启用 System 2 语义重排）
/smart-search "之前谁提过用 PostgreSQL 替代 MySQL？" --deep

# 变更影响分析
/smart-search --impact "auth module"

# AI 会：
# 1. System 1 快速返回候选
# 2. 如果有 LLM 且候选 > 5，自动重排
# 3. 展示结果（标注来源、时间、相关性）
# 4. 后台记录访问，强化相关文档的权重
```
