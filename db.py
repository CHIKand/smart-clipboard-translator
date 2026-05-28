"""SQLite 历史记录管理"""

import os
import sqlite3
from datetime import datetime

DB_DIR = os.path.join(os.getenv('APPDATA', ''), 'SmartClipboardTranslator')
DB_PATH = os.path.join(DB_DIR, 'history.db')


def _get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库表"""
    conn = _get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            original_text TEXT NOT NULL,
            translated_text TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def add_record(original_text: str, translated_text: str) -> None:
    """添加一条翻译记录"""
    conn = _get_connection()
    conn.execute(
        'INSERT INTO translations (timestamp, original_text, translated_text) VALUES (?, ?, ?)',
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), original_text, translated_text),
    )
    conn.commit()
    conn.close()


def get_all_records(limit: int = 200) -> list[dict]:
    """获取所有记录，按时间倒序"""
    conn = _get_connection()
    rows = conn.execute(
        'SELECT * FROM translations ORDER BY id DESC LIMIT ?', (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_records(keyword: str, limit: int = 100) -> list[dict]:
    """搜索包含关键词的记录"""
    conn = _get_connection()
    pattern = f'%{keyword}%'
    rows = conn.execute(
        'SELECT * FROM translations WHERE original_text LIKE ? OR translated_text LIKE ? ORDER BY id DESC LIMIT ?',
        (pattern, pattern, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_record_count() -> int:
    """获取记录总数"""
    conn = _get_connection()
    row = conn.execute('SELECT COUNT(*) as cnt FROM translations').fetchone()
    conn.close()
    return row['cnt']


def delete_record(record_id: int) -> None:
    """删除指定记录"""
    conn = _get_connection()
    conn.execute('DELETE FROM translations WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
