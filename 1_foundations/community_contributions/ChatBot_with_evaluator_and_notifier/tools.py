import os
import csv
import json
import base64
from dotenv import load_dotenv
from datetime import datetime
import requests


try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False


CSV_FILE = "user_interest.csv"
SHEET_NAME = "UserInterest"


def _get_google_credentials():
    load_dotenv(override=True)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if google_creds_json:
        json_str = base64.b64decode(google_creds_json).decode('utf-8')
        creds_dict = json.loads(json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        print("[info] Loaded Google credentials from environment.")
        return creds

    raise RuntimeError("Google credentials not found.")

def _save_to_google_sheets(email, name, notes):
    creds = _get_google_credentials()
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    row = [datetime.today().strftime('%Y-%m-%d %H:%M'), email, name, notes]
    sheet.append_row(row)
    print(f"[Google Sheets] Recorded: {email}, {name}")

def _save_to_csv(email, name, notes):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Email", "Name", "Notes"])
        writer.writerow([datetime.today().strftime('%Y-%m-%d %H:%M'), email, name, notes])
    print(f"[CSV] Recorded: {email}, {name}")

def _record_user_details(email, name="Name not provided", notes="Not provided"):
    try:
        if GOOGLE_SHEETS_AVAILABLE:
            _save_to_google_sheets(email, name, notes)
        else:
            raise ImportError("gspread not installed.")
    except Exception as e:
        print(f"[Warning] Google Sheets write failed, using CSV. Reason: {e}")
        _save_to_csv(email, name, notes)

    return {"recorded": "ok"}


# --- Minimal Pushover + logging helpers for agent-based RAG ---

def send_pushover_notification(message: str, user_details: dict | None = None):
    """
    Sends a simple Pushover notification if PUSHOVER_TOKEN and PUSHOVER_USER are set.
    Returns a small dict with status info; never raises to keep the app resilient.
    """
    load_dotenv(override=True)
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    if not token or not user:
        print("[pushover] disabled (missing PUSHOVER_TOKEN or PUSHOVER_USER)")
        return {"sent": False, "reason": "missing_creds"}

    try:
        payload = {
            "token": token,
            "user": user,
            "title": "RAG: Unsupported Answer With Empty Context",
            "message": message,
            "priority": 0,
        }

        if user_details:
            try:
                details = {k: v for k, v in user_details.items() if v}
            except Exception:
                details = {}
            if details:
                payload["message"] = payload["message"] + "\n" + json.dumps(details)

        resp = requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=10)
        ok = resp.status_code == 200
        print(f"[pushover] status={resp.status_code} ok={ok}")
        return {"sent": ok, "status_code": resp.status_code}
    except Exception as e:
        print(f"[pushover] error: {e}")
        return {"sent": False, "error": str(e)}


def collect_user_details(name: str | None = None, email: str | None = None) -> dict:
    return {"name": name or "", "email": email or ""}


def log_interaction(query: str, response: str, evaluation: dict, user_details: dict | None = None, csv_path: str = "interactions.csv"):
    try:
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "query", "response", "evaluation", "user_details"])
            writer.writerow([
                datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                query,
                response,
                json.dumps(evaluation, ensure_ascii=False),
                json.dumps(user_details or {}, ensure_ascii=False),
            ])
        print(f"[log] wrote interaction to {csv_path}")
    except Exception as e:
        print(f"[log] error: {e}")


# Back-compat simple notifier expected by existing controller
def notify(title: str, message: str):
    full = f"{title}: {message}" if title else message
    return send_pushover_notification(full)
