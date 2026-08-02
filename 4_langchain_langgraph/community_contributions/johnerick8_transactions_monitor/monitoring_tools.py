from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from rapidfuzz import fuzz
import json
import sqlite3
from datetime import datetime

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

DB_PATH = "compliance.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            amount REAL,
            currency TEXT,
            decision TEXT,
            risk_score REAL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()



with open("sanctions_list.json", "r") as f:
    SANCTIONS_LIST = json.load(f)


def push_notification(text: str):
    requests.post(
        pushover_url,
        data={
            "token": pushover_token,
            "user": pushover_user,
            "message": text,
        },
    )
    return "Notification sent"


def check_sanctions(name: str):
    threshold = 85
    matches = []

    for entry in SANCTIONS_LIST:
        score = fuzz.ratio(name.lower(), entry["name"].lower())

        if score >= threshold:
            matches.append({
                "name": entry["name"],
                "score": score,
                "reason": entry["reason"],
                "date_added": entry["date_added"]
            })

    if matches:
        return {
            "status": "match",
            "matches": matches
        }

    return {"status": "clear"}

def save_compliance_result(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO compliance_records (
            user_id, name, amount, currency, decision, risk_score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("user_id"),
        data.get("name"),
        data.get("amount"),
        data.get("currency"),
        data.get("decision"),
        data.get("risk_score"),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

    return {"status": "saved"}


def get_transaction_history(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, name, amount, currency, decision, risk_score, created_at
        FROM compliance_records
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return {
        "count": len(rows),
        "transactions": [dict(row) for row in rows]
    }


def velocity_check(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as count
        FROM compliance_records
        WHERE user_id = ?
    """, (user_id,))

    count = cursor.fetchone()["count"]
    conn.close()

    if count > 5:
        return {"risk": "high", "reason": "high transaction velocity"}
    return {"risk": "low"}


def get_tools():
    return [
        Tool(
            name="check_sanctions",
            func=check_sanctions,
            description="Check if a person or entity is on a sanctions list using fuzzy matching"
        ),
        Tool(
            name="get_transaction_history",
            func=get_transaction_history,
            description="Retrieve past transactions for a user from the database"
        ),
        Tool(
            name="velocity_check",
            func=velocity_check,
            description="Check if user has unusually high transaction activity from the database"
        ),
        Tool(
            name="save_compliance_result",
            func=save_compliance_result,
            description="Save the compliance decision and transaction details to the database"
        ),
        Tool(
            name="send_push_notification",
            func=push_notification,
            description="Send a push notification with the compliance result to the user via Pushover"
        ),
    ]