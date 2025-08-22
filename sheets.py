import gspread
from google.oauth2.service_account import Credentials
from config import SHEET_ID, WORKSHEET_TITLE

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# credentials.json loyihangiz ildizida bo'lishi kerak
CREDS = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
GC = gspread.authorize(CREDS)
WS = GC.open_by_key(SHEET_ID).worksheet(WORKSHEET_TITLE)

def load_rows():
    """
    Varaqdagi barcha qatorlarni oladi (2D ro'yxat).
    0-qatorda header bo'ladi.
    """
    return WS.get_all_values()
