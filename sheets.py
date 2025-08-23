import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# .env faylini yuklaymiz
load_dotenv()

# Google Sheets API scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Render’da maxfiy fayl doimiy yo‘li
creds_path = "/etc/secrets/GOOGLE_APPLICATION_CREDENTIALS"

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
