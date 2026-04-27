import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_GROUP_ID, PRICE
from database import save_order, update_status, get_order, get_all_users, get_all_users_details, get_statistics, add_purchase

async def receive_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    topic = context.user_data.get("mtt_topic", "Noma'lum")
    file_id_to_send = context.user_data.get("mtt_file_id")
    order_type = context.user_data.get("order_type", "mtt")
    user_text = context.user_data.get("user_text", "Yozilmadi")

    order_id = save_order(
        user_id=user.id,
        username=user.username or user.first_name,
        order_type=order_type,
        section=context.user_data.get("mtt_group", ""),
        topic=topic,
        file_id=file_id_to_send
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")
        ]
    ])

    caption = (
        f"💰 <b>Yangi to'lov cheki</b>\n\n"
        f"👤 Foydalanuvchi: @{user.username or user.first_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📚 Mavzu: {topic}\n"
        f"✍️ Hafta mavzusi: <b>{user_text}</b>\n"
        f"🗂 Bo'lim: {order_type.upper()}\n"
        f"📋 Buyurtma №: {order_id}"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await update.message.reply_text(
        "✅ Chekingiz adminga yuborildi!\n"
        "Tez orada tekshirib, fayl yuboriladi. Kuting... ⏳"
    )
    return ConversationHandler.END


# 1. BIRINCHI BOSQICH: Tasdiqlash bosilganda xavfsizlik oynasini chiqarish
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace("approve_", ""))

    # Tugmalarni 2-bosqichga o'zgartiramiz
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚠️ Ha, tasdiqlayman", callback_data=f"confirm_approve_{order_id}"),
            InlineKeyboardButton("🔙 Bekor qilish", callback_data=f"cancel_approve_{order_id}")
        ]
    ])
    
    await query.edit_message_reply_markup(reply_markup=keyboard)

# 2. IKKINCHI BOSQICH: Admin rostdan ham tasdiqlasa (Faylni yuborish)
async def admin_confirm_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace("confirm_approve_", ""))
    order = get_order(order_id)

    if not order:
        await query.answer("Buyurtma topilmadi!")
        return

    user_id = order[1]
    topic = order[5]
    file_id = order[6]

    # Mijozga yuborish
    await context.bot.send_document(
        chat_id=user_id,
        document=file_id,
        caption=f"✅ To'lovingiz tasdiqlandi!\n📁 <b>{topic}</b> — mana sizning materialingiz!",
        parse_mode="HTML"
    )

    update_status(order_id, "approved")
    
    await query.edit_message_caption(
        caption=f"📋 Buyurtma №: {order_id}\n\n✅ <b>TASDIQLANDI</b> — Fayl yuborildi!",
        parse_mode="HTML"
    )

# 3. BEKOR QILISH: Admin adashib bosgan bo'lsa, orqaga qaytarish
async def admin_cancel_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace("cancel_approve_", ""))

    # Asosiy tugmalarni qaytaramiz
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")
        ]
    ])
    
    await query.edit_message_reply_markup(reply_markup=keyboard)

    update_status(order_id, "approved")
    
    await query.edit_message_caption(
        caption=f"📋 Buyurtma №: {order_id}\n\n✅ <b>TASDIQLANDI</b> — Fayl yuborildi!",
        parse_mode="HTML"
    )

async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace("reject_", ""))
    order = get_order(order_id)

    if not order:
        return

    user_id = order[1]
    update_status(order_id, "rejected")

    await context.bot.send_message(
        chat_id=user_id,
        text="❌ Afsuski, to'lovingiz tasdiqlanmadi.\n\n"
             "Iltimos, qaytadan to'g'ri chek yuboring yoki savollaringiz bo'lsa @zz6274 bilan bog'laning."
    )
    await query.edit_message_caption(
        caption=f"📋 Buyurtma №: {order_id}\n\n❌ <b>RAD ETILDI</b>",
        parse_mode="HTML"
    )

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ Xato! Foydalanish: <code>/reklama Xabar matni</code>", parse_mode="HTML")
        return

    broadcast_text = " ".join(context.args)
    users = get_all_users()
    
    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=broadcast_text)
            count += 1
        except Exception:
            continue

    await update.message.reply_text(f"✅ Xabar {count} ta foydalanuvchiga muvaffaqiyatli yuborildi!")

