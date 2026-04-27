import asyncio
from telegram import Bot, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from config import BOT_TOKEN, ADMIN_GROUP_ID

async def setup_menus():
    bot = Bot(token=BOT_TOKEN)
    
    # 1. Hamma oddiy foydalanuvchilar uchun (Faqat Start)
    await bot.set_my_commands(
        [BotCommand("start", "🔄 Bosh menyuga qaytish")],
        scope=BotCommandScopeDefault()
    )
    
    # 2. Faqat ADMIN GURUH uchun (Hamma buyruqlar)
    await bot.set_my_commands(
        [
            BotCommand("fayl", "📁 Mijozga fayl yuborish"),
            BotCommand("stat", "📊 Bot statistikasi"),
            BotCommand("reklama", "📢 Hammaga xabar tarqatish"),
            BotCommand("users", "👥 Foydalanuvchilar ro'yxati"),
            BotCommand("start", "🔄 Bosh menyu")
        ],
        scope=BotCommandScopeChat(chat_id=ADMIN_GROUP_ID)
    )
    
    print("✅ Menyular aqlli tarzda ajratildi!")

if __name__ == "__main__":
    asyncio.run(setup_menus())