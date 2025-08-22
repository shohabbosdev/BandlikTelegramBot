import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# .env faylini yuklaymiz
load_dotenv()

# Secret fayl yo‘li Render secrets orqali yoki .env orqali

creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

# Credential va gspread client yaratish
creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
GC = gspread.authorize(creds)

# .env fayldan olingan Sheet nomlari
SHEET_ID = os.environ.get("SHEET_ID")
WORKSHEET_TITLE = os.environ.get("WORKSHEET_TITLE")

# Worksheetni ochish
WS = GC.open_by_key(SHEET_ID).worksheet(WORKSHEET_TITLE)

def load_rows():
    return WS.get_all_values()
