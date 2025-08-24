import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Import qilish handlers.py dan
from handlers import start, search, stat, grafik, inline_pagination_handler

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")

# Flask app
app = Flask(__name__)

# Telegram Application - global o'zgaruvchi
application = None

def create_application():
    """Application yaratish va sozlash"""
    global application
    if application is None:
        application = Application.builder().token(TOKEN).build()
        
        # Handlerlarni qo'shish
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stat", stat))
        application.add_handler(CommandHandler("grafik", grafik))
        application.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    
    return application

# 🔹 Webhook route
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        
        # Event loop tekshirish va ishga tushirish
        loop = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Update ni asinxron ravishda qayta ishlash
        if loop.is_running():
            # Agar loop allaqachon ishlayotgan bo'lsa, task yaratamiz
            asyncio.create_task(application.process_update(update))
        else:
            # Agar loop ishlamayotgan bo'lsa, run qilamiz
            loop.run_until_complete(application.process_update(update))
            
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
    
    return "ok", 200

# 🔹 Root route
@app.route("/")
def index():
    return "Bot ishlayapti ✅", 200

async def initialize_bot():
    """Botni asinxron ravishda ishga tushirish"""
    global application
    application = create_application()
    await application.initialize()
    await application.start()
    logger.info("Bot ishga tushdi...")

if __name__ == "__main__":
    # Botni ishga tushirish
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_bot())
    
    # Flask serverni ishga tushirish
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
