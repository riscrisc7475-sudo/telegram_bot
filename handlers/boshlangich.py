from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from config import PRICE, CARD_NUMBER
from database import save_order

B_WAIT_TOPIC, B_WAIT_PAYMENT = range(5, 7)

async def boshlangich_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🏫 <b>Boshlang'ich ta'lim bo'limi (Maxsus Buyurtma)</b>\n\n"
        "Bu bo'limda materiallar sizning arizangizga asosan <b>maxsus 2 soat ichida</b> tayyorlab beriladi.\n\n"
        "✍️ Iltimos, <b>Sinf, Fan va Mavzu nomini</b> bitta xabarda to'liq yozib yuboring.\n"
        "<i>Masalan: 3-sinf, Ona tili, Ot so'z turkumi</i>"
    )
    keyboard = [[InlineKeyboardButton("🏠 Bosh menyuga qaytish", callback_data="back_to_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return B_WAIT_TOPIC

async def b_receive_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["b_topic_text"] = update.message.text
    keyboard = [[InlineKeyboardButton("🏠 Bosh menyuga qaytish", callback_data="back_to_main")]]
    text = (
        f"✅ Arizangiz qabul qilindi!\n\n"
        f"💳 Xizmat narxi: <b>{PRICE:,} so'm</b>\n"
        f"📌 Karta raqami: <code>{CARD_NUMBER}</code>\n\n"
        f"To'lovni amalga oshirib, <b>to'lov chekini (skrinshot)</b> shu yerga yuboring 👇"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    return B_WAIT_PAYMENT

async def b_receive_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import ADMIN_GROUP_ID
    user = update.message.from_user
    topic_text = context.user_data.get("b_topic_text", "Yozilmadi")

    order_id = save_order(
        user_id=user.id,
        username=user.username or user.first_name,
        order_type="boshlangich",
        section="Maxsus Buyurtma",
        topic=topic_text,
        file_id="CUSTOM_ORDER"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"b_approve_{order_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")
        ]
    ])

    caption = (
        f"🆕 <b>YANGI MAXSUS BUYURTMA</b>\n\n"
        f"👤 Mijoz: @{user.username or user.first_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"✍️ Buyurtma:\n<b>{topic_text}</b>\n\n"
        f"📋 Buyurtma №: {order_id}\n\n"
        f"⚠️ Fayl tayyor bo'lgach:\n"
        f"<code>/fayl {user.id}</code> deb hujjat bilan yuboring!"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await update.message.reply_text(
        "✅ Chekingiz va arizangiz adminlarimizga yuborildi!\nKuting... ⏳"
    )
    return ConversationHandler.END