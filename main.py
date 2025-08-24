# main.py
import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Import handlers
from handlers import start, search, stat, grafik, inline_pagination_handler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")

# Flask app
app = Flask(__name__)

# Global application variable
application = None

async def create_application():
    """Create and initialize telegram application"""
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(CommandHandler("grafik", grafik))
    app.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    
    await app.initialize()
    await app.start()
    
    return app

# Initialize application on module load
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application = loop.run_until_complete(create_application())
    logger.info("Bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        update = Update.de_json(data, application.bot)
        
        # Create isolated event loop for this request
        def process_update_sync():
            local_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(local_loop)
            try:
                local_loop.run_until_complete(application.process_update(update))
            finally:
                local_loop.close()
        
        # Run in separate thread to avoid loop conflicts
        import threading
        thread = threading.Thread(target=process_update_sync)
        thread.start()
        thread.join(timeout=30)  # 30 second timeout
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    serve(app, host="0.0.0.0", port=port)
