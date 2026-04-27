from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import PRICE, CARD_NUMBER
import json

with open("data/mtt_files.json") as f:
    MTT_DATA = json.load(f)

CHOOSE_GROUP, CHOOSE_TOPIC, CHOOSE_SUBTOPIC, WAIT_PAYMENT = range(4)
WAIT_TEXT = 99  # bot.py uchun moslik

async def mtt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()

    keyboard = [[InlineKeyboardButton(g, callback_data=f"mtt_group_{g}")] for g in MTT_DATA.keys()]
    keyboard.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_to_main")])
    text = "📚 MTT bo'limi\n\nQaysi guruh uchun material kerak?"

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_GROUP

async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group = query.data.replace("mtt_group_", "")
    context.user_data["mtt_group"] = group

    topics = MTT_DATA[group]
    keyboard = [[InlineKeyboardButton(t, callback_data=f"mtt_topic_{t}")] for t in topics.keys()]
    keyboard.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_to_main")])

    await query.edit_message_text(
        f"📂 <b>{group}</b> guruhi\n\nQaysi fan/yo'nalish kerak?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return CHOOSE_TOPIC

async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    topic = query.data.replace("mtt_topic_", "")
    context.user_data["mtt_topic"] = topic
    group = context.user_data["mtt_group"]

    subtopics = MTT_DATA[group][topic]
    keyboard = [[InlineKeyboardButton(st, callback_data=f"mtt_sub_{st}")] for st in subtopics.keys()]
    keyboard.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_to_main")])

    await query.edit_message_text(
        f"📘 <b>{topic}</b> ({group})\n\nAynan qaysi mavzu kerak?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return CHOOSE_SUBTOPIC

async def choose_subtopic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subtopic = query.data.replace("mtt_sub_", "")
    group = context.user_data["mtt_group"]
    topic = context.user_data["mtt_topic"]
    file_id = MTT_DATA[group][topic][subtopic]

    context.user_data["mtt_subtopic"] = subtopic
    context.user_data["mtt_file_id"] = file_id
    context.user_data["order_type"] = "mtt"
    context.user_data["mtt_topic"] = f"{topic} → {subtopic}"
    context.user_data["user_text"] = "Matn talab qilinmadi"

    keyboard = [[InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_to_main")]]

    await query.edit_message_text(
        f"✅ Siz tanladingiz: <b>{topic} → {subtopic}</b>\n\n"
        f"💳 To'lov miqdori: <b>{PRICE:,} so'm</b>\n"
        f"📌 Karta raqami: <code>{CARD_NUMBER}</code>\n\n"
        f"To'lovni amalga oshirib, <b>to'lov chekini (skrinshot)</b> shu yerga yuboring 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAIT_PAYMENT