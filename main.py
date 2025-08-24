import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 🔹 Log sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# 🔹 Bot token
TOKEN = os.getenv("BOT_TOKEN")

# 🔹 Flask ilovasi
app = Flask(__name__)

# 🔹 PTB Application
application = Application.builder().token(TOKEN).build()


# 🔹 /start komandasi
async def start(update: Update, context):
    await update.message.reply_text("Assalomu alaykum! Bot ishlayapti ✅")


# 🔹 Oddiy matn javobi
async def echo(update: Update, context):
    await update.message.reply_text(f"Siz yozdingiz: {update.message.text}")


# 🔹 Handlerlar
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


# 🔹 Webhook yo‘li
WEBHOOK_PATH = "/webhook"


@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)

        # Har bir POST uchun alohida event loop yaratamiz
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()

    except Exception as e:
        log.exception("Webhook error: %s", e)

    return "OK"


@app.route("/", methods=["GET"])
def home():
    return "Bot ishlayapti ✅"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
