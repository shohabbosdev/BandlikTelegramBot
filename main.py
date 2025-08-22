from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN
from handlers import start, stat, search, grafik, inline_pagination_handler


def main():
    app = Application.builder().token(TOKEN).build()

    # komandalar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(CommandHandler("grafik", grafik))

    # matnli qidiruv (shu handler ichida tugma matnlarini filtrlab olamiz)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

    # inline pagination uchun
    app.add_handler(CallbackQueryHandler(inline_pagination_handler, pattern=r"^pg\|"))

    app.run_polling()

if __name__ == "__main__":
    main()
