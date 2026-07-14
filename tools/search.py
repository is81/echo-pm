#!/usr/bin/env python3
"""双系统检索引擎。

源自回响计划 src/echo/agent/core.py 的双系统检索模式：
System 1（快速关键词，始终可用）→ System 2（LLM 语义重排，可选，失败静默回退）

用法：
    python search.py --db knowledge.db --query "数据库迁移" --deep

依赖：Python 3.8+（零外部依赖，使用 sqlite3 内置 FTS5）
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
    """双系统检索引擎。对应 Echo 的 _retrieve_memories()。"""

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
        """System 1：快速关键词搜索。必须 < 100ms，始终返回结果。

        对应 Echo 的 SQL ORDER BY priority_score DESC + 关键词重叠。
        """
        conn = self._get_conn()
        keywords = query.split()

        # 尝试 FTS5
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
            pass  # FTS5 不可用，回退

        # 回退：LIKE 查询 + 关键词重叠评分
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
        """System 2：LLM 语义重排。可选增强，失败静默回退。

        对应 Echo 的 _semantic_rerank()。

        注意：此实现是占位符——真正的 LLM 调用由 Claude Code 在 skill
        运行时完成。独立脚本仅用于演示 System 1。
        """
        # 独立运行时，System 2 不可用，直接返回 System 1 结果
        return candidates[:top_k]

    def search(self, query: str, limit: int = 10,
               enable_system2: bool = True) -> tuple[list[SearchResult], SearchStats]:
        """执行完整的两层检索。对应 Echo 的 retrieve() 流程。"""
        stats = SearchStats()
        t0 = time.perf_counter()

        # System 1：快速通道（始终运行）
        t1 = time.perf_counter()
        results = self.system1_fast_search(query, limit=limit * 3)  # 多取一些给 System 2
        stats.system1_time_ms = (time.perf_counter() - t1) * 1000
        stats.system1_count = len(results)

        # System 2：语义重排（可选）
        if enable_system2 and self.use_system2 and len(results) > 5:
            t2 = time.perf_counter()
            try:
                reranked = self.system2_rerank(query, results, top_k=limit)
                if reranked:
                    results = reranked
                    stats.system2_used = True
            except Exception:
                pass  # 静默回退
            stats.system2_time_ms = (time.perf_counter() - t2) * 1000

        # 记录访问（正反馈闭环）
        self._record_access([r.id for r in results])

        stats.total_time_ms = (time.perf_counter() - t0) * 1000
        return results[:limit], stats

    def _record_access(self, ids: list[int]):
        """记录检索访问，触发正反馈强化。

        对应 Echo 的 record_access()。
        base_weight += 0.02（上限 1.0），access_count += 1。
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
        """变更影响分析：搜索所有提及 keyword 的文档。

        对应 /smart-search 的 --impact 模式。
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
    parser = argparse.ArgumentParser(description="双系统检索引擎")
    parser.add_argument("--db", default="knowledge.db", help="SQLite 数据库路径")
    parser.add_argument("--query", required=True, help="搜索查询")
    parser.add_argument("--deep", action="store_true", help="启用 System 2（需要 LLM）")
    parser.add_argument("--impact", action="store_true", help="变更影响分析模式")
    parser.add_argument("--fast", action="store_true", help="仅使用 System 1")
    args = parser.parse_args()

    search_engine = DualSystemSearch(
        args.db,
        use_system2=not args.fast,
    )

    if args.impact:
        results = search_engine.impact_search(args.query)
        print(f"变更影响分析 — \"{args.query}\"")
        print(f"找到 {len(results)} 条相关文档：")
    else:
        results, stats = search_engine.search(
            args.query,
            enable_system2=args.deep,
        )
        print(f"搜索 \"{args.query}\" — {stats.system1_count} 条候选"
              f" ({stats.system1_time_ms:.1f}ms)"
              + (f" → System 2 重排 ({stats.system2_time_ms:.1f}ms)"
                 if stats.system2_used else ""))

    for i, r in enumerate(results, 1):
        preview = r.snippet[:120] if r.snippet else r.content[:120]
        print(f"\n{i}. [{r.rank:.3f}] ({r.source})")
        print(f"   {preview}...")
