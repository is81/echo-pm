#!/usr/bin/env python3
"""Lesson capture helper.

Derived from Project Echo's three-pathway learning pattern:
conversational reflection + tool learning + autonomous exploration → shared _extract_knowledge() engine

Usage:
    python capture.py --channel reflection --input notes.md
    python capture.py --channel practice --input "How we solved the K8s deployment issue..."

Dependencies: Python 3.8+ (zero external dependencies).
Note: Actual LLM extraction is performed by Claude Code at skill runtime.
This script handles post-extraction storage and deduplication.
"""

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


# Channel weight mapping (corresponds to Echo's three-pathway base_weight)
CHANNEL_WEIGHTS = {
    "reflection": 0.4,    # Conversational reflection
    "practice": 0.45,     # Tool/practice learning
    "exploration": 0.35,  # Autonomous exploration
}


def content_hash(text: str) -> str:
    """First 16 hex characters of SHA256."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the lesson database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'reflection',
            channel TEXT DEFAULT 'reflection',
            base_weight REAL DEFAULT 0.4,
            tags TEXT DEFAULT '[]',
            related_to TEXT DEFAULT '[]',
            extracted_at REAL DEFAULT (UNIXEPOCH())
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_lesson_hash
        ON lessons(content_hash)
    """)
    conn.commit()
    return conn


def insert_lesson(conn: sqlite3.Connection, content: str,
                  channel: str = "reflection",
                  tags: list[str] = None,
                  related_to: list[str] = None) -> dict:
    """Insert a lesson (auto-dedup)."""
    weight = CHANNEL_WEIGHTS.get(channel, 0.4)

    try:
        conn.execute("""
            INSERT OR IGNORE INTO lessons
            (content_hash, content, channel, base_weight, tags, related_to)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            content_hash(content),
            content,
            channel,
            weight,
            json.dumps(tags or [], ensure_ascii=False),
            json.dumps(related_to or [], ensure_ascii=False),
        ))
        conn.commit()
        if conn.total_changes > 0:
            return {"status": "inserted", "weight": weight}
        else:
            return {"status": "duplicate"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def batch_insert_lessons(conn: sqlite3.Connection,
                         lessons: list[dict]) -> dict:
    """Batch insert lessons, returning statistics."""
    stats = {"inserted": 0, "duplicates": 0, "errors": 0}

    conn.execute("BEGIN")
    for lesson in lessons:
        result = insert_lesson(
            conn,
            lesson["content"],
            lesson.get("channel", "reflection"),
            lesson.get("tags"),
            lesson.get("related_to"),
        )
        if result["status"] == "inserted":
            stats["inserted"] += 1
        elif result["status"] == "duplicate":
            stats["duplicates"] += 1
        else:
            stats["errors"] += 1
    conn.commit()

    return stats


def list_recent_lessons(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """List recent lessons."""
    rows = conn.execute("""
        SELECT id, content, channel, base_weight, tags, extracted_at
        FROM lessons
        ORDER BY extracted_at DESC
        LIMIT ?
    """, (limit,)).fetchall()

    return [
        {
            "id": r[0],
            "content": r[1],
            "channel": r[2],
            "weight": r[3],
            "tags": json.loads(r[4]) if r[4] else [],
            "time": datetime.fromtimestamp(r[5]).isoformat() if r[5] else "",
        }
        for r in rows
    ]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lesson capture helper")
    parser.add_argument("--channel", choices=["reflection", "practice", "exploration"],
                        default="reflection", help="Capture channel")
    parser.add_argument("--input", type=str, help="Input text (or file path)")
    parser.add_argument("--db", default="lessons.db", help="Lesson DB path")
    parser.add_argument("--list", action="store_true", help="List recent lessons")
    parser.add_argument("--tags", type=str, help="Comma-separated tags")
    args = parser.parse_args()

    conn = init_db(args.db)

    if args.list:
        lessons = list_recent_lessons(conn)
        print(f"Recent {len(lessons)} lessons:\n")
        for l in lessons:
            tags_str = f" [{', '.join(l['tags'])}]" if l['tags'] else ""
            print(f"[{l['channel']}] (w={l['weight']}) {l['content'][:100]}..."
                  f"{tags_str}")
    elif args.input:
        # Read input
        input_path = Path(args.input)
        if input_path.is_file():
            text = input_path.read_text(encoding="utf-8", errors="replace")
        else:
            text = args.input  # Direct text

        tags = args.tags.split(",") if args.tags else []

        # Note: Actual LLM extraction is done by Claude Code at skill runtime.
        # This script stores raw text as a marker, awaiting later processing.
        result = insert_lesson(
            conn,
            f"[Pending extraction] {text[:500]}",
            channel=args.channel,
            tags=tags,
        )
        print(f"Lesson {result['status']} (channel={args.channel}, weight={result.get('weight', 'N/A')})")
    else:
        parser.print_help()

    conn.close()
