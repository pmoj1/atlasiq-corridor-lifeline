"""Bounded transactional local assessment archive; no recipient or credential storage."""
import hashlib
import json
from pathlib import Path
import sqlite3


def record(path, result, limit=1000):
    payload = json.dumps(result, sort_keys=True, allow_nan=False)
    fingerprint = hashlib.sha256(payload.encode()).hexdigest()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY, fingerprint TEXT UNIQUE, payload TEXT NOT NULL)')
        db.execute('INSERT OR IGNORE INTO assessments(fingerprint,payload) VALUES (?,?)', (fingerprint, payload))
        db.execute('DELETE FROM assessments WHERE id NOT IN (SELECT id FROM assessments ORDER BY id DESC LIMIT ?)', (limit,))
    return fingerprint


def recent(path, limit=100):
    if not Path(path).exists():
        return []
    with sqlite3.connect(path, timeout=10) as db:
        rows = db.execute('SELECT payload FROM assessments ORDER BY id DESC LIMIT ?', (min(max(int(limit), 1), 1000),)).fetchall()
    return [json.loads(row[0]) for row in rows]