async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    users = get_all_users_details()

    if not users:
        await update.message.reply_text("📭 Baza hozircha bo'sh. Mijozlar yo'q.")
        return

    text = f"👥 <b>Barcha foydalanuvchilar ro'yxati</b> (Jami: {len(users)} ta)\n\n"
    for index, user in enumerate(users, 1):
        user_id = user[0]
        username = str(user[1]).replace("<", "").replace(">", "").replace("&", "&amp;")
        text += f"{index}. 🆔 <code>{user_id}</code> | 👤 {username}\n"

    if len(text) > 4000:
        await update.message.reply_text("⚠️ Ro'yxat juda uzun! Bir qismi:\n\n" + text[:3800], parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")

async def send_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Xato: <code>/send ID Xabar</code>", parse_mode="HTML")
        return

    try:
        target_user_id = int(context.args[0])
        message_text = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=target_user_id, text=message_text)
        await update.message.reply_text(f"✅ Xabar yuborildi!")
    except Exception:
        await update.message.reply_text("❌ Xatolik yuz berdi.")

async def bot_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    total_users, approved_orders, pending_orders = get_statistics()
    total_revenue = approved_orders * PRICE

    text = (
        f"📊 <b>Botingiz Moliyaviy Hisoboti</b>\n\n"
        f"👥 Jami mijozlar (bazada): <b>{total_users} ta</b>\n"
        f"✅ Sotilgan fayllar: <b>{approved_orders} ta</b>\n"
        f"⏳ Kutayotgan to'lovlar: <b>{pending_orders} ta</b>\n\n"
        f"💰 <b>Jami ishlangan pul: {total_revenue:,} so'm</b>"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def auto_collect_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    if update.message.document:
        file_name = update.message.document.file_name
        file_id = update.message.document.file_id

        with open("tayyor_idlar.txt", "a", encoding="utf-8") as f:
            f.write(f'"{file_name}": "{file_id}",\n')

        print(f"✅ Saqlandi: {file_name}")

async def b_admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace("b_approve_", ""))
    order = get_order(order_id)

    if not order:
        await query.answer("Buyurtma topilmadi!")
        return

    user_id = order[1]
    update_status(order_id, "approved")
    
    await context.bot.send_message(
        chat_id=user_id,
        text="✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
             "Adminlarimiz sizning arizangiz ustida ishlashni boshladi. "
             "Materialingiz maksimal 2 soat ichida shu bot orqali sizga yuboriladi. Kuting ⏱",
        parse_mode="HTML"
    )

    await query.edit_message_caption(
        caption=query.message.caption + "\n\n✅ <b>TASDIQLANDI</b> — Mijozga 2 soat kutish xabari yuborildi!",
        parse_mode="HTML"
    )

# 🌟 YANGILANGAN QUROL: 1 qadamda /fayl ID orqali istalgan narsani yuborish



    # 2. Agar fayl yuborilgan bo'lsa
    if update.message and update.message.document:
        # Oldin /fayl buyrug'i yuborilganmi?
        pending_id = context.user_data.get("pending_file_user_id")
        
        if pending_id:
            file_id = update.message.document.file_id
            target_user_id = pending_id

            try:
                await context.bot.send_document(
                    chat_id=target_user_id, 
                    document=file_id, 
                    caption="🎉 <b>Sizning buyurtmangiz tayyor!</b>\n\nIshonchingiz uchun rahmat!", 
                    parse_mode="HTML"
                )
                
                from database import add_purchase
                add_purchase(target_user_id, "🏫 Maxsus buyurtma", file_id)

                await update.message.reply_text("✅ Fayl muvaffaqiyatli mijozga yuborildi!")
                del context.user_data["pending_file_user_id"]
            except Exception as e:
                await update.message.reply_text(f"❌ Yuborishda xato: {e}")
        else:
            await update.message.reply_text("❌ Avval /fayl ID buyrug'ini yuboring!")

    # 3. Reply usuli - reply orqali fayl yuborish
    if update.message and update.message.reply_to_message:
        from config import ADMIN_GROUP_ID
        if update.effective_chat.id != ADMIN_GROUP_ID:
            return

        original_msg = update.message.reply_to_message
        caption = original_msg.caption or original_msg.text or ""

        import re
        match = re.search(r"🆔 ID:\s*(\d+)", caption)
        target_user_id = int(match.group(1)) if match else None

        if not target_user_id:
            match = re.search(r"ID:\s*(\d+)", caption)
            target_user_id = int(match.group(1)) if match else None

        if target_user_id and update.message.document:
            file_id = update.message.document.file_id
            try:
                await context.bot.send_document(
                    chat_id=target_user_id,
                    document=file_id,
                    caption="🎉 <b>Sizning buyurtmangiz tayyor!</b>\n\nIshonchingiz uchun rahmat!",
                    parse_mode="HTML"
                )
                
                from database import add_purchase
                add_purchase(target_user_id, "🏫 Maxsus buyurtma", file_id)

                await update.message.reply_text("✅ Fayl muvaffaqiyatli mijozga yuborildi!")
            except Exception as e:
                await update.message.reply_text(f"❌ Xato: {e}")

