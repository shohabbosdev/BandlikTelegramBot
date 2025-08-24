import os
import logging
import asyncio
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Import handlers from handlers.py
from handlers import start, search, stat, grafik, inline_pagination_handler

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# Flask app
app = Flask(__name__)

# Global variables
application = None
event_loop = None

def setup_application():
    """Application yaratish va handlerlar qo'shish"""
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(CommandHandler("grafik", grafik))
    app.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    
    return app

async def init_bot():
    """Bot initialization"""
    global application
    application = setup_application()
    await application.initialize()
    await application.start()
    logger.info("Bot ishga tushdi...")

def run_async_in_thread(coro):
    """Alohida thread ichida async kodni ishga tushirish"""
    global event_loop
    
    def run_in_thread():
        global event_loop
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(coro)
    
    thread = threading.Thread(target=run_in_thread)
    thread.daemon = True
    thread.start()
    thread.join()

def schedule_coroutine(coro):
    """Coroutine ni mavjud event loop ga qo'shish"""
    global event_loop
    if event_loop and event_loop.is_running():
        # Thread-safe ravishda task qo'shish
        future = asyncio.run_coroutine_threadsafe(coro, event_loop)
        try:
            future.result(timeout=30)  # 30 sekund timeout
        except Exception as e:
            logger.error(f"Coroutine execution error: {e}")
    else:
        logger.error("Event loop is not running!")

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook handler"""
    try:
        data = request.get_json(force=True)
        if not data:
            return "No data received", 400
        
        update = Update.de_json(data, application.bot)
        if not update:
            return "Invalid update", 400
        
        # Update ni async ravishda qayta ishlash
        schedule_coroutine(application.process_update(update))
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return "Error", 500

@app.route("/")
def index():
    """Health check endpoint"""
    return "🤖 Telegram Bot is running! ✅", 200

@app.route("/health")
def health():
    """Detailed health check"""
    try:
        status = {
            "bot": "running" if application else "not initialized",
            "loop": "running" if event_loop and event_loop.is_running() else "stopped"
        }
        return status, 200
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    try:
        # Bot initialization
        logger.info("Initializing bot...")
        run_async_in_thread(init_bot())
        logger.info("Bot initialized successfully!")
        
        # Flask server
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
        
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
