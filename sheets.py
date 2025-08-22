import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# .env faylini yuklaymiz
load_dotenv()

# Google Sheets API scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Secret fayl yo‘li
creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if not creds_path or not os.path.exists(creds_path):
    raise FileNotFoundError("Google credentials.json fayli topilmadi!")

creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
GC = gspread.authorize(creds)

# .env fayldan olingan Sheet nomlari
SHEET_ID = os.environ.get("SHEET_ID")
WORKSHEET_TITLE = os.environ.get("WORKSHEET_TITLE")

if not SHEET_ID or not WORKSHEET_TITLE:
    raise ValueError(".env faylida SHEET_ID yoki WORKSHEET_TITLE topilmadi!")

# Worksheetni ochish
WS = GC.open_by_key(SHEET_ID).worksheet(WORKSHEET_TITLE)

def load_rows():
    return WS.get_all_values()
