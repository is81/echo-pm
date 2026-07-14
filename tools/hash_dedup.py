#!/usr/bin/env python3
"""Content-hash deduplication tool.

Derived from Project Echo's src/echo/memory/store.py bulk_insert() pattern:
SHA256 first 16 hex chars as content_hash, UNIQUE INDEX + INSERT OR IGNORE.

Usage:
    python hash_dedup.py --input docs/ --db knowledge.db

Dependencies: Python 3.8+ (zero external dependencies, uses only hashlib + sqlite3 built-ins)
"""

import hashlib
import sqlite3
from pathlib import Path


def content_hash(text: str) -> str:
    """Compute content hash (first 16 hex characters of SHA256).

    Corresponds to Echo models.py's content_hash field.
    64-bit collision probability is negligible at million-record scale.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the knowledge base, creating the knowledge table.

    Key design: UNIQUE INDEX on content_hash —
    deduplication is enforced by the SQLite engine, not application logic.
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
    """Batch insert, one transaction per batch, per-item IntegrityError handling.

    Corresponds to Echo store.py's bulk_insert() pattern:
    - BEGIN/COMMIT per batch
    - Per-item try/except IntegrityError
    - Returns insert statistics (new, skipped duplicates, failed)

    Args:
        conn: Database connection
        items: [{"content": "...", "source": "...", "tags": [...]}, ...]
        batch_size: Items per batch
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
                # Duplicate content, silently skip
                stats["skipped"] += 1
            except Exception:
                stats["failed"] += 1
        conn.commit()

    return stats


def dry_run_scan(paths: list[str]) -> list[dict]:
    """Dry-run mode: scan files without inserting, return report.

    Corresponds to Echo zim_ingest.py's dry_run=True mode.
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


# json module needed (built-in)
import json


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Content-hash dedup import tool")
    parser.add_argument("--input", nargs="+", required=True, help="Input files/directories")
    parser.add_argument("--db", default="knowledge.db", help="SQLite database path")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (no actual import)")
    args = parser.parse_args()

    if args.dry_run:
        results = dry_run_scan(args.input)
        print(f"Scan results: {len(results)} file(s)")
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
        print(f"Import complete: {stats['inserted']} inserted, {stats['skipped']} duplicates skipped, {stats['failed']} failed")
        conn.close()
