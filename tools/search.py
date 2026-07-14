#!/usr/bin/env python3
"""Dual-system search engine.

Derived from Project Echo's src/echo/agent/core.py dual-system retrieval pattern:
System 1 (fast keywords, always available) → System 2 (LLM semantic re-rank, optional, silent fallback on failure)

Usage:
    python search.py --db knowledge.db --query "database migration" --deep

Dependencies: Python 3.8+ (zero external dependencies, uses sqlite3 built-in FTS5)
"""

import json
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchResult:
    id: int
    content: str
    source: str
    rank: float
    snippet: str = ""


@dataclass
class SearchStats:
    system1_time_ms: float = 0.0
    system1_count: int = 0
    system2_time_ms: float = 0.0
    system2_used: bool = False
    total_time_ms: float = 0.0


class DualSystemSearch:
    """Dual-system search engine. Corresponds to Echo's _retrieve_memories()."""

    def __init__(self, db_path: str, use_system2: bool = True,
                 system2_timeout_ms: int = 5000):
        self.db_path = db_path
        self.use_system2 = use_system2
        self.system2_timeout_ms = system2_timeout_ms

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def system1_fast_search(self, query: str, limit: int = 20
                            ) -> list[SearchResult]:
        """System 1: Fast keyword search. Must be < 100ms, always returns results.

        Corresponds to Echo's SQL ORDER BY priority_score DESC + keyword overlap.
        """
        conn = self._get_conn()
        keywords = query.split()

        # Try FTS5
        try:
            fts_query = " OR ".join(keywords)
            rows = conn.execute("""
                SELECT id, content, source, base_weight as rank,
                       snippet(knowledge_fts, 0, '<mark>', '</mark>', '...', 32) as snippet
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (fts_query, limit)).fetchall()

            if rows:
                conn.close()
                return [SearchResult(**dict(r)) for r in rows]
        except Exception:
            pass  # FTS5 unavailable, fall back

        # Fallback: LIKE query + keyword overlap scoring
        like_clauses = " OR ".join(["content LIKE ?"] * len(keywords))
        rows = conn.execute(f"""
            SELECT id, content, source, base_weight as rank,
                   substr(content, 1, 200) as snippet
            FROM knowledge_base
            WHERE {like_clauses}
            ORDER BY base_weight DESC
            LIMIT ?
        """, [f"%{kw}%" for kw in keywords] + [limit]).fetchall()

        conn.close()
        return [SearchResult(**dict(r)) for r in rows]

    def system2_rerank(self, query: str, candidates: list[SearchResult],
                       top_k: int = 5) -> list[SearchResult]:
        """System 2: LLM semantic re-rank. Optional enhancement, silent fallback on failure.

        Corresponds to Echo's _semantic_rerank().

        Note: This implementation is a placeholder — actual LLM invocation is
        performed by Claude Code at skill runtime. The standalone script only
        demonstrates System 1.
        """
        # When running standalone, System 2 is unavailable — return System 1 results directly
        return candidates[:top_k]

    def search(self, query: str, limit: int = 10,
               enable_system2: bool = True) -> tuple[list[SearchResult], SearchStats]:
        """Execute full two-tier retrieval. Corresponds to Echo's retrieve() flow."""
        stats = SearchStats()
        t0 = time.perf_counter()

        # System 1: Fast path (always runs)
        t1 = time.perf_counter()
        results = self.system1_fast_search(query, limit=limit * 3)  # Fetch extra for System 2
        stats.system1_time_ms = (time.perf_counter() - t1) * 1000
        stats.system1_count = len(results)

        # System 2: Semantic re-rank (optional)
        if enable_system2 and self.use_system2 and len(results) > 5:
            t2 = time.perf_counter()
            try:
                reranked = self.system2_rerank(query, results, top_k=limit)
                if reranked:
                    results = reranked
                    stats.system2_used = True
            except Exception:
                pass  # Silent fallback
            stats.system2_time_ms = (time.perf_counter() - t2) * 1000

        # Record access (positive feedback loop)
        self._record_access([r.id for r in results])

        stats.total_time_ms = (time.perf_counter() - t0) * 1000
        return results[:limit], stats

    def _record_access(self, ids: list[int]):
        """Record retrieval access, triggering positive feedback reinforcement.

        Corresponds to Echo's record_access().
        base_weight += 0.02 (cap 1.0), access_count += 1.
        """
        conn = self._get_conn()
        conn.execute("""
            UPDATE knowledge_base
            SET base_weight = MIN(1.0, base_weight + 0.02),
                access_count = access_count + 1,
                last_accessed = UNIXEPOCH()
            WHERE id IN ({})
        """.format(",".join("?" * len(ids))), ids)
        conn.commit()
        conn.close()

    def impact_search(self, keyword: str) -> list[SearchResult]:
        """Change impact analysis: search all documents mentioning the keyword.

        Corresponds to /smart-search's --impact mode.
        """
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT id, content, source, base_weight as rank,
                   substr(content, 1, 200) as snippet
            FROM knowledge_base
            WHERE content LIKE ?
            ORDER BY base_weight DESC
            LIMIT 50
        """, (f"%{keyword}%",)).fetchall()
        conn.close()
        return [SearchResult(**dict(r)) for r in rows]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dual-system search engine")
    parser.add_argument("--db", default="knowledge.db", help="SQLite database path")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--deep", action="store_true", help="Enable System 2 (requires LLM)")
    parser.add_argument("--impact", action="store_true", help="Change impact analysis mode")
    parser.add_argument("--fast", action="store_true", help="System 1 only")
    args = parser.parse_args()

    search_engine = DualSystemSearch(
        args.db,
        use_system2=not args.fast,
    )

    if args.impact:
        results = search_engine.impact_search(args.query)
        print(f"Change Impact Analysis — \"{args.query}\"")
        print(f"Found {len(results)} relevant document(s):")
    else:
        results, stats = search_engine.search(
            args.query,
            enable_system2=args.deep,
        )
        print(f"Search \"{args.query}\" — {stats.system1_count} candidate(s)"
              f" ({stats.system1_time_ms:.1f}ms)"
              + (f" → System 2 re-rank ({stats.system2_time_ms:.1f}ms)"
                 if stats.system2_used else ""))

    for i, r in enumerate(results, 1):
        preview = r.snippet[:120] if r.snippet else r.content[:120]
        print(f"\n{i}. [{r.rank:.3f}] ({r.source})")
        print(f"   {preview}...")
