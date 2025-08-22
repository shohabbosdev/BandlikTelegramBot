import asyncio
import os
import uuid
from collections import Counter
import matplotlib.pyplot as plt

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from config import REQUIRED_STATUS
from sheets import load_rows
from utils import safe_cell, escape_md, split_and_send_text
from formatters import format_card, format_results_block
from keyboards import reply_main_menu, pagination_keyboard

# Ustun indekslari (0-based)
HEMIS_UID    = 0   # A
IDX_HEMIS    = 2   # C
IDX_FIO      = 3   # D
IDX_STAT     = 4   # E
IDX_JSH      = 5   # F
IDX_W        = 22  # W
IDX_LAVOZIM  = 29  # AD
IDX_TASHKILOT= 30  # AE
IDX_SANASI   = 34  # AI
IDX_Guruhi   = 14  # O
IDX_Yunalish = 22  # W

PER_PAGE = 7

# chat_id -> {"query": str, "results": [dict,...], "page_msg_id": int, "page": int}
CHAT_CACHE = {}

# ---------------- Helper: natijalarni qurish ----------------
def build_results_from_rows(rows, query: str):
    """rows = get_all_values() — list of lists. Returns list of dicts."""
    res = []
    q = (query or "").strip().lower()
    if not q:
        return res
    for r in rows[1:]:
        hemisuid = safe_cell(r, HEMIS_UID)
        fio = safe_cell(r, IDX_FIO)
        guruh = safe_cell(r, IDX_Guruhi)
        yunalish = safe_cell(r, IDX_Yunalish)
        hemis = safe_cell(r, IDX_HEMIS)
        jsh = safe_cell(r, IDX_JSH)
        status = safe_cell(r, IDX_STAT)
        if not (fio or hemis or jsh or hemisuid):
            continue
        if q in fio.lower() or q in hemis.lower() or q in jsh.lower() or q in hemisuid.lower():
            item = {
                "hemisuid": hemisuid,
                "guruh": guruh,
                "yunalish": yunalish,
                "fio": fio,
                "hemis": hemis,
                "status": status,
                "jshshir": jsh,
            }
            if REQUIRED_STATUS.lower() in (status or "").lower():
                item["lavozim"]   = safe_cell(r, IDX_LAVOZIM)
                item["tashkilot"] = safe_cell(r, IDX_TASHKILOT)
                item["sanasi"]    = safe_cell(r, IDX_SANASI)
            res.append(item)
    return res

def _results_summary(results):
    total = len(results)
    active = sum(1 for it in results if REQUIRED_STATUS.lower() in (it.get("status","") or "").lower())
    pct = round((active/total*100),2) if total else 0.0
    return total, active, pct

# ---------------- /start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear any previous cache for this chat
    CHAT_CACHE.pop(update.effective_chat.id, None)
    await update.message.reply_text(
        "👋 *Assalomu alaykum!*\n\n"
        "Ism/familiya (qismi bo‘lsa ham), HEMIS ID yoki JSHSHIR yuboring — men jadvaldan topib beraman.\n\n"
        "📌 Pastdagi tugmalardan foydalanishingiz mumkin:",
        parse_mode="Markdown",
        reply_markup=reply_main_menu()
    )

# ---------------- Statistika (/stat yoki tugma) ----------------
async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    rows = load_rows()
    if len(rows) <= 1:
        await context.bot.send_message(chat_id=chat_id, text="❌ *Jadval bo‘sh.*", parse_mode="Markdown")
        return

    total_students = len(rows) - 1
    total_active = 0
    total_per_w = Counter()
    active_per_w = Counter()

    for r in rows[1:]:
        w_val = safe_cell(r, IDX_W) or "Noma'lum"
        status = safe_cell(r, IDX_STAT)
        total_per_w[w_val] += 1
        if REQUIRED_STATUS.lower() in (status or "").lower():
            active_per_w[w_val] += 1
            total_active += 1

    overall_pct = round((total_active / total_students * 100), 2) if total_students else 0.0

    lines = [
        "📊 *Statistika (W ustuni bo‘yicha):*\n",
        f"👥 *Jami talabalar:* {total_students} ta",
        f"🟢 *Faol shartnoma egalari (umumiy):* {total_active} ta ({overall_pct}%)\n",
    ]

    for w_key in sorted(total_per_w.keys(), key=lambda x: (x.lower() if isinstance(x, str) else str(x))):
        tot = total_per_w[w_key]
        act = active_per_w.get(w_key, 0)
        pct_group = round((act / tot * 100), 2) if tot else 0.0
        lines.append(f"▫️ *{escape_md(w_key)}:* jami {tot} | faol: {act} ({pct_group}%)")

    text = "\n".join(lines)

    # Agar oldingi sahifa xabari bo'lsa yechib tashlaymiz
    cache = CHAT_CACHE.get(chat_id)
    if cache and cache.get("page_msg_id"):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=cache["page_msg_id"])
        except Exception:
            pass
        cache["page_msg_id"] = None

    await split_and_send_text(chat_id, text, context)

