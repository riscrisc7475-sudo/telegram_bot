from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_URL, ADMIN_GROUP_ID
from database import init_db, get_user_purchases

from handlers.mtt import (
    mtt_start, choose_group, choose_topic, choose_subtopic,
    CHOOSE_GROUP, CHOOSE_TOPIC, CHOOSE_SUBTOPIC, WAIT_PAYMENT
)
from handlers.boshlangich import (
    boshlangich_start, b_receive_topic, b_receive_payment,
    B_WAIT_TOPIC, B_WAIT_PAYMENT
)
from handlers.admin import (
    receive_payment_screenshot, admin_approve, admin_reject,
    broadcast_message, users_list, send_to_user, bot_statistics,
    b_admin_approve, send_custom_file, catch_file_id,
    admin_confirm_approve, admin_cancel_approve, send_file_by_reply # Ikkala qurol ham ulandi!
)

# 🔍 DETEKTIV FUNKSIYA
async def xatoni_ushlash(update, context):
    xato_matni = f"❌ DIQQAT, DASTURDA XATO:\n\n{context.error}"
    print(xato_matni)
    if update and update.effective_chat:
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=xato_matni)
        except:
            pass

async def check_subscription(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Kanalni tekshirishda xato: {e}")
        return False

async def start(update: Update, context):
    context.user_data.clear()
    user_id = update.effective_user.id
    is_subscribed = await check_subscription(user_id, context.bot)

    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_sub")]
        ]
        text = "⛔️ <b>Botdan foydalanish uchun rasmiy kanalimizga a'zo bo'lishingiz shart!</b>\n\nIltimos, pastdagi tugma orqali kanalga qo'shiling va tasdiqlang."
        if update.callback_query:
            await update.callback_query.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("🧒 MTT (Maktabgacha)", callback_data="section_mtt")],
        [InlineKeyboardButton("🏫 Boshlang'ich ta'lim", callback_data="section_boshlangich")],
        [InlineKeyboardButton("📥 Mening xaridlarim", callback_data="my_purchases")],
        [InlineKeyboardButton("👨‍💻 Admin bilan bog'lanish", url="https://t.me/zz6274")]
    ]
    text = "Assalomu alaykum! 👋\n\nMalaka oshirish botiga xush kelibsiz. Qaysi bo'limdan material kerak?"

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            pass
        await update.callback_query.answer()
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def my_purchases(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    purchases = get_user_purchases(user_id)

    if not purchases:
        await query.message.reply_text("📭 Sizda hali tasdiqlangan xaridlar yo'q.")
        return

    await query.message.reply_text(
        f"📥 *Sizning xaridlaringiz* ({len(purchases)} ta):\nFayllar yuborilmoqda...",
        parse_mode="Markdown"
    )
    for topic, file_id in purchases:
        try:
            await context.bot.send_document(chat_id=user_id, document=file_id, caption=f"📁 {topic}")
        except Exception:
            pass

async def require_photo(update: Update, context):
    await update.message.reply_text(
        "📸 <b>Iltimos, to'lovni tasdiqlash uchun chekni rasm (skrinshot) ko'rinishida yuboring!</b>",
        parse_mode="HTML"
    )

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    mtt_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(mtt_start, pattern="^section_mtt$")],
        states={
            CHOOSE_GROUP: [CallbackQueryHandler(choose_group, pattern="^mtt_group_")],
            CHOOSE_TOPIC: [CallbackQueryHandler(choose_topic, pattern="^mtt_topic_")],
            CHOOSE_SUBTOPIC: [CallbackQueryHandler(choose_subtopic, pattern="^mtt_sub_")],
            WAIT_PAYMENT: [
                MessageHandler(filters.PHOTO, receive_payment_screenshot),
                MessageHandler(filters.ALL & ~filters.PHOTO & ~filters.COMMAND, require_photo)
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(start, pattern="^back_to_main$")
        ],
        allow_reentry=True
    )

    boshlangich_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(boshlangich_start, pattern="^section_boshlangich$")],
        states={
            B_WAIT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, b_receive_topic)],
            B_WAIT_PAYMENT: [
                MessageHandler(filters.PHOTO, b_receive_payment),
                MessageHandler(filters.ALL & ~filters.PHOTO & ~filters.COMMAND, require_photo)
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(start, pattern="^back_to_main$")
        ],
        allow_reentry=True
    )

    # 1. Zanjirli qafaslar
    app.add_handler(mtt_conv)
    app.add_handler(boshlangich_conv)

    # 2. Asosiy buyruqlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reklama", broadcast_message))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("send", send_to_user))
    app.add_handler(CommandHandler("stat", bot_statistics))
    
    # 3. FAYL YUBORISH QUROLLARI (Reply va /fayl)
    
    # A. Reply usuli: Mijoz chekiga "Reply" qilib fayl tashlaganda
    app.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.GROUPS & filters.REPLY, send_file_by_reply))
    
    # B. /fayl usuli: Fayl YOKI RASM tashlab, izohiga /fayl 1234567 deb yozganda
    app.add_handler(MessageHandler((filters.Document.ALL | filters.PHOTO) & filters.CaptionRegex(r'^/fayl \d+'), send_custom_file))
    
    # C. Arxivchi qorovul (guruhdagi oddiy fayllar uchun)
    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO) & filters.ChatType.GROUPS & ~filters.REPLY,
        catch_file_id
    ))

    # 4. Tugmalar
    app.add_handler(CallbackQueryHandler(start, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(my_purchases, pattern="^my_purchases$"))

    app.add_handler(CallbackQueryHandler(admin_approve, pattern="^approve_"))
    app.add_handler(CallbackQueryHandler(admin_confirm_approve, pattern="^confirm_approve_"))
    app.add_handler(CallbackQueryHandler(admin_cancel_approve, pattern="^cancel_approve_"))
    app.add_handler(CallbackQueryHandler(admin_reject, pattern="^reject_"))
    app.add_handler(CallbackQueryHandler(b_admin_approve, pattern="^b_approve_"))
    
    app.add_error_handler(xatoni_ushlash)
    
    print("✅ Motor ishga tushdi! REPLY va /FAYL tizimlari 100% ulandi!")
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main()