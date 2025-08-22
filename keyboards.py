from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def reply_main_menu():
    """Oddiy /start menyusi"""
    keyboard = [
        ["🔎 Qidiruv", "📊 Statistika"],
        ["Grafik"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def pagination_keyboard(current_page: int, total_pages: int):
    """Inline ◀ / ▶ tugmalari. Callback: pg|<page>"""
    if total_pages <= 1:
        return None
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton("◀️", callback_data=f"pg|{current_page-1}"))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton("▶️", callback_data=f"pg|{current_page+1}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None
