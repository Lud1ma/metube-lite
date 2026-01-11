import sqlite3
from datetime import datetime

DB_PATH = "downloads.db"


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                status TEXT,
                filename TEXT,
                created_at TIMESTAMP
            )
        """)


def set_download(video_id, title, status, filename=None):
    with get_db() as db:
        db.execute("""
            INSERT INTO downloads (video_id, title, status, filename, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(video_id)
            DO UPDATE SET
                title=excluded.title,
                status=excluded.status,
                filename=excluded.filename
        """, (
            video_id,
            title,
            status,
            filename,
            datetime.utcnow(),
        ))


def get_all_downloads():
    with get_db() as db:
        rows = db.execute("SELECT * FROM downloads").fetchall()
        return {row["video_id"]: dict(row) for row in rows}


def is_downloaded(video_id):
    with get_db() as db:
        row = db.execute(
            "SELECT status FROM downloads WHERE video_id = ?",
            (video_id,),
        ).fetchone()
        return row and row["status"] == "done"
