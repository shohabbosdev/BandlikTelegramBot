from typing import List
import re

def safe_cell(row: List[str], idx: int) -> str:
    """Index dan tashqarida bo'lsa yoki bo'sh bo'lsa '' qaytaradi."""
    try:
        v = row[idx]
    except Exception:
        return ""
    if v is None:
        return ""
    return str(v).strip()

def escape_md(text: str) -> str:
    """Markdown uchun minimal escape (asterisk, underscore, backtick)."""
    if text is None:
        return ""
    return str(text).replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")

async def split_and_send_text(chat_id, text, context, limit: int = 3900):
    """Uzoq matnni Telegram limitiga mos bo'lib bo'lib yuboradi."""
    parts = []
    if len(text) <= limit:
        parts = [text]
    else:
        cur = []
        cur_len = 0
        for line in text.splitlines(keepends=True):
            if cur_len + len(line) > limit:
                parts.append("".join(cur))
                cur = [line]
                cur_len = len(line)
            else:
                cur.append(line)
                cur_len += len(line)
        if cur:
            parts.append("".join(cur))

    for p in parts:
        await context.bot.send_message(chat_id=chat_id, text=p, parse_mode="Markdown")
