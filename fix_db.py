import sqlite3

def fix_database():
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        
        # purchases jadvalini majburan yaratamiz
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                file_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Baza muvaffaqiyatli yangilandi va 'purchases' jadvali qo'shildi!")
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    fix_database()