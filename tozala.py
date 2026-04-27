import sqlite3

# PASTDAGI RAQAM O'RNIGA O'ZINGIZNING TELEGRAM ID'INGIZNI YOZING
MENING_ID = 5741958428 

def tozalash():
    try:
        conn = sqlite3.connect('bot.db')
        c = conn.cursor()
        
        # 1. "Mening xaridlarim" ro'yxatidan faqat sizni o'chiramiz
        c.execute("DELETE FROM purchases WHERE user_id = ?", (MENING_ID,))
        
        # 2. Test uchun yuborgan eski to'lov cheklari (zakazlar) tarixini ham o'chiramiz
        c.execute("DELETE FROM orders WHERE user_id = ?", (MENING_ID,))
        
        conn.commit()
        conn.close()
        
        print("✅ Sizning test ma'lumotlaringiz bazadan muvaffaqiyatli tozalab tashlandi!")
    except Exception as e:
        print(f"❌ Xato yuz berdi: {e}")

if __name__ == "__main__":
    tozalash()