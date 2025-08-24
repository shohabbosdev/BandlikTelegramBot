import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Import handlers
try:
    from handlers import start, search, stat, grafik, inline_pagination_handler
    logger.info("Handlers successfully imported")
except Exception as e:
    logger.error(f"Handler import error: {e}")
    raise

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN not found!")

# Flask app
app = Flask(__name__)

# Bot application
application = Application.builder().token(TOKEN).build()

# Add handlers with error handling
try:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stat", stat))
    application.add_handler(CommandHandler("grafik", grafik))
    application.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    logger.info("All handlers added successfully")
except Exception as e:
    logger.error(f"Error adding handlers: {e}")
    raise

async def setup_webhook():
    """Webhook sozlash"""
    try:
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        logger.info(f"Webhook o'rnatildi: {WEBHOOK_URL}/webhook")
    except Exception as e:
        logger.error(f"Webhook sozlashda xato: {e}")

@app.route('/')
def health_check():
    """Health check endpoint"""
    return "Bot is running in webhook mode!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    try:
        # Ma'lumotlarni olish
        update_data = request.get_json()
        logger.info(f"Webhook received update: {update_data}")
        
        if update_data:
            # Update obyektini yaratish
            update = Update.de_json(update_data, application.bot)
            logger.info(f"Processing update: {update.update_id}")
            
            # Async update ni qayta ishlash
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.process_update(update))
            loop.close()
            logger.info(f"Update {update.update_id} processed successfully")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return "Error", 500

@app.route('/health')
def detailed_health():
    """Detailed health check"""
    return {
        "status": "running",
        "mode": "webhook",
        "bot": "active",
        "webhook_url": f"{WEBHOOK_URL}/webhook" if WEBHOOK_URL else None
    }, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    # Application ni initialize qilish
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(application.initialize())
        logger.info("Application initialized successfully")
        
        # Webhook rejimi
        if WEBHOOK_URL:
            logger.info("Webhook rejimida ishga tushmoqda...")
            loop.run_until_complete(setup_webhook())
            logger.info(f"Flask server {port} portda ishga tushmoqda...")
            app.run(host="0.0.0.0", port=port, debug=False)
        else:
            # Polling rejimi
            logger.info("WEBHOOK_URL topilmadi, polling rejimida ishga tushmoqda...")
            loop.run_until_complete(application.run_polling())
    except Exception as e:
        logger.error(f"Main error: {e}", exc_info=True)
    finally:
        loop.close()
