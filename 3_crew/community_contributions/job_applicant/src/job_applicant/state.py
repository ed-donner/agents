import sqlite3
import hashlib
import json
import os
from datetime import datetime
from typing import Optional


class ApplicationStateManager:
    """SQLite-backed state manager for tracking job applications and preventing duplicates."""

    def __init__(self, db_path: str = "./output/applications.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    location TEXT,
                    score REAL,
                    recommendation TEXT,
                    raw_json TEXT,
                    discovered_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_url_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    resume_path TEXT,
                    cover_letter_path TEXT,
                    screenshot_path TEXT,
                    error_message TEXT,
                    applied_at TEXT NOT NULL,
                    FOREIGN KEY (job_url_hash) REFERENCES jobs(url_hash)
                )
            """)
            conn.commit()

    @staticmethod
    def _hash_url(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def save_job(self, job_posting: dict, score: float = 0.0, recommendation: str = "Apply") -> bool:
        """Save a job posting. Returns True if new, False if duplicate."""
        url_hash = self._hash_url(job_posting["url"])
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO jobs (url_hash, url, title, company, platform, location, score, recommendation, raw_json, discovered_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        url_hash,
                        job_posting["url"],
                        job_posting["title"],
                        job_posting["company"],
                        job_posting.get("platform", "unknown"),
                        job_posting.get("location", ""),
                        score,
                        recommendation,
                        json.dumps(job_posting),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def save_application(
        self,
        job_url: str,
        status: str,
        resume_path: Optional[str] = None,
        cover_letter_path: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Record an application attempt."""
        url_hash = self._hash_url(job_url)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO applications (job_url_hash, status, resume_path, cover_letter_path, screenshot_path, error_message, applied_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    url_hash,
                    status,
                    resume_path,
                    cover_letter_path,
                    screenshot_path,
                    error_message,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

    def get_applied_urls(self) -> set:
        """Get all URLs that have been successfully applied to."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT j.url FROM jobs j
                   INNER JOIN applications a ON j.url_hash = a.job_url_hash
                   WHERE a.status = 'submitted'"""
            ).fetchall()
            return {row[0] for row in rows}

    def is_already_applied(self, url: str) -> bool:
        """Check if we've already successfully applied to this job."""
        return url in self.get_applied_urls()

    def get_stats(self) -> dict:
        """Get summary statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            total_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
            submitted = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'submitted'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'failed'").fetchone()[0]
            blocked = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'blocked'").fetchone()[0]

            platform_counts = conn.execute(
                "SELECT platform, COUNT(*) FROM jobs GROUP BY platform"
            ).fetchall()

            return {
                "total_jobs_discovered": total_jobs,
                "total_applications": total_apps,
                "submitted": submitted,
                "failed": failed,
                "blocked": blocked,
                "by_platform": {row[0]: row[1] for row in platform_counts},
            }

    def get_all_applications(self) -> list:
        """Get all application records for display."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT j.title, j.company, j.platform, j.url, j.score,
                          a.status, a.error_message, a.applied_at, a.resume_path, a.cover_letter_path
                   FROM applications a
                   INNER JOIN jobs j ON j.url_hash = a.job_url_hash
                   ORDER BY a.applied_at DESC"""
            ).fetchall()
            return [dict(row) for row in rows]

    def get_matched_jobs(self) -> list:
        """Get all discovered jobs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT title, company, platform, location, url, score, recommendation, discovered_at FROM jobs ORDER BY score DESC"
            ).fetchall()
            return [dict(row) for row in rows]
