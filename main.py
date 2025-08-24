import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")

# Flask app
app = Flask(__name__)

# Telegram Application
application = Application.builder().token(TOKEN).build()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Bot ishga tushdi ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


# 🔹 Webhook route
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))  # ✅ event loop to‘g‘ri ishlaydi
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
    return "ok", 200


# 🔹 Root route
@app.route("/")
def index():
    return "Bot ishlayapti ✅", 200


if __name__ == "__main__":
    # Botni ishga tushirish
    async def run():
        await application.initialize()
        await application.start()
        await application.updater.start_polling()  # polling emas, lekin update queue ishlashi uchun
        logger.info("Bot ishga tushdi...")

    asyncio.run(run())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