# 🌟 YANGILIK: Fayl kalitlarini txt faylga saqlaydigan funksiya
async def catch_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        file_id = None
        file_name = "Noma'lum"

        if update.message.document:
            file_id = update.message.document.file_id
            file_name = update.message.document.file_name or "Hujjat"
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_name = f"Rasm_{update.message.message_id}"
        elif update.message.video:
            file_id = update.message.video.file_id
            file_name = f"Video_{update.message.message_id}"
        elif update.message.audio:
            file_id = update.message.audio.file_id
            file_name = f"Audio_{update.message.message_id}"

        if file_id:
            try:
                with open("tayyor_idlar.txt", "a", encoding="utf-8") as f:
                    f.write(f'"{file_name}": "{file_id}",\n')
            except Exception as e:
                print(f"⚠️ Txt ga yozishda xato: {e}", flush=True)

            print(f"✅ TXT ga saqlandi: {file_name}", flush=True)
            # 🌟 YANGI QUROL: REPLY ORQALI FAYL YUBORISH
# 🌟 YANGILANGAN QUROL 2: REPLY ORQALI YUBORISH
async def send_file_by_reply(update, context):
    from config import ADMIN_GROUP_ID
    import re
    from database import add_purchase

    # Faqat admin guruhida ishlashi uchun
    if update.effective_chat.id != int(ADMIN_GROUP_ID):
        return

    # Reply bo'lmasa indamaydi
    if not update.message.reply_to_message:
        return

    original_msg = update.message.reply_to_message
    caption = original_msg.caption or original_msg.text or ""

    # Chek ichidan mijoz ID sini topish
    match = re.search(r"ID:\s*(\d+)", caption)
    if not match:
        match = re.search(r"🆔 ID:\s*(\d+)", caption) # Emoji bo'lsa ham ushlaydi
        if not match:
            await update.message.reply_text("❌ Xato: Reply qilingan chekda mijoz ID si topilmadi!")
            return 

    target_user_id = int(match.group(1))

    try:
        # Eng zo'r usul: copy_message (Fayl, rasm, video farqi yo'q)
        await context.bot.copy_message(
            chat_id=target_user_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            caption="🎉 <b>Sizning buyurtmangiz tayyor!</b>\n\nIshonchingiz uchun rahmat! Fayl 'Mening xaridlarim' bo'limiga saqlandi.",
            parse_mode="HTML"
        )
        
        file_id = "Noma'lum"
        if update.message.document:
            file_id = update.message.document.file_id
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            
        add_purchase(target_user_id, "🏫 Maxsus buyurtma", file_id)

        await update.message.reply_text("✅ Muvaffaqiyatli mijozga yuborildi (Reply orqali)!")
    except Exception as e:
        await update.message.reply_text(f"❌ Mijozga yuborishda xato: {e}")
        
        # 2. Xaridlarga saqlash
        add_purchase(target_user_id, "🏫 Maxsus buyurtma", file_id)

        await update.message.reply_text("✅ Fayl muvaffaqiyatli mijozga yuborildi va uning xaridlariga qo'shildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Mijozga yuborishda xato (Balki botni bloklagandir): {e}")
        # 🌟 YANGILANGAN QUROL: 1 qadamda /fayl ID orqali yuborish
async def send_custom_file(update, context):
    from config import ADMIN_GROUP_ID
    import re
    from database import add_purchase

    if update.effective_chat.id != int(ADMIN_GROUP_ID):
        return

    caption = update.message.caption or update.message.text or ""
    
    match = re.search(r'/fayl\s+(\d+)', caption)
    if not match:
        await update.message.reply_text("❌ ID topilmadi! Iltimos, rasm/fayl tagiga: /fayl 123456789 deb yozing.")
        return
        
    target_user_id = int(match.group(1))

    try:
        await context.bot.copy_message(
            chat_id=target_user_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            caption="🎉 <b>Sizning buyurtmangiz tayyor!</b>\n\nIshonchingiz uchun rahmat! Fayl 'Mening xaridlarim' bo'limiga saqlandi.",
            parse_mode="HTML"
        )
        
        file_id = "Noma'lum"
        if update.message.document:
            file_id = update.message.document.file_id
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            
        add_purchase(target_user_id, "🏫 Maxsus buyurtma", file_id)

        await update.message.reply_text("✅ Muvaffaqiyatli mijozga yuborildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Mijozga yuborishda xato: {e}")