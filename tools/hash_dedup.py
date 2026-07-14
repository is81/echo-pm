#!/usr/bin/env python3
"""内容哈希去重工具。

源自回响计划 src/echo/memory/store.py 的 bulk_insert() 模式：
SHA256 前 16 位十六进制作为 content_hash，UNIQUE INDEX + INSERT OR IGNORE。

用法：
    python hash_dedup.py --input docs/ --db knowledge.db

依赖：Python 3.8+（零外部依赖，仅使用 hashlib + sqlite3 内置库）
"""

import hashlib
import sqlite3
from pathlib import Path


def content_hash(text: str) -> str:
    """计算内容哈希（SHA256 前 16 个十六进制字符）。

    对应 Echo models.py 的 content_hash 字段。
    64 bits 的碰撞概率在百万级数据量下可忽略不计。
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def init_db(db_path: str) -> sqlite3.Connection:
    """初始化知识库，创建 memories 表。

    关键设计：UNIQUE INDEX 在 content_hash 上，
    去重由 SQLite 引擎强制执行，而非应用层逻辑。
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'imported',
            tags TEXT DEFAULT '[]',
            base_weight REAL DEFAULT 0.5,
            created_at REAL DEFAULT (UNIXEPOCH())
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_content_hash
        ON knowledge(content_hash)
    """)
    conn.commit()
    return conn


def bulk_insert(conn: sqlite3.Connection,
                items: list[dict],
                batch_size: int = 500) -> dict:
    """批量插入，每个批次一个事务，逐条处理 IntegrityError。

    对应 Echo store.py 的 bulk_insert() 模式：
    - 每批 BEGIN/COMMIT
    - 逐条 try/except IntegrityError
    - 返回插入统计（新插入数、重复跳过数、失败数）

    Args:
        conn: 数据库连接
        items: [{"content": "...", "source": "...", "tags": [...]}, ...]
        batch_size: 每批条数
    """
    stats = {"inserted": 0, "skipped": 0, "failed": 0}

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        conn.execute("BEGIN")
        for item in batch:
            try:
                ch = content_hash(item["content"])
                tags = item.get("tags", [])
                conn.execute(
                    """INSERT INTO knowledge (content_hash, content, source, tags)
                       VALUES (?, ?, ?, ?)""",
                    (ch, item["content"], item.get("source", "imported"),
                     json.dumps(tags) if tags else "[]")
                )
                stats["inserted"] += 1
            except sqlite3.IntegrityError:
                # 重复内容，静默跳过
                stats["skipped"] += 1
            except Exception:
                stats["failed"] += 1
        conn.commit()

    return stats


def dry_run_scan(paths: list[str]) -> list[dict]:
    """预演模式：扫描文件但不插入，返回报告。

    对应 Echo zim_ingest.py 的 dry_run=True 模式。
    """
    results = []
    for path_str in paths:
        p = Path(path_str)
        if p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace")
            results.append({
                "path": str(p),
                "hash": content_hash(content),
                "size": len(content),
                "preview": content[:100] + "..." if len(content) > 100 else content,
            })
        elif p.is_dir():
            for f in p.rglob("*.md"):
                content = f.read_text(encoding="utf-8", errors="replace")
                results.append({
                    "path": str(f),
                    "hash": content_hash(content),
                    "size": len(content),
                    "preview": content[:100] + "..." if len(content) > 100 else content,
                })
    return results


# 需要 json 模块（内置）
import json


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="内容哈希去重导入工具")
    parser.add_argument("--input", nargs="+", required=True, help="输入文件/目录")
    parser.add_argument("--db", default="knowledge.db", help="SQLite 数据库路径")
    parser.add_argument("--dry-run", action="store_true", help="预演模式（不实际导入）")
    args = parser.parse_args()

    if args.dry_run:
        results = dry_run_scan(args.input)
        print(f"扫描结果：{len(results)} 个文件")
        for r in results:
            print(f"  [{r['hash']}] {r['path']} ({r['size']} chars)")
            print(f"    {r['preview']}")
    else:
        items = []
        for r in dry_run_scan(args.input):
            full_content = Path(r['path']).read_text(encoding="utf-8", errors="replace")
            items.append({"content": full_content, "source": r['path']})

        conn = init_db(args.db)
        stats = bulk_insert(conn, items)
        print(f"导入完成：新增 {stats['inserted']}，跳过重复 {stats['skipped']}，失败 {stats['failed']}")
        conn.close()
