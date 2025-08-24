import os
import logging
import asyncio
from flask import Flask, request

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)

# --- Muhit o'zgaruvchilari ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render Secrets ga qo'ying
APP_URL   = os.getenv("APP_URL", "https://bandliktelegrambot.onrender.com")
WEBHOOK_PATH = "/webhook"

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("app")

# --- PTB Application ---
application = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()

# --- Handlers (sizning handlers.py dan) ---
from handlers import start, stat, search, grafik, inline_pagination_handler

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stat", stat))
application.add_handler(CommandHandler("grafik", grafik))
application.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

# Xatolarni ko'rish oson bo'lsin
async def on_error(update, context):
    log.exception("Update error: %s", context.error)

application.add_error_handler(on_error)

# --- Webhook ni o'rnatish ---
async def _ensure_webhook():
    url = f"{APP_URL}{WEBHOOK_PATH}"
    info = await application.bot.get_webhook_info()
    if info.url != url:
        log.info("Setting webhook to %s", url)
        await application.bot.set_webhook(url=url, drop_pending_updates=True)
    else:
        log.info("Webhook already set to %s", url)

# Flask app
app = Flask(__name__)

@app.get("/")
def index():
    return "OK"

@app.post(WEBHOOK_PATH)
def webhook():
    try:
        data = request.get_json(force=True, silent=False)
        update = Update.de_json(data, application.bot)
        # PTB async ishlaydi: update'ni event loopga topshiramiz
        asyncio.get_event_loop().create_task(application.process_update(update))
    except Exception as e:
        log.exception("Webhook error: %s", e)
    return "OK"

# Render Flask dev serverida ishga tushganda webhookni set qilamiz
if __name__ == "__main__":
    # Event loop mavjud bo'lmasa yaratib olamiz
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_ensure_webhook())

    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
