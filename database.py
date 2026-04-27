import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  order_type TEXT,
                  section TEXT,
                  topic TEXT,
                  file_id TEXT,
                  status TEXT)''')
    conn.commit()
    conn.close()
def init_db():
    import sqlite3
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    
    # Eski jadvallaringiz (orders va h.k) shu yerda turadi, tegmaysiz.
    # Masalan: cursor.execute('''CREATE TABLE IF NOT EXISTS orders...''')
    
    # YANGI QO'SHILADIGAN JADVAL:
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
def save_order(user_id, username, order_type, section, topic, file_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, username, order_type, section, topic, file_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, username, order_type, section, topic, file_id, "pending"))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_status(order_id, status):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

def get_order(order_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = c.fetchone()
    conn.close()
    return order

def get_all_users():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id FROM orders")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_all_users_details():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id, username FROM orders")
    users = c.fetchall()
    conn.close()
    return users

# YANGI: Mijozning tasdiqlangan fayllarini olish
def get_user_purchases(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT topic, file_id FROM orders WHERE user_id=? AND status='approved'", (user_id,))
    purchases = c.fetchall()
    conn.close()
    return purchases

# YANGI: Admin uchun moliyaviy statistika
def get_statistics():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT user_id) FROM orders")
    total_users = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(id) FROM orders WHERE status='approved'")
    approved_orders = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(id) FROM orders WHERE status='pending'")
    pending_orders = c.fetchone()[0] or 0
    conn.close()
    return total_users, approved_orders, pending_orders
def add_purchase(user_id, topic, file_id):
    conn = sqlite3.connect("bot.db") # yoki bazangiz nomi qanday bo'lsa shunday
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO purchases (user_id, topic, file_id)
        VALUES (?, ?, ?)
    ''', (user_id, topic, file_id))
    conn.commit()
    conn.close()