# ---------------- Qidiruv (foydalanuvchi yuborgan matn) ----------------
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    # Reply tugma bosilganda ularni qidiruv deb o'tkazmaymiz
    if text in ("🔎 Qidiruv", "Qidiruv"):
        await update.message.reply_text("🔎 Qidiruvni boshlash uchun: *ism/familiya (qismi)* yoki *HEMIS ID / JSHSHIR* yuboring.", parse_mode="Markdown")
        return
    if text in ("📊 Statistika", "Statistika"):
        await stat(update, context)
        return
    if text in ("Grafik", "grafik", "Grafik"):
        await grafik(update, context)
        return

    if not text:
        await update.message.reply_text("📝 Iltimos, qidirish uchun matn yuboring.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    rows = load_rows()
    results = build_results_from_rows(rows, text)

    if not results:
        # eski sahifa bo'lsa o'chiramiz
        cache = CHAT_CACHE.get(chat_id)
        if cache and cache.get("page_msg_id"):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=cache["page_msg_id"])
            except:
                pass
            cache["page_msg_id"] = None
        await update.message.reply_text("❌ *Hech qanday ma'lumot topilmadi.*", parse_mode="Markdown")
        return

    # cache ga saqlaymiz
    CHAT_CACHE[chat_id] = {"query": text, "results": results, "page_msg_id": None, "page": 1}
    await send_page(chat_id, context, page=1)

# ---------------- Sahifa yuborish (yangi xabar qilib) ----------------
async def send_page(chat_id: int, context: ContextTypes.DEFAULT_TYPE, page: int):
    cache = CHAT_CACHE.get(chat_id)
    if not cache:
        return
    results = cache["results"]
    total, active, pct = _results_summary(results)
    total_pages = max(1, (len(results) + PER_PAGE - 1)//PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page-1)*PER_PAGE
    end = start + PER_PAGE
    page_items = results[start:end]

    header = (
        f"📋 *Jami natija:* {total} ta\n"
        f"🟢 *Faollar:* {active} ta ({pct}%)\n"
        f"📄 *Sahifa:* {page}/{total_pages}\n\n"
    )
    text = header + format_results_block(page_items)

    # avvalgi sahifa mavjud bo'lsa o'chiramiz
    if cache.get("page_msg_id"):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=cache["page_msg_id"])
        except Exception:
            pass
        cache["page_msg_id"] = None

    sent = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=pagination_keyboard(page, total_pages))
    cache["page_msg_id"] = sent.message_id
    cache["page"] = page
    CHAT_CACHE[chat_id] = cache

# ---------------- Inline pagination (callback) ----------------
async def inline_pagination_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    if not cq:
        return
    await cq.answer()
    data = cq.data  # format: "pg|<page>"
    try:
        _, raw_page = data.split("|", 1)
        page = int(raw_page)
    except Exception:
        return

    chat_id = cq.message.chat.id
    cache = CHAT_CACHE.get(chat_id)
    if not cache:
        return

    # Edit message to new page content
    results = cache["results"]
    total, active, pct = _results_summary(results)
    total_pages = max(1, (len(results) + PER_PAGE - 1)//PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page-1)*PER_PAGE
    end = start + PER_PAGE
    page_items = results[start:end]

    header = (
        f"📋 *Jami natija:* {total} ta\n"
        f"🟢 *Faollar:* {active} ta ({pct}%)\n"
        f"📄 *Sahifa:* {page}/{total_pages}\n\n"
    )
    new_text = header + format_results_block(page_items)

    # Harakat: tahrir qilishga harakat qilamiz
    try:
        await cq.edit_message_text(text=new_text, parse_mode="Markdown", reply_markup=pagination_keyboard(page, total_pages))
        cache["page"] = page
        CHAT_CACHE[chat_id] = cache
    except Exception:
        # agar edit mumkin bo'lmasa, tashqi yuboramiz (o'chirish va yangi yuborish)
        await send_page(chat_id, context, page)

# ---------------- Grafik (Grafik tugmasi yoki /grafik) ----------------
async def grafik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import uuid, os
    from collections import Counter
    from config import IDX_W
    from sheets import load_rows
    from utils import safe_cell
    from telegram import InputFile
    from telegram.constants import ChatAction

    mpl.use("Agg")  # Headless mode, server uchun

    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    rows = load_rows()
    vals = [safe_cell(r, IDX_W) for r in rows[1:] if safe_cell(r, IDX_W)]
    if not vals:
        await context.bot.send_message(chat_id=chat_id, text="❌ Grafik uchun ma'lumot topilmadi.")
        return

    counts = Counter(vals).most_common()
    labels = [str(t[0]) for t in counts]
    data = [t[1] for t in counts]

    # Shrift sozlash
    orig_font = mpl.rcParams["font.family"]
    try:
        mpl.rcParams["font.family"] = "Times New Roman"
    except Exception:
        pass  # fallback default

    # Ranglar
    cmap = plt.cm.get_cmap("tab20", len(labels))
    colors = [cmap(i) for i in range(len(labels))]

    # Rasm o‘lchami: kenglik elementlar soniga qarab, maksimal 40
    width = min(40, max(10, len(labels) * 0.35))
    plt.figure(figsize=(width, 6), dpi=120)
    bars = plt.bar(range(len(labels)), data, color=colors)

    # X o‘qi
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=9)
    plt.ylabel("Soni")
    plt.title("📊 Yo'nalishlar bo'yicha taqsimot grafigi")
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    # Bar ustidagi qiymatlar
    for bar, val in zip(bars, data):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(val), ha="center", va="bottom", fontsize=8, fontweight="bold")

    # Legend
    plt.legend(bars, labels, title="Qiymatlar", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)

    # Fayl nomi va saqlash
    file_name = f"/tmp/grafik_{uuid.uuid4().hex}.png"
    try:
        plt.tight_layout()
        plt.savefig(file_name, bbox_inches="tight")
        plt.close()
        with open(file_name, "rb") as ph:
            await context.bot.send_photo(chat_id=chat_id, photo=ph, caption="📊 W ustunidagi qiymatlar taqsimoti")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Grafik yaratishda xatolik: {e}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        mpl.rcParams["font.family"] = orig_font  # asl shriftga qaytish

