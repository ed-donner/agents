# tools.py

import os
import csv
import json
import base64
from dotenv import load_dotenv
from datetime import datetime


try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False


CSV_FILE = "user_interest.csv"
SHEET_NAME = "UserInterest"


def _get_google_credentials():
    """
    Loads Google credentials either from local file or HF Spaces secret.
    Returns a ServiceAccountCredentials object.
    """
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
