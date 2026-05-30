# -*- coding: utf-8 -*-
"""
把本機 DB 的 tags 匯出成 SQL UPDATE 語句，供 server 端執行。
用法：python scripts/export_tags_sql.py
輸出：scripts/tags_update.sql
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "exam.db"
OUT_PATH = Path(__file__).parent / "tags_update.sql"

conn = sqlite3.connect(DB_PATH)
rows = conn.execute("SELECT id, tags FROM questions WHERE tags IS NOT NULL AND tags != ''").fetchall()
conn.close()

with open(OUT_PATH, "w", encoding="utf-8") as f:
    for qid, tags in rows:
        safe_tags = tags.replace("'", "''")
        f.write(f"UPDATE questions SET tags='{safe_tags}' WHERE id='{qid}';\n")

print(f"匯出完成：{len(rows)} 題有 tags → {OUT_PATH}")
