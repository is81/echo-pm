#!/usr/bin/env python3
"""经验捕获助手。

源自回响计划的三途径学习模式：
对话反思 + 工具习得 + 自主探索 → 共享 _extract_knowledge() 引擎

用法：
    python capture.py --channel reflection --input notes.md
    python capture.py --channel practice --input "K8s 部署问题的解决方案..."

依赖：Python 3.8+（零外部依赖）。
注意：实际的 LLM 提取由 Claude Code 在 skill 运行时完成，
此脚本处理提取后的入库和去重。
"""

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


# 通道权重映射（对应 Echo 的三途径 base_weight）
CHANNEL_WEIGHTS = {
    "reflection": 0.4,    # 对话反思
    "practice": 0.45,     # 工具/实践习得
    "exploration": 0.35,  # 主动探索
}


def content_hash(text: str) -> str:
    """SHA256 前 16 位十六进制。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def init_db(db_path: str) -> sqlite3.Connection:
    """初始化经验库。"""
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
    """插入一条经验（自动去重）。"""
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
    """批量插入经验，返回统计。"""
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
    """列出最近的经验。"""
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
    parser = argparse.ArgumentParser(description="经验捕获助手")
    parser.add_argument("--channel", choices=["reflection", "practice", "exploration"],
                        default="reflection", help="捕获通道")
    parser.add_argument("--input", type=str, help="输入文本（或文件路径）")
    parser.add_argument("--db", default="lessons.db", help="经验库路径")
    parser.add_argument("--list", action="store_true", help="列出最近的经验")
    parser.add_argument("--tags", type=str, help="逗号分隔的标签")
    args = parser.parse_args()

    conn = init_db(args.db)

    if args.list:
        lessons = list_recent_lessons(conn)
        print(f"最近 {len(lessons)} 条经验：\n")
        for l in lessons:
            tags_str = f" [{', '.join(l['tags'])}]" if l['tags'] else ""
            print(f"[{l['channel']}] (w={l['weight']}) {l['content'][:100]}..."
                  f"{tags_str}")
    elif args.input:
        # 读取输入
        input_path = Path(args.input)
        if input_path.is_file():
            text = input_path.read_text(encoding="utf-8", errors="replace")
        else:
            text = args.input  # 直接文本

        tags = args.tags.split(",") if args.tags else []

        # 注意：真正的 LLM 提取由 Claude Code 在 skill 运行时完成
        # 此脚本将原始文本以标记形式存储，等待后续处理
        result = insert_lesson(
            conn,
            f"[待提取] {text[:500]}",
            channel=args.channel,
            tags=tags,
        )
        print(f"经验已{result['status']}（channel={args.channel}, weight={result.get('weight', 'N/A')}）")
    else:
        parser.print_help()

    conn.close()
