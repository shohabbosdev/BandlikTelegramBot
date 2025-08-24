import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from handlers import start, stat, search, grafik, inline_pagination_handler
from config import TOKEN

app = Flask(__name__)

# PTB Application (async)
telegram_app = Application.builder().token(TOKEN).build()

# Handlers qo‘shamiz
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("stat", stat))
telegram_app.add_handler(CommandHandler("grafik", grafik))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
telegram_app.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))

# Global event loop yaratamiz
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.post("/webhook")
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    # Yaratilgan loopga task qo‘shamiz
    loop.create_task(telegram_app.process_update(update))
    return "OK", 200

@app.get("/")
def home():
    return "Bot is running!", 200

if __name__ == "__main__":
    # Applicationni initialize/start qilamiz
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
