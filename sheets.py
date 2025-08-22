import os
import gspread
from google.oauth2.service_account import Credentials

# JSON faylni env variable orqali o‘qiymiz
creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if not creds_path:
    raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS yo'q!")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

GC = gspread.authorize(creds)
