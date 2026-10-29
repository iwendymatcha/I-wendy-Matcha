import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "matcha_online.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT,
            reset_otp TEXT,
            reset_otp_expiry TIMESTAMP,
            points INTEGER DEFAULT 0,
            role TEXT DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Products table (With name_th, drink_category, has_milk_option)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_th TEXT,
            category TEXT NOT NULL, -- 'drink', 'powder', 'equipment'
            drink_category TEXT DEFAULT '-', -- 'Pure', 'Latte', 'Fusion'
            has_milk_option INTEGER DEFAULT 0, -- 1: Yes, 0: No
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 50,
            description TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            is_bestseller INTEGER DEFAULT 0
        )
    ''')

    # 3. Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            vat_amount REAL NOT NULL,
            discount_amount REAL DEFAULT 0,
            delivery_fee REAL NOT NULL,
            grand_total REAL NOT NULL,
            distance_km REAL NOT NULL,
            customer_lat REAL,
            customer_lng REAL,
            address_note TEXT NOT NULL,
            slip_filename TEXT,
            payment_status TEXT DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
            shipping_status TEXT DEFAULT 'preparing', -- 'preparing', 'delivering', 'completed', 'cancelled'
            points_awarded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 4. Order Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            product_name_th TEXT,
            price_per_unit REAL NOT NULL,
            quantity INTEGER NOT NULL,
            sweetness TEXT DEFAULT '-',
            milk_type TEXT DEFAULT '-',
            total_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # Ensure product_name_th column exists in order_items
    order_items_cols = [c[1] for c in cursor.execute("PRAGMA table_info(order_items)").fetchall()]
    if 'product_name_th' not in order_items_cols:
        cursor.execute("ALTER TABLE order_items ADD COLUMN product_name_th TEXT")

    # Ensure is_bestseller column exists in products
    prod_cols = [c[1] for c in cursor.execute("PRAGMA table_info(products)").fetchall()]
    if 'is_bestseller' not in prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN is_bestseller INTEGER DEFAULT 0")

    # Ensure email and OTP columns exist in users
    user_cols = [c[1] for c in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if 'email' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if 'reset_otp' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_otp TEXT")
    if 'reset_otp_expiry' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_otp_expiry TIMESTAMP")

    # Seed Default Users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_hash = generate_password_hash("admin123")
        customer_hash = generate_password_hash("member123")
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, phone, email, points, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', admin_hash, 'แอดมินร้าน I wendy Matcha', '0958025203', 'admin@iwendymatcha.com', 0, 'admin'))
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, phone, email, points, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('member1', customer_hash, 'Nanami', '0891234567', 'nanami@matcha.com', 0, 'customer'))

    # Seed Products if empty
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_th TEXT,
            category TEXT NOT NULL,
            drink_category TEXT DEFAULT '-',
            has_milk_option INTEGER DEFAULT 0,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 50,
            description TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        seed_default_products(cursor)

    conn.commit()
    conn.close()

def seed_default_products(cursor):
    # 12 Matcha Drinks strictly matching the table:
    # Item ID | Menu Name (EN) | Menu Name (TH) | Price (THB) | Category | Has Milk Option?
    drinks_data = [
        # (id, name, name_th, category, drink_category, has_milk_option, price, stock, description, image_url)
        (1, "Clear Matcha", "ชาใส มัทฉะ", "drink", "Pure", 0, 90.0, 50, 
         "มัทฉะอุจิแท้สกัดเข้มข้น รสชาติสดชื่น หอมกลิ่นอูมามิและสาหร่ายแท้", 
         "/static/images/drinks/clear_matcha.png"),
        
        (2, "Matcha Soda", "มัทฉะ โซดา", "drink", "Pure", 0, 75.0, 45, 
         "มัทฉะเข้มข้นผสานความซ่าสดชื่นของโซดา ดับกระหายคลายร้อน ดื่มง่าย", 
         "/static/images/drinks/matcha_soda.png"),
        
        (3, "Honey Lemon Matcha", "ฮันนี่ เลมอน มัทฉะ", "drink", "Pure", 0, 80.0, 40, 
         "มัทฉะแท้ผสานน้ำผึ้งป่าเดือนห้าและเลมอนสด เปรี้ยวหวานสดชื่นกลมกล่อม", 
         "/static/images/drinks/honey_lemon_matcha.png"),
        
        (4, "Orange Juice Matcha", "มัทฉะ น้ำส้มสด", "drink", "Pure", 0, 100.0, 40, 
         "มัทฉะพรีเมียมท็อปบนน้ำส้มคั้นสดแท้ 100% เปรี้ยวหวานละมุน สดชื่นตื่นตัว", 
         "/static/images/drinks/orange_juice_matcha.png"),
        
        (5, "Matcha Latte", "มัทฉะ ลาเต้", "drink", "Latte", 1, 95.0, 50, 
         "มัทฉะเกรดพิธีการผสมผสานนมสดแท้ นุ่มละมุน หวานมันกลมกล่อมลงตัว", 
         "/static/images/drinks/matcha_latte.png"),
        
        (6, "Creamy Matcha", "ครีมมี่ มัทฉะ", "drink", "Latte", 1, 90.0, 45, 
         "มัทฉะลาเต้สูตรครีมมี่นุ่มละมุนพิเศษ เพิ่มความมันนวลเนียน เข้มข้นเต็มรสสัมผัส", 
         "/static/images/drinks/creamy_matcha.png"),
        
        (7, "Dirty Matcha", "เดอร์ตี้ มัทฉะ", "drink", "Latte", 1, 115.0, 35, 
         "มัทฉะเข้มข้นดับเบิ้ลช็อตราดบนนมสดเย็นจัด แยกชั้นสวยงาม รสเข้มสัมผัสเย็น", 
         "/static/images/drinks/dirty_matcha.png"),
        
        (8, "Matcha Strawberry Latte", "มัทฉะ สตรอว์เบอร์รี ลาเต้", "drink", "Fusion", 1, 105.0, 40, 
         "สตรอว์เบอร์รีเคี่ยวโฮมเมด ท็อปด้วยนมสดและมัทฉะลาเต้เข้มข้น รสสัมผัสเปรี้ยวหวานมัน", 
         "/static/images/drinks/matcha_strawberry_latte.png"),
        
        (9, "Pistachio Matcha", "พิสตาชิโอ มัทฉะ", "drink", "Fusion", 1, 110.0, 40, 
         "มัทฉะเกรดพรีเมียมผสมผสานนมถั่วพิสตาชิโอ หอมนัตตี้ เข้มข้นลุ่มลึกอย่างมีเอกลักษณ์", 
         "/static/images/drinks/pistachio_matcha.png"),
        
        (10, "Matcha Red Bean", "มัทฉะ ถั่วแดง", "drink", "Fusion", 1, 95.0, 35, 
         "มัทฉะลาเต้เสิร์ฟพร้อมถั่วแดงกวนญี่ปุ่น รสสัมผัสหวานมันดั้งเดิมสไตล์เกียวโต", 
         "/static/images/drinks/matcha_red_bean.png"),
        
        (11, "Matcha Boba Fresh Milk", "มัทฉะ นมสดไข่มุก", "drink", "Fusion", 1, 85.0, 50, 
         "มัทฉะนมสดเสิร์ฟพร้อมไข่มุกบราวน์ชูการ์นุ่มหนึบ เคี้ยวเพลิน หอมหวานกำลังดี", 
         "/static/images/drinks/matcha_boba_fresh_milk.png"),
        
        (12, "Matcha Cheese Coconut", "มัทฉะ มะพร้าว ครีมชีส", "drink", "Fusion", 0, 120.0, 35, 
         "น้ำมะพร้าวสดหอมหวานธรรมชาติ ท็อปด้วยมัทฉะและครีมชีสโฟมเนียนนุ่ม หอมมันสดชื่น", 
         "/static/images/drinks/matcha_cheese_coconut.png")
    ]

    for d in drinks_data:
        cursor.execute('''
            INSERT INTO products (id, name, name_th, category, drink_category, has_milk_option, price, stock, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', d)

    # Powders (รูปภาพจริงจากโฟลเดอร์ผงมัทฉะ)
    powders_data = [
        (13, "Uji Marine & Fresh Powder (100g)", "ผงมัทฉะ อุจิ มารีน แอนด์ เฟรช", "powder", "Powder", 0, 350.0, 25, 
         "ผงมัทฉะแท้กลิ่นสาหร่ายสด ยอดหญ้า ถั่วแระ อูมามิเด่นชัด ไม่ฝาดขม เหมาะทำชาใสและผสมผลไม้", 
         "/static/images/powders/uii.png"),
        (14, "Kyoto Nutty & Creamy Powder (100g)", "ผงมัทฉะ เกียวโต นัตตี้ แอนด์ ครีมมี่", "powder", "Powder", 0, 380.0, 30, 
         "โทนนัตตี้ อัลมอนด์อบ เนยสด นุ่มละมุนลิ้น เหมาะที่สุดสำหรับชง Matcha Latte ทุกเมนู", 
         "/static/images/powders/kyoto.png"),
        (15, "Shizuoka Sweet & Floral Powder (100g)", "ผงมัทฉะ ชิซูโอกะ สวีท แอนด์ ฟลอรัล", "powder", "Powder", 0, 390.0, 20, 
         "โทนดอกไม้ขาว ข้าวโพดหวาน หวานธรรมชาติ ดื่มง่าย นุ่มนวลละมุนใจ", 
         "/static/images/powders/shizuoka.png"),
        (16, "Fukuoka Roasty & Earthy Powder (100g)", "ผงมัทฉะ ฟุกุโอกะ โรสต์ แอนด์ เอิร์ธตี้", "powder", "Powder", 0, 320.0, 30, 
         "ผงมัทฉะคั่วเข้มข้น กลิ่นข้าวคั่ว โกโก้ เฮเซลนัท เข้มลึกสู้ส่วนผสมของเบเกอรี่ได้ดีเยี่ยม", 
         "/static/images/powders/fuknoka.png")
    ]
    for p in powders_data:
        cursor.execute('''
            INSERT INTO products (id, name, name_th, category, drink_category, has_milk_option, price, stock, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', p)

    # Ceremonial Matcha Sets (จากโฟลเดอร์เซ็ตอุปกรณ์มัทฉะ)
    matcha_sets_data = [
        (17, "Black Cat Matcha Set", "เซ็ตชงชามัทฉะ ลายแมวดำ", "equipment", "Set", 0, 690.0, 15, 
         "ในเซ็ตประกอบด้วย: ชามชงชาเซรามิกปากรินลายแมวดำ, แปรงไม้ไผ่ Chasen, แท่นวางแปรงเซรามิก และช้อนตักชา Chashaku", 
         "/static/images/3.png"),
        (18, "Pastel Blue Matcha Set", "เซ็ตชงชามัทฉะ ฟ้าพาสเทล", "equipment", "Set", 0, 650.0, 12, 
         "ในเซ็ตประกอบด้วย: ชามชงชาเซรามิกปากรินโทนฟ้าพาสเทล, แปรงไม้ไผ่ Chasen พร้อมแท่นวางเซรามิก และช้อนตักชา Chashaku", 
         "/static/images/2.png"),
        (19, "Star & Moon Matcha Set", "เซ็ตชงชามัทฉะ พระจันทร์และดวงดาว", "equipment", "Set", 0, 590.0, 10, 
         "ในเซ็ตประกอบด้วย: ชามชงชาเซรามิกปากรินประดับพระจันทร์และดวงดาว และแท่นวางแปรงเซรามิกเข้าชุด", 
         "/static/images/4.png"),
        (20, "Sakura Pink Matcha Set", "เซ็ตชงชามัทฉะ ซากุระพิงค์", "equipment", "Set", 0, 690.0, 15, 
         "ในเซ็ตประกอบด้วย: ชามชงชาเซรามิกปากรินสีชมพู, แปรงไม้ไผ่ Chasen ประดับชาร์มผีเสื้อ, แท่นวางแปรงเซรามิกสีชมพู และช้อนตักชา Chashaku", 
         "/static/images/1.png")
    ]
    for s in matcha_sets_data:
        cursor.execute('''
            INSERT INTO products (id, name, name_th, category, drink_category, has_milk_option, price, stock, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', s)

if __name__ == "__main__":
    init_db()
    print("Database Initialized & Synced with Exact 12 Drinks and Milk Options successfully!")
