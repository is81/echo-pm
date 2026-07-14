# The Seven Patterns of Project Echo — Detailed Guide

This document records the seven core design patterns that EchoPM extracted from Project Echo. Each pattern includes: source files, core formulas/algorithms, design philosophy, and how it maps to project management.

---

## Pattern A: Gene-Level Immutable Principles

**Sources**:
- `F:/Project Echo/config/principles.yaml` — 3 principles marked `immutable: true`
- `F:/Project Echo/config/birth_inscription.txt` — 19-character birth inscription
- `F:/Project Echo/src/echo/config.py` — Principle loader
- `F:/Project Echo/src/echo/memory/models.py` — 7-layer SQL + code protection for birth memories

**Core idea**: Defining "what must never change" is more important than defining "what should be done." A project's DNA needs 7 layers of redundant protection.

**Maps to project management**: Project charter and immutable principles. See `/project-charter`.

**Echo's implementation details**:
- Memories with `source="birth"` enjoy 7-layer protection
- SQL WHERE clause layer (`WHERE source != 'birth'`) + Python early-return layer + config immutable flag layer + system prompt ordering layer (identity before context)
- Principles can append new entries, but never overwrite existing ones

---

## Pattern B: Three-Factor Multiplicative Priority

**Sources**:
- `F:/Project Echo/src/echo/memory/models.py` L74-152

**Core formula**:
```
P = W_base × f_access × f_emotion × f_recency

f_access = 1.0 + log(1 + access_count) × 0.1    # Logarithmic decay
f_emotion = 1.0 + |valence| × 0.3 + arousal × 0.2  # Intensity signal
f_recency = 0.5 ^ (age_hours / half_life_hours)     # Exponential decay
```

**Design highlights**:
- Multiplication, not addition — a single weak factor drags down the total score
- base_weight starts at 0.5 (not 1.0) — leaves growth room for new items
- half_life varies per memory — high-arousal memories decay at half rate
- Active forget threshold at 0.05 — soft delete, no data loss

**Maps to project management**: Backlog priority ranking. See `/priority-backlog`.

---

## Pattern C: Sleep-Phase Memory Consolidation

**Sources**:
- `F:/Project Echo/src/echo/agent/core.py` L177-248 — `sleep()` method
- `F:/Project Echo/src/echo/memory/summarizer.py` — Memory compressor

**Six independent steps**:
1. Anchor reflection — Update self-awareness
2. Pattern crystallization — Distill patterns from experience
3. Conversational learning — Extract factual knowledge
4. Autonomous exploration — Proactively search for new knowledge (8h cooldown)
5. Memory compression — Group old details → LLM summary → archive originals
6. Active forgetting — Mark items with priority < 0.05 as forgotten

