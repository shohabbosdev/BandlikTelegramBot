import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import threading

# Import handlers
from handlers import start, search, stat, grafik, inline_pagination_handler

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not found!")

# Flask app for health check only
app = Flask(__name__)

# Bot application
application = Application.builder().token(TOKEN).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stat", stat))
application.add_handler(CommandHandler("grafik", grafik))
application.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

async def run_bot():
    """Bot polling rejimida ishga tushirish"""
    try:
        # Bot ni ishga tushirish
        logger.info("Bot polling rejimida ishga tushdi!")
        
        # run_polling avtomatik ravishda initialize, start va polling ni boshqaradi
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Bot error: {e}")

def start_bot_thread():
    """Bot ni alohida thread da ishga tushirish"""
    try:
        # Yangi event loop yaratish
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Bot ni ishga tushirish
        loop.run_until_complete(run_bot())
        
    except Exception as e:
        logger.error(f"Bot thread error: {e}")

@app.route('/')
def health_check():
    """Health check endpoint"""
    return "Bot is running in polling mode!", 200

@app.route('/health')
def detailed_health():
    """Detailed health check"""
    return {
        "status": "running",
        "mode": "polling",
        "bot": "active"
    }, 200

if __name__ == "__main__":
    # Bot ni alohida thread da ishga tushirish
    bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
    bot_thread.start()
    
    # Flask health check server
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting health check server on port {port}")
    
    # Flask ni oddiy rejimda ishga tushirish
    app.run(host="0.0.0.0", port=port, debug=False)
