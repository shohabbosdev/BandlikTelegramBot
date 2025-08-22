from environs import env

env.read_env()

TOKEN = env("BOT_TOKEN")
SHEET_ID=env("SHEET_ID")
WORKSHEET_TITLE=env("WORKSHEET_TITLE")
REQUIRED_STATUS = env("REQUIRED_STATUS")