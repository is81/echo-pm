# /smart-search — Intelligent Search

## Trigger Conditions

Activate when the user says "find", "search", "there was a document", "has anyone mentioned", "look up", "search", "grep", "find", "who changed this", "change impact", "誰が".

## PMBOK Alignment

- **10.3 Control Communications**: Ensure project information is traceable and retrievable
- **13.4 Control Stakeholder Engagement**: Track stakeholder concerns and interaction history
- **4.5 Perform Integrated Change Control**: Search all affected documents and modules before changes

## Echo Origins

Project Echo's dual-system retrieval (see `docs/patterns.md` for details):

- `src/echo/agent/core.py` L518-559: `_retrieve_memories()` — dual-system architecture
- System 1: SQL `ORDER BY priority_score DESC` + keyword overlap scoring
- System 2: LLM semantic re-ranking of System 1's top-K candidates
- Fallback chain: vector similarity (sqlite-vec) → Python cosine → pure keywords
- Post-retrieval `record_access()` positive feedback loop

Core insight: **A cheap, always-available fast path + an optional quality-boosting re-ranker. The expensive path never blocks result delivery. Retrieval IS reinforcement.**

---

## Workflow

### Step 1: Design System 1 — The Fast Path

System 1 requirements:
- ✅ Offline-capable (no external API dependency)
- ✅ Completes within 100ms
- ✅ Never returns empty when relevant results exist
- ✅ Zero dependencies

**Reference implementation** (based on SQLite FTS5 or simple keyword overlap):

```python
def system1_search(query: str, limit: int = 20) -> list[SearchResult]:
    """Fast keyword search. Always available, always returns results."""
    # Option A: SQLite FTS5 full-text index
    results = conn.execute("""
        SELECT *, snippet(knowledge_fts, 0, '<mark>', '</mark>', '...', 32)
        FROM knowledge_fts
        WHERE knowledge_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (fts5_query(query), limit)).fetchall()

    # Option B: If FTS5 is unavailable, fall back to LIKE queries
    if not results:
        keywords = query.split()
        results = conn.execute("""
            SELECT *, 0 as rank FROM knowledge_base
            WHERE """ + " OR ".join(["content LIKE ?"] * len(keywords)),
            [f"%{kw}%" for kw in keywords]
        ).fetchall()

    return results
```

**Scoring**: `score = keyword_overlap × 0.1 + base_weight`

### Step 2: Design System 2 — The Semantic Re-ranker

System 2 is an optional enhancement, never a requirement:

```python
def system2_rerank(query: str, candidates: list[SearchResult],
                   top_k: int = 5) -> list[SearchResult]:
    """LLM semantic re-ranking. Silently returns original results on failure."""
    try:
        # Build prompt: query + top-20 candidates
        response = llm_call(
            system="You are a project knowledge retriever. Select the top-K results most relevant to the query from the candidates.",
            user=f"Query: {query}\nCandidates:\n{format_candidates(candidates)}",
            temperature=0.1,  # Low temperature, pursuing accuracy
        )
        reranked = parse_response(response)
        if reranked:  # Only replace if parsing succeeds
            return reranked[:top_k]
    except Exception:
        pass  # Any failure → silent fallback

    return candidates[:top_k]  # fallback
```

### Step 3: Connect the Fallback Chain

Complete retrieval chain (best to worst, each layer auto-falls-through on failure):

```
User Query
    ↓
System 1: FTS5 full-text search
    ↓ (results > 5 AND LLM available?)
System 2: LLM semantic re-rank (optional, try/except)
    ↓ (failed?)
System 1 original results (fallback, always available)
    ↓
Return results + record access (positive feedback loop)
```

### Step 4: Build the Positive Feedback Loop

Call `record_access()` after every retrieval:

```python
def retrieve(query: str) -> list[SearchResult]:
    results = _do_search(query)

    # Retrieval IS reinforcement: found documents get weight boost
    for r in results:
        record_access(r.id)
        # base_weight += 0.02 (cap 1.0)
        # access_count += 1
        # if access_count > 3: extend half_life

    return results
```

**Effect**: Frequently-found documents naturally gain higher priority, forming a virtuous cycle of "this document is useful → more people find it → it ranks higher."

### Step 5: Advanced — Change Impact Analysis

When the user asks "What would be affected if I change this?":

1. Extract change keywords (filenames, function names, module names)
2. System 1 searches all documents mentioning these keywords
3. System 2 re-ranks by "degree of impact"
4. Output impact analysis report, labeling direct/indirect impact

---

## Deliverables

| File | Description |
|------|-------------|
| `tools/search.py` | Dual-system search engine |
| Search Configuration | System 2 toggle, top-K, FTS5 parameters |

---

## Usage Example

```bash
# Quick search (System 1 only)
/smart-search "database migration plan" --fast

# Deep search (enable System 2 semantic re-rank)
/smart-search "who previously suggested replacing MySQL with PostgreSQL?" --deep

# Change impact analysis
/smart-search --impact "auth module"

# The AI will:
# 1. System 1 fast-returns candidates
# 2. If LLM is available and candidates > 5, auto re-rank
# 3. Display results (annotated with source, time, relevance)
# 4. Silently record access, reinforcing relevant document weights
```
