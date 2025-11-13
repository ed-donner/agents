import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
import json
from .config import config


def get_db_connection():
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metric_type TEXT NOT NULL,
            value REAL NOT NULL,
            status TEXT DEFAULT 'normal',
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_status (
            agent_name TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            last_run DATETIME DEFAULT CURRENT_TIMESTAMP,
            run_count INTEGER DEFAULT 0,
            error_message TEXT
        )
    """)

    conn.commit()
    conn.close()


def write_system_metric(metric_type: str, value: float, status: str = "normal", metadata: dict = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    metadata_json = json.dumps(metadata) if metadata else None
    cursor.execute("""
        INSERT INTO metrics (metric_type, value, status, metadata)
        VALUES (?, ?, ?, ?)
    """, (metric_type, value, status, metadata_json))
    conn.commit()
    conn.close()


def get_recent_metrics(limit: int = 50, metric_type: str = None) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM metrics"
    params = []
    if metric_type:
        query += " WHERE metric_type = ?"
        params.append(metric_type)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "metric_type": row["metric_type"],
            "value": row["value"],
            "status": row["status"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None
        }
        for row in rows
    ]


def create_alert(alert_id: str, title: str, message: str, severity: str, metadata: dict = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    metadata_json = json.dumps(metadata) if metadata else None
    try:
        cursor.execute("""
            INSERT INTO alerts (alert_id, title, message, severity, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (alert_id, title, message, severity, metadata_json))
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute("""
            UPDATE alerts
            SET title = ?, message = ?, severity = ?, status = 'active',
                resolved_at = NULL, metadata = ?
            WHERE alert_id = ?
        """, (title, message, severity, metadata_json, alert_id))
        conn.commit()
    conn.close()


def resolve_alert(alert_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alerts
        SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
        WHERE alert_id = ?
    """, (alert_id,))
    conn.commit()
    conn.close()


def get_active_alerts() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM alerts
        WHERE status = 'active'
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "alert_id": row["alert_id"],
            "title": row["title"],
            "message": row["message"],
            "severity": row["severity"],
            "created_at": row["created_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None
        }
        for row in rows
    ]


def update_agent_status(agent_name: str, status: str, error_message: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT run_count FROM agent_status WHERE agent_name = ?", (agent_name,))
    row = cursor.fetchone()
    if row:
        new_count = row["run_count"] + 1 if status == "completed" else row["run_count"]
        cursor.execute("""
            UPDATE agent_status
            SET status = ?, last_run = CURRENT_TIMESTAMP, run_count = ?, error_message = ?
            WHERE agent_name = ?
        """, (status, new_count, error_message, agent_name))
    else:
        cursor.execute("""
            INSERT INTO agent_status (agent_name, status, run_count, error_message)
            VALUES (?, ?, ?, ?)
        """, (agent_name, status, 1 if status == "completed" else 0, error_message))
    conn.commit()
    conn.close()


def get_agent_status(agent_name: str = None) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    if agent_name:
        cursor.execute("SELECT * FROM agent_status WHERE agent_name = ?", (agent_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "agent_name": row["agent_name"],
                "status": row["status"],
                "last_run": row["last_run"],
                "run_count": row["run_count"],
                "error_message": row["error_message"]
            }
        return None
    else:
        cursor.execute("SELECT * FROM agent_status ORDER BY last_run DESC")
        rows = cursor.fetchall()
        conn.close()
        return {
            row["agent_name"]: {
                "status": row["status"],
                "last_run": row["last_run"],
                "run_count": row["run_count"],
                "error_message": row["error_message"]
            }
            for row in rows
        }


def get_system_summary() -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT metric_type, COUNT(*) as count, AVG(value) as avg_value
        FROM metrics
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY metric_type
    """)
    metrics_summary = {row["metric_type"]: {"count": row["count"], "avg": row["avg_value"]}
                      for row in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) as count FROM alerts WHERE status = 'active'")
    active_alerts_count = cursor.fetchone()["count"]
    cursor.execute("SELECT agent_name, status FROM agent_status")
    agents = {row["agent_name"]: row["status"] for row in cursor.fetchall()}
    conn.close()
    return {
        "metrics_summary": metrics_summary,
        "active_alerts": active_alerts_count,
        "agents": agents,
        "timestamp": datetime.now().isoformat()
    }


def cleanup_old_data(days: int = 7):
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
    cursor.execute("""
        DELETE FROM alerts
        WHERE status = 'resolved' AND resolved_at < ?
    """, (cutoff,))
    conn.commit()
    conn.close()