**Design highlights**:
- Each step wrapped in independent try/except
- Timeout protection (30s total, 8h cooldown for autonomous exploration)
- Lifecycle boundary is the right time for maintenance (doesn't consume interaction latency budget)

**Maps to project management**: Phase retrospective and closeout. See `/retrospective`.

---

## Pattern D: Graceful Degradation Chain

**Sources**:
- `F:/Project Echo/src/echo/llm/backend.py` L298-331 — LLM backend priority chain
- `F:/Project Echo/src/echo/memory/store.py` L25-30 — numpy optional import
- `F:/Project Echo/src/echo/memory/store.py` L122-133 — sqlite-vec optional import
- `F:/Project Echo/src/echo/zim_reader.py` L191-220 — libzim optional import

**Core pattern**:
```python
# Module-level feature flag
try:
    import optional_dependency
    _FEATURE_AVAILABLE = True
except ImportError:
    _FEATURE_AVAILABLE = False

# Check flag at usage + provide fallback
if _FEATURE_AVAILABLE:
    result = use_feature()
else:
    result = fallback_implementation()  # Pure Python alternative

# Multi-backend priority chain
for backend in [best, better, fallback]:
    try:
        return backend.try()
    except Exception:
        continue
return graceful_error_message()  # Never crash
```

**Maps to project management**: All skills have zero-dependency core functionality. Helper tools in `tools/` are optional.

---

## Pattern E: Dual-System Retrieval

**Sources**:
- `F:/Project Echo/src/echo/agent/core.py` L518-559 — `_retrieve_memories()`
- `F:/Project Echo/src/echo/memory/store.py` L411-457 — Vector similarity search (with fallbacks)

**Architecture**:
```
Query → System 1 (fast keywords, always available)
      → System 2 (LLM semantic re-rank, wrapped in try/except)
      → Return results + record_access() positive feedback loop
```

**Design highlights**:
- System 1 must be < 100ms, offline-capable, never return empty
- System 2 is an optional enhancement — any failure → silent fallback to System 1 original results
- Vector search as intermediate layer (sqlite-vec → Python cosine → plain text, layered fallbacks)
- Retrieval IS reinforcement — retrieved memories automatically get weight boosts

**Maps to project management**: Intelligent project knowledge base search. See `/smart-search`.

---

## Pattern F: Anchor Self-Model

**Sources**:
- `F:/Project Echo/src/echo/consciousness/anchors.py` — SoulAnchor / AnchorRegistry
- `F:/Project Echo/config/anchors.yaml` — 18 soul anchor definitions (4 dimensions)
- `F:/Project Echo/src/echo/consciousness/crystallize.py` — CrystallizationEngine

**Core idea**: Define **questions** as genes, let **answers** evolve through learning.

18 predefined questions distributed across:
- Identity dimension (Who am I? What is my origin?)
- Values dimension (What do I believe? What is unacceptable?)
- Cognition dimension (How do I think? What are my limitations?)
- Relationship dimension (My relationship with others? My responsibilities?)

Each anchor's answer has a confidence score [0, 1]. The CrystallizationEngine ticks every 10 interactions, selecting the least-certain anchor for reflection and update.

**Maps to project management**: Anchors in the project charter (success metrics + immutable principles). See `/project-charter` + `/retrospective`.

---

## Pattern G: Content-Hash Idempotent Import

**Sources**:
- `F:/Project Echo/src/echo/memory/store.py` L173-223 — `bulk_insert()`
- `F:/Project Echo/src/echo/zim_ingest.py` — ZIM import pipeline
- `F:/Project Echo/src/echo/zim_reader.py` — Multi-strategy content discovery

**Core design**:
```sql
CREATE UNIQUE INDEX idx_content_hash ON memories(content_hash);

-- Idempotent insert
INSERT OR IGNORE INTO memories (...) VALUES (...);
```

**Design highlights**:
- content_hash = SHA256(content)[:16] — 16 hexadecimal characters (64 bits)
- Deduplication enforced by SQLite UNIQUE INDEX (not application-layer check-then-insert)
- Batch transactions + per-item IntegrityError handling → partial success
- Dry-run mode: scan and report first, confirm before importing
- Configurable content modes: titles / first_para / full
- Multi-strategy discovery: primary strategy → fallback → last resort

**Maps to project management**: Knowledge import pipeline. See `/knowledge-import`.

---

## Pattern Cross-Reference

```
Pattern A (Immutable Principles) ──────────────→ /project-charter
Pattern B (Three-Factor Priority) ─────────────→ /priority-backlog
Pattern C (Sleep Consolidation) ───────────────→ /retrospective
Pattern D (Graceful Degradation) ──→ Foundational design principle for ALL skills
Pattern E (Dual-System Retrieval) ─────────────→ /smart-search
Pattern F (Anchor Self-Model) ─────→ /project-charter + /retrospective
Pattern G (Idempotent Import) ─────────────────→ /knowledge-import
                                                  /lesson-capture (also uses G's dedup)
                              Patterns C + E + D → /project-pulse
```
