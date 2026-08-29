from modules.setup_logging import setup_logging
import gspread
import pandas as pd
from modules.config import Config
from google.oauth2.service_account import Credentials as google_sheets_cred

logger = setup_logging()

# --- Google Sheets Setup ---
def initialize_google_sheets(config: Config) -> tuple[gspread.Client, pd.DataFrame]:

    logger.info("INSIDE INITIALIZE GOOGLE SHEET FUNCTION")
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds = google_sheets_cred.from_service_account_file(config.CREDENTIALS_PATH, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("<your_sheet_name>").get_worksheet(0)
        data = sheet.get_all_values()
        if not data:
            logger.error("No data found in the sheet")
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data[1:], columns=data[0])
            if not df.empty:
                df['Volume (ml)'] = pd.to_numeric(df['Volume (ml)'], errors='coerce').fillna(0).astype(int)
                df['Price (PKR)'] = pd.to_numeric(df['Price (PKR)'].str.replace(",", ""), errors='coerce').fillna(0).astype(float)
                df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
                df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(3.6).astype(float)
            df.to_csv("products.csv", index=False)
            logger.info("Data fetched from Google Sheets and saved to products.csv")
        return client, df
    except Exception as e:
        logger.error(f"Error initializing Google Sheets: {str(e)}")
        return None, pd.DataFrame()