import json, sqlite3, os, datetime as dt
from contextlib import contextmanager

DB_PATH = os.getenv("AUDITOR_DB_PATH", os.path.join(os.path.dirname(__file__), "auditor.sqlite"))

@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with connect() as c:
        cur = c.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            fetched_at TEXT,
            input_chars INTEGER,
            readability_json TEXT,
            seo_json TEXT,
            tone_json TEXT,
            plagiarism_json TEXT,
            overall_grade TEXT,
            report_md TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT,
            level TEXT,
            tstamp TEXT,
            message TEXT
        )
        """)


def write_log(tag: str, level: str, message: str):
    with connect() as c:
        c.execute("INSERT INTO logs(tag, level, tstamp, message) VALUES (?,?,?,?)",
                  (tag, level, dt.datetime.utcnow().isoformat(), message))


def write_audit(row: dict) -> int:
    with connect() as c:
        cur = c.cursor()
        cur.execute("""
            INSERT INTO audits(url,title,fetched_at,input_chars,readability_json,seo_json,tone_json,plagiarism_json,overall_grade,report_md)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            row.get("url"),
            row.get("title"),
            row.get("fetched_at"),
            row.get("input_chars", 0),
            json.dumps(row.get("readability", {})),
            json.dumps(row.get("seo", {})),
            json.dumps(row.get("tone", {})),
            json.dumps(row.get("plagiarism", {})),
            row.get("overall_grade"),
            row.get("report_md", "")
        ))
        return cur.lastrowid


def list_audits(limit: int = 25):
    with connect() as c:
        cur = c.cursor()
        cur.execute("SELECT id,url,title,fetched_at,overall_grade,input_chars FROM audits ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]


def get_audit(audit_id: int):
    with connect() as c:
        cur = c.cursor()
        cur.execute("SELECT * FROM audits WHERE id=?", (audit_id,))
        r = cur.fetchone()
        if not r:
            return None
        cols = [d[0] for d in cur.description]
        row = dict(zip(cols, r))
        
        for k in ("readability_json", "seo_json", "tone_json", "plagiarism_json"):
            if row.get(k):
                row[k] = json.loads(row[k])
        return row


init_db()
