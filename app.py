import os
import re
import math
import time
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "i_wendy_matcha_super_fresh_secure_key_2026"

@app.template_filter('currency')
def currency_filter(val):
    try:
        f = float(val)
        if f.is_integer():
            return f"{int(f):,}"
        return f"{f:,.2f}"
    except (ValueError, TypeError):
        return val

@app.template_filter('comma')
def comma_filter(val):
    try:
        return f"{float(val):,.2f}"
    except (ValueError, TypeError):
        return val

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# พิกัด Central Khon Kaen Campus (จุดเริ่มต้นคำนวณค่าส่ง)
STORE_LAT = 16.4326
STORE_LNG = 102.8236
PROMPTPAY_NUMBER = "0958025203"
STORE_PHONE = "0958025203"
ADMIN_SECRET_KEY = "ImatchaU"

# ==========================================
# ตั้งค่าระบบส่งอีเมลจริงผ่าน Gmail / SMTP
# ==========================================
# โหลดการตั้งค่าจากไฟล์ .env (ถ้ามี)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception as e:
        print("[.env Load Error]", e)

SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'jinxxyz01@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'dxpoyrmkibhthcbu')
SMTP_SENDER_NAME = "I wendy Matcha 🍵"

def send_otp_email(recipient_email, otp):
    """ส่งรหัสยืนยัน OTP ไปยังอีเมลจริงของผู้ใช้งานผ่าน SMTP"""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[SMTP Notice] ยังไม่ได้ตั้งค่า SMTP_EMAIL / SMTP_PASSWORD - รหัส OTP สำหรับ {recipient_email} คือ: {otp}")
        return False, "ยังไม่ได้กำหนดค่า SMTP_EMAIL และ SMTP_PASSWORD"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(f"🍃 รหัสยืนยัน OTP สำหรับตั้งรหัสผ่านใหม่: {otp} - I wendy Matcha", 'utf-8')
        msg['From'] = f"{Header(SMTP_SENDER_NAME, 'utf-8').encode()} <{SMTP_EMAIL}>"
        msg['To'] = recipient_email

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f7faf7; margin: 0; padding: 25px 10px; }}
                .card {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 18px; overflow: hidden; border: 1px solid #e3ede1; box-shadow: 0 10px 25px rgba(0,0,0,0.06); }}
                .card-header {{ background: linear-gradient(135deg, #254117 0%, #3e6b26 100%); color: white; padding: 28px 20px; text-align: center; }}
                .card-body {{ padding: 32px 24px; text-align: center; color: #2d3748; }}
                .otp-box {{ background: #f0f8ee; border: 2px dashed #4b8032; border-radius: 12px; font-size: 34px; font-weight: bold; letter-spacing: 8px; color: #254117; padding: 16px 24px; margin: 24px auto; display: inline-block; }}
                .footer {{ font-size: 12px; color: #a0aec0; text-align: center; padding: 18px; border-top: 1px solid #edf2f7; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="card-header">
                    <h2 style="margin: 0; font-size: 22px;">🍵 I wendy Matcha</h2>
                    <p style="margin: 6px 0 0; font-size: 13px; opacity: 0.9;">ระบบยืนยันตัวตนตั้งรหัสผ่านใหม่</p>
                </div>
                <div class="card-body">
                    <p style="font-size: 15px; line-height: 1.6; margin-top: 0;">สวัสดีค่ะ,<br>คุณได้ส่งคำขอตั้งรหัสผ่านใหม่สำหรับบัญชี I wendy Matcha</p>
                    <p style="font-size: 14px; color: #718096; margin-bottom: 0;">รหัสยืนยัน OTP สำหรับใช้ตั้งรหัสผ่านใหม่ของคุณคือ:</p>
                    <div class="otp-box">{otp}</div>
                    <p style="font-size: 13px; color: #e53e3e; margin: 15px 0 5px;">⏳ รหัส OTP มีอายุการใช้งาน <strong>15 นาที</strong></p>
                    <p style="font-size: 12px; color: #a0aec0; margin: 0;">* หากคุณไม่ได้เป็นผู้ทำรายการนี้ กรุณาเพิกเฉยต่ออีเมลฉบับนี้</p>
                </div>
                <div class="footer">
                    &copy; 2026 I wendy Matcha Online Delivery. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=12)
        server.starttls()
        server.login(SMTP_EMAIL.strip(), SMTP_PASSWORD.strip().replace(' ', ''))
        server.sendmail(SMTP_EMAIL.strip(), recipient_email, msg.as_string())
        server.quit()
        return True, "สำเร็จ"
    except Exception as e:
        print(f"[SMTP Send Error] {e}")
        return False, str(e)

def haversine_distance(lat1, lon1, lat2, lon2):
    """คำนวณระยะทางจริงบนพื้นผิวโลก (กิโลเมตร)"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_shipping(distance_km):
    """
    กติกาค่าส่ง:
    - ระยะทางน้อยกว่าหรือเท่ากับ 3 กม. = ส่งฟรี! (0 บาท)
    - เกิน 3 กม. = คิดเพิ่ม 5 บาท ต่อ กิโลเมตร (คำนวณจากระยะทางส่วนที่เกิน 3 กม.)
    """
    if distance_km <= 3.0:
        return 0.0
    return round(math.ceil(distance_km - 3.0) * 5.0, 2)

# เตรียมฐานข้อมูลเมื่อเริ่มระบบ
init_db()

def get_bestseller_product_ids():
    """ดึงรายชื่อ Product ID สินค้าขายดี (สำหรับแสดงดาว ⭐): จากยอดขายจริง และที่แอดมินตั้งค่าไว้"""
    best_ids = set()
    try:
        conn = get_db()
        # 1. สินค้าที่แอดมินเลือกเป็นขายดี (is_bestseller = 1)
        manual = conn.execute("SELECT id FROM products WHERE is_bestseller = 1").fetchall()
        for r in manual:
            best_ids.add(r['id'])

        # 2. สินค้าที่มียอดสั่งซื้อจริงสูงสุด Top 5
        sales_rows = conn.execute('''
            SELECT oi.product_id, SUM(oi.quantity) as total_qty
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.payment_status = 'verified'
            GROUP BY oi.product_id
            ORDER BY total_qty DESC
            LIMIT 5
        ''').fetchall()
        for r in sales_rows:
            if r['total_qty'] and r['total_qty'] >= 3:
                best_ids.add(r['product_id'])
        conn.close()
    except Exception:
        pass
    return best_ids

@app.context_processor
def global_context():
    """ส่งข้อมูล User, จำนวนตะกร้า และแจ้งเตือนออเดอร์ไปยังทุกหน้า Template อัตโนมัติ"""
    current_user = None
    pending_orders_count = 0
    if 'user_id' in session:
        conn = get_db()
        current_user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        if current_user and current_user['role'] == 'admin':
            pending_orders_count = conn.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'pending'").fetchone()[0]
        conn.close()

    cart = session.get('cart', [])
    cart_total_items = 0 if (current_user and current_user['role'] == 'admin') else sum(item.get('quantity', 1) for item in cart)
    bestseller_ids = get_bestseller_product_ids()
    return dict(
        current_user=current_user,
        cart_total_items=cart_total_items,
        pending_orders_count=pending_orders_count,
        promptpay_number=PROMPTPAY_NUMBER,
        store_phone=STORE_PHONE,
        store_lat=STORE_LAT,
        store_lng=STORE_LNG,
        bestseller_ids=bestseller_ids
    )

# ==========================================
# 1. หน้าร้าน & แคตตาล็อกเมนู
# ==========================================
@app.route('/')
def index():
    category = request.args.get('cat', 'all')
    bestseller_ids = get_bestseller_product_ids()
    conn = get_db()
    if category == 'all':
        products = conn.execute("SELECT * FROM products ORDER BY category, id").fetchall()
    elif category == 'bestseller':
        if bestseller_ids:
            placeholders = ','.join('?' for _ in bestseller_ids)
            products = conn.execute(f"SELECT * FROM products WHERE id IN ({placeholders}) ORDER BY category, id", list(bestseller_ids)).fetchall()
        else:
            products = conn.execute("SELECT * FROM products WHERE is_bestseller = 1 ORDER BY category, id").fetchall()
    elif category in ['Pure', 'Latte', 'Fusion']:
        products = conn.execute("SELECT * FROM products WHERE drink_category = ? ORDER BY id", (category,)).fetchall()
    elif category in ['equipment', 'set']:
        products = conn.execute("SELECT * FROM products WHERE category IN ('equipment', 'set') ORDER BY id").fetchall()
    else:
        products = conn.execute("SELECT * FROM products WHERE category = ? ORDER BY id", (category,)).fetchall()
    
    drinks = conn.execute("SELECT * FROM products WHERE category = 'drink' ORDER BY id").fetchall()
    powders = conn.execute("SELECT * FROM products WHERE category = 'powder' ORDER BY id").fetchall()
    equipments = conn.execute("SELECT * FROM products WHERE category IN ('equipment', 'set') ORDER BY id").fetchall()
    conn.close()

    cart = session.get('cart', [])
    cart_counts = {}
    for item in cart:
        pid = item.get('product_id')
        cart_counts[pid] = cart_counts.get(pid, 0) + item.get('quantity', 0)

    return render_template('index.html', 
                           products=products, 
                           drinks=drinks, 
                           powders=powders, 
                           equipments=equipments,
                           current_cat=category,
                           cart_counts=cart_counts)

# ==========================================
# 2. ระบบสมาชิก & ลืมรหัสผ่าน (รีเซ็ตรหัสผ่านโดยตรง)
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ? OR phone = ? OR email = ?", 
                            (identifier, identifier, identifier)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            flash(f'ยินดีต้อนรับคุณ {user["name"]} สู่ I wendy Matcha 🍃', 'success')

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('ชื่อผู้ใช้ อีเมล หรือรหัสผ่านไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not username or not password or not name or not phone or not email:
            flash('กรุณากรอกข้อมูลให้ครบทุกช่องรวมทั้งอีเมล', 'warning')
            return render_template('register.html', name=name, username=username, phone=phone, email=email)

        # 1. ตรวจสอบเบอร์โทรศัพท์: ต้องเริ่มต้นด้วย 0 และเป็นตัวเลข 10 หลักเท่านั้น
        if not re.match(r'^0\d{9}$', phone):
            flash('เบอร์โทรศัพท์ต้องเริ่มต้นด้วยเลข 0 และเป็นตัวเลข 10 หลักเท่านั้น (เช่น 0812345678)', 'warning')
            return render_template('register.html', name=name, username=username, phone=phone, email=email)

        # 2. ตรวจสอบรูปแบบอีเมล
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('รูปแบบอีเมลไม่ถูกต้อง กรุณาระบุอีเมลที่ถูกต้อง (เช่น yourname@email.com)', 'warning')
            return render_template('register.html', name=name, username=username, phone=phone, email=email)

        # 3. ตรวจสอบความรัดกุมของรหัสผ่าน: ตัวอักษรและตัวเลขรวมกันอย่างน้อย 8 ตัว
        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            flash('❌ รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร และต้องประกอบด้วยตัวอักษรภาษาอังกฤษและตัวเลขรวมกัน', 'danger')
            return render_template('register.html', name=name, username=username, phone=phone, email=email)

        conn = get_db()
        # 4. ตรวจสอบข้อมูลซ้ำแยกแต่ละช่องให้ชัดเจน
        existing_username = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing_username:
            conn.close()
            flash(f'❌ ชื่อผู้ใช้ "{username}" มีผู้ใช้งานแล้ว กรุณาตั้งชื่อผู้ใช้อื่นค่ะ', 'warning')
            return render_template('register.html', name=name, username='', phone=phone, email=email)

        existing_phone = conn.execute("SELECT id FROM users WHERE phone = ?", (phone,)).fetchone()
        if existing_phone:
            conn.close()
            flash(f'❌ เบอร์โทรศัพท์ {phone} นี้เคยลงทะเบียนไว้แล้ว (หากเป็นของคุณ สามารถกด "เข้าสู่ระบบ" หรือ "ลืมรหัสผ่าน" ได้ค่ะ)', 'warning')
            return render_template('register.html', name=name, username=username, phone='', email=email)

        existing_email = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_email:
            conn.close()
            flash(f'❌ อีเมล {email} นี้เคยลงทะเบียนไว้แล้ว (หากเป็นของคุณ สามารถกด "ลืมรหัสผ่าน" ได้ค่ะ)', 'warning')
            return render_template('register.html', name=name, username=username, phone=phone, email='')

        pwd_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, phone, email, points, role)
            VALUES (?, ?, ?, ?, ?, 0, 'customer')
        ''', (username, pwd_hash, name, phone, email))
        new_user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # เข้าสู่ระบบให้อัตโนมัติทันทีหลังสมัครสมาชิก
        session['user_id'] = new_user_id
        session['username'] = username
        session['role'] = 'customer'
        session['name'] = name

        flash(f'🎉 สมัครสมาชิกและเข้าสู่ระบบสำเร็จแล้ว! ยินดีต้อนรับคุณ {name} สู่ I wendy Matcha 🍵', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('ออกจากระบบเรียบร้อยแล้ว แล้วแวะมาจิบมัทฉะใหม่นะคะ 🍵', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """ขั้นตอนที่ 1: สมาชิกกรอกอีเมลเพื่อขอรับรหัส OTP สำหรับตั้งรหัสผ่านใหม่"""
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()

        if not identifier:
            flash('กรุณากรอกอีเมลของคุณ', 'warning')
            return render_template('forgot_password.html')

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ? OR username = ? OR phone = ?", 
                            (identifier.lower(), identifier, identifier)).fetchone()

        if not user or not user['email']:
            conn.close()
            flash('❌ ไม่พบบัญชีผู้ใช้หรืออีเมลนี้ในระบบสมาชิก กรุณาตรวจสอบอีกครั้ง', 'danger')
            return render_template('forgot_password.html', identifier=identifier)

        # สร้างรหัส OTP 6 หลัก และกำหนดเวลาหมดอายุ 15 นาที
        otp = f"{random.randint(100000, 999999)}"
        expiry = datetime.now() + timedelta(minutes=15)

        conn.execute("UPDATE users SET reset_otp = ?, reset_otp_expiry = ? WHERE id = ?", 
                     (otp, expiry.strftime('%Y-%m-%d %H:%M:%S'), user['id']))
        conn.commit()
        conn.close()

        session['reset_user_id'] = user['id']

        # Mask อีเมลเพื่อความปลอดภัย
        parts = user['email'].split('@')
        masked = f"{parts[0][:1]}***{parts[0][-1]}@{parts[1]}" if len(parts) == 2 and len(parts[0]) > 2 else user['email']

        # ส่งอีเมลจริงไปยังอีเมลของผู้ใช้ผ่าน SMTP
        sent, err_msg = send_otp_email(user['email'], otp)
        if sent:
            flash(f'📧 ระบบได้ส่งรหัสยืนยัน OTP 6 หลักไปยังอีเมล {masked} ของคุณเรียบร้อยแล้ว กรุณาตรวจสอบกล่องจดหมาย (Inbox / Spam)', 'success')
        else:
            if not SMTP_EMAIL or not SMTP_PASSWORD:
                flash(f'⚠️ ยังไม่ได้ตั้งค่าบัญชีอีเมลส่งจริง (SMTP) ในระบบ (รหัส OTP จำลองสำหรับทดสอบคือ: {otp}) กรุณาตั้งค่า SMTP_EMAIL และ App Password เพื่อส่งเข้าอีเมลจริงค่ะ', 'warning')
            else:
                flash(f'❌ ไม่สามารถส่งอีเมลไปยัง {masked} ได้: {err_msg} กรุณาตรวจสอบการตั้งค่า SMTP', 'danger')

        return redirect(url_for('reset_password'))

    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """ขั้นตอนที่ 2: กรอกรหัส OTP และตั้งรหัสผ่านใหม่ (ต้องมีตัวอักษรและตัวเลขรวมกัน 8 ตัว)"""
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('กรุณากรอกอีเมลเพื่อขอรับรหัส OTP ก่อนค่ะ', 'warning')
        return redirect(url_for('forgot_password'))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not user:
        return redirect(url_for('forgot_password'))

    parts = (user['email'] or '').split('@')
    masked_email = f"{parts[0][:1]}***{parts[0][-1]}@{parts[1]}" if len(parts) == 2 and len(parts[0]) > 2 else (user['email'] or '')

    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 1. ตรวจสอบรหัส OTP
        if not user['reset_otp'] or user['reset_otp'] != otp:
            flash('❌ รหัส OTP ไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง', 'danger')
            return render_template('reset_password.html', user_id=user_id, masked_email=masked_email)

        # 2. ตรวจสอบเวลาหมดอายุ OTP
        if user['reset_otp_expiry']:
            try:
                exp = datetime.strptime(str(user['reset_otp_expiry'])[:19], '%Y-%m-%d %H:%M:%S')
                if datetime.now() > exp:
                    flash('❌ รหัส OTP นี้หมดอายุแล้ว กรุณาขอรับรหัส OTP ใหม่อีกครั้ง', 'warning')
                    return redirect(url_for('forgot_password'))
            except Exception:
                pass

        # 3. ตรวจสอบรหัสผ่านใหม่ตรงกัน
        if new_password != confirm_password:
            flash('❌ รหัสผ่านใหม่ทั้งสองช่องไม่ตรงกัน', 'danger')
            return render_template('reset_password.html', user_id=user_id, masked_email=masked_email)

        # 4. ตรวจสอบความรัดกุมของรหัสผ่าน: ตัวอักษรและตัวเลขรวมกัน 8 ตัวขึ้นไป
        if len(new_password) < 8 or not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
            flash('❌ รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร และต้องประกอบด้วยตัวอักษรภาษาอังกฤษและตัวเลขรวมกัน', 'danger')
            return render_template('reset_password.html', user_id=user_id, masked_email=masked_email)

        hashed = generate_password_hash(new_password)
        conn = get_db()
        conn.execute("UPDATE users SET password_hash = ?, reset_otp = NULL, reset_otp_expiry = NULL WHERE id = ?", 
                     (hashed, user['id']))
        conn.commit()
        conn.close()

        session.pop('reset_user_id', None)
        flash('✅ เปลี่ยนรหัสผ่านสำเร็จแล้ว! สามารถเข้าสู่ระบบด้วยรหัสผ่านใหม่ได้ทันทีค่ะ', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', user_id=user_id, masked_email=masked_email)

@app.route('/order-status', endpoint='order_status')
@app.route('/profile', endpoint='profile')
def profile():
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบเพื่อติดตามสถานะการสั่งซื้อและดูประวัติคำสั่งซื้อของคุณ', 'info')
        return redirect(url_for('login'))

    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    orders = conn.execute('''
        SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()

    orders_with_items = []
    for ord_row in orders:
        items = conn.execute('''
            SELECT * FROM order_items WHERE order_id = ?
        ''', (ord_row['id'],)).fetchall()
        orders_with_items.append({'order': ord_row, 'items': items})

    conn.close()
    return render_template('profile.html', user=user, orders_data=orders_with_items)

# ==========================================
# 2.5 คู่มือการใช้งานระบบ (User Manual & Docs)
# ==========================================
@app.route('/manual', endpoint='manual')
def manual():
    return render_template('manual.html')

@app.route('/download-manual', endpoint='download_manual')
def download_manual():
    docs_dir = os.path.join(app.root_path, 'static', 'docs')
    filename = 'manual_i_wendy_matcha.docx'
    # Regenerate file if missing
    if not os.path.exists(os.path.join(docs_dir, filename)):
        try:
            import create_docx_manual
            create_docx_manual.build_manual_docx()
        except Exception:
            pass
    return send_from_directory(
        docs_dir, 
        filename, 
        as_attachment=True, 
        download_name='คู่มือการใช้งาน_IwendyMatcha.docx'
    )

# ==========================================
# 3. ระบบตะกร้าสินค้า (Add multiple items)
# ==========================================
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if session.get('role') == 'admin':
        return jsonify({'success': False, 'message': 'บัญชีแอดมินไม่สามารถสั่งซื้อสินค้าได้ กรุณาใช้บัญชีลูกค้าสำหรับการสั่งซื้อ'})

    try:
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'ข้อมูลสินค้าหรือจำนวนไม่ถูกต้อง'})

    if quantity <= 0:
        return jsonify({'success': False, 'message': 'จำนวนสินค้าต้องอย่างน้อย 1 ชิ้น'})

    sweetness = request.form.get('sweetness', 'ปกติ 100%')
    milk_type = request.form.get('milk_type', 'นมสดแท้')

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()

    if not product:
        return jsonify({'success': False, 'message': 'ไม่พบสินค้าในระบบ'})

    # ตรวจสอบสถานะว่าถูกแจ้งหมดชั่วคราวหรือไม่
    if product['is_active'] == 0:
        return jsonify({'success': False, 'message': f'ขออภัย {product["name"]} สินค้าหมดชั่วคราว (Out of Stock)'})

    # ตรวจสอบสต็อกคงเหลือ
    if product['stock'] <= 0:
        return jsonify({'success': False, 'message': f'ขออภัย {product["name"]} สินค้าหมดแล้ว (Sold Out)'})

    cart = session.get('cart', [])
    current_in_cart = sum(item['quantity'] for item in cart if item['product_id'] == product_id)
    unit_text = "แก้ว" if product['category'] == 'drink' else "ชิ้น"

    # เชื่อมโยงสต็อกหลังบ้านกับการสั่งซื้อ: ถ้าในคลังมี 1 ชิ้น ลูกค้าสั่งได้ไม่เกิน 1 ชิ้น
    if current_in_cart >= product['stock']:
        return jsonify({
            'success': False, 
            'message': f'ขออภัยค่ะ {product["name"]} ในคลังมีเพียง {product["stock"]} {unit_text} (คุณใส่ลงตะกร้าครบตามสต็อกแล้ว)',
            'stock': product['stock'],
            'in_cart': current_in_cart,
            'remaining': 0
        })

    if current_in_cart + quantity > product['stock']:
        remaining = max(0, product['stock'] - current_in_cart)
        return jsonify({
            'success': False, 
            'message': f'ขออภัยค่ะ {product["name"]} ในคลังมีเหลือเพียง {product["stock"]} {unit_text} (ในตะกร้ามีแล้ว {current_in_cart} {unit_text} สั่งเพิ่มได้อีกเพียง {remaining} {unit_text})',
            'stock': product['stock'],
            'in_cart': current_in_cart,
            'remaining': remaining
        })

    if product['category'] != 'drink':
        sweetness = '-'
        milk_type = '-'
    elif product['has_milk_option'] == 0:
        milk_type = '-'

    # ตรวจสอบว่ามีรายการเดิมที่ตรงกันทั้งสินค้า ความหวาน และนม หรือไม่
    found = False
    for item in cart:
        if (item['product_id'] == product_id and 
            item.get('sweetness') == sweetness and 
            item.get('milk_type') == milk_type):
            item['quantity'] += quantity
            found = True
            break

    if not found:
        cart.append({
            'product_id': product['id'],
            'name': product['name'],
            'name_th': product['name_th'],
            'category': product['category'],
            'drink_category': product['drink_category'],
            'has_milk_option': product['has_milk_option'],
            'price': product['price'],
            'quantity': quantity,
            'sweetness': sweetness,
            'milk_type': milk_type,
            'image_url': product['image_url']
        })

    session['cart'] = cart
    total_qty = sum(i['quantity'] for i in cart)
    new_in_cart = current_in_cart + quantity
    new_remaining = max(0, product['stock'] - new_in_cart)

    return jsonify({
        'success': True, 
        'message': f'เพิ่ม {product["name"]} ลงตะกร้าแล้ว ({new_in_cart}/{product["stock"]} {unit_text})',
        'total_items': total_qty,
        'product_id': product_id,
        'stock': product['stock'],
        'in_cart': new_in_cart,
        'remaining': new_remaining
    })

@app.route('/cart')
def view_cart():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    cart = session.get('cart', [])
    conn = get_db()
    
    # ซิงค์สต็อกจริงจากฐานข้อมูลกับจำนวนในตะกร้าแบบ Real-time
    updated_cart = []
    cart_modified = False

    for item in cart:
        prod = conn.execute("SELECT * FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        if not prod or prod['is_active'] == 0 or prod['stock'] <= 0:
            cart_modified = True
            flash(f"⚠️ สินค้า {item['name']} ในคลังหมดสต็อกแล้ว ระบบจึงนำออกจากตะกร้าของคุณค่ะ", "warning")
            continue
            
        current_stock = prod['stock']
        item['stock'] = current_stock
        item['is_active'] = prod['is_active']
        
        # ถ้ายอดรวมในตะกร้าเกินสต็อกคงเหลือในคลัง
        if item['quantity'] > current_stock:
            item['quantity'] = current_stock
            cart_modified = True
            unit_text = "แก้ว" if item.get('category') == 'drink' else "ชิ้น"
            flash(f"⚠️ สินค้า {item['name']} ในคลังมีเหลือเพียง {current_stock} {unit_text} ระบบได้ปรับจำนวนในตะกร้าให้ตรงตามสต็อกจริงแล้วค่ะ", "warning")
            
        updated_cart.append(item)
        
    conn.close()
    
    if cart_modified:
        session['cart'] = updated_cart
        cart = updated_cart

    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    # ถอย VAT (ราคารวมภาษีแล้ว)
    before_vat = round(subtotal / 1.07, 2)
    vat_est = round(subtotal - before_vat, 2)
    return render_template('cart.html', cart=cart, subtotal=subtotal, before_vat=before_vat, vat_est=vat_est)

@app.route('/cart/update', methods=['POST'])
def update_cart():
    try:
        index = int(request.form.get('index'))
    except (ValueError, TypeError):
        return redirect(url_for('view_cart'))
        
    action = request.form.get('action') # 'increase', 'decrease', 'remove'
    cart = session.get('cart', [])

    if 0 <= index < len(cart):
        item = cart[index]
        conn = get_db()
        prod = conn.execute("SELECT stock, is_active FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        conn.close()

        if action == 'increase':
            if not prod or prod['is_active'] == 0 or prod['stock'] <= 0:
                flash(f'ขออภัย สินค้า {item["name"]} ในคลังหมดแล้วค่ะ', 'warning')
            else:
                total_in_cart = sum(it['quantity'] for it in cart if it['product_id'] == item['product_id'])
                if total_in_cart + 1 > prod['stock']:
                    unit_text = "แก้ว" if item.get('category') == 'drink' else "ชิ้น"
                    flash(f'⚠️ ขออภัย สินค้า {item["name"]} ในคลังมีเหลือเพียง {prod["stock"]} {unit_text} ไม่สามารถสั่งซื้อเกินจำนวนที่มีได้ค่ะ', 'warning')
                else:
                    item['quantity'] += 1
        elif action == 'decrease':
            item['quantity'] -= 1
            if item['quantity'] <= 0:
                cart.pop(index)
        elif action == 'remove':
            cart.pop(index)

    session['cart'] = cart
    return redirect(url_for('view_cart'))

@app.route('/cart/clear')
def clear_cart():
    session['cart'] = []
    flash('ล้างรายการในตะกร้าสินค้าเรียบร้อยแล้ว', 'info')
    return redirect(url_for('view_cart'))

# ==========================================
# 4. หน้าสั่งซื้อ & คำนวณค่าส่ง & Dynamic PromptPay
# ==========================================
@app.route('/api/calculate-shipping', methods=['POST'])
def api_calculate_shipping():
    data = request.json or {}
    lat = float(data.get('lat', STORE_LAT))
    lng = float(data.get('lng', STORE_LNG))

    distance = round(haversine_distance(STORE_LAT, STORE_LNG, lat, lng), 2)
    fee = calculate_shipping(distance)
    return jsonify({'distance_km': distance, 'shipping_fee': fee})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนทำการสั่งซื้อสินค้า', 'warning')
        return redirect(url_for('login'))

    cart = session.get('cart', [])
    if not cart:
        flash('ตะกร้าสินค้าว่างเปล่า กรุณาเลือกเครื่องดื่มมัทฉะก่อนนะคะ', 'warning')
        return redirect(url_for('index'))

    # ตรวจสอบความถูกต้องของสต็อกสินค้าในคลังแบบ Real-time ก่อนทำการสั่งซื้อ
    conn = get_db()
    for item in cart:
        prod = conn.execute("SELECT stock, is_active, name, category FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        if not prod or prod['is_active'] == 0 or prod['stock'] <= 0:
            conn.close()
            flash(f"⚠️ ขออภัย สินค้า {item['name']} ในคลังหมดสต็อกแล้ว กรุณาตรวจสอบตะกร้าสินค้าค่ะ", "danger")
            return redirect(url_for('view_cart'))
            
        total_in_cart = sum(it['quantity'] for it in cart if it['product_id'] == item['product_id'])
        if total_in_cart > prod['stock']:
            conn.close()
            unit_text = "แก้ว" if prod['category'] == 'drink' else "ชิ้น"
            flash(f"⚠️ ขออภัย สินค้า {item['name']} ในคลังมีเหลือเพียง {prod['stock']} {unit_text} ไม่สามารถสั่งซื้อ {total_in_cart} {unit_text} ได้ค่ะ ระบบได้นำคุณกลับมาที่ตะกร้าเพื่อปรับยอด", "danger")
            return redirect(url_for('view_cart'))

    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()

    subtotal = sum(item['price'] * item['quantity'] for item in cart)

    # สิทธิ์แลกแต้ม: ตรวจสอบเครื่องดื่มในตะกร้า (ฟรี 1 แก้ว ราคาไม่เกิน 100 บาท)
    eligible_drinks = [item for item in cart if item.get('category') == 'drink']
    max_drink_price = max((item['price'] for item in eligible_drinks), default=0.0)
    eligible_discount = min(100.0, max_drink_price) if eligible_drinks else 0.0

    if request.method == 'POST':
        lat = float(request.form.get('latitude', STORE_LAT))
        lng = float(request.form.get('longitude', STORE_LNG))
        address_note = request.form.get('address_note', '').strip()
        use_points = request.form.get('use_points') == '1'

        distance = round(haversine_distance(STORE_LAT, STORE_LNG, lat, lng), 2)
        delivery_fee = calculate_shipping(distance)

        # สิทธิ์แลกแต้ม: จะใช้ได้ก็ต่อเมื่อแต้มครบ 10 แต้มขึ้นไปเท่านั้น
        discount = 0.0
        if use_points and user['points'] >= 10 and eligible_drinks:
            discount = eligible_discount
            conn = get_db()
            conn.execute("UPDATE users SET points = points - 10 WHERE id = ?", (user['id'],))
            conn.commit()
            conn.close()

        # ถอย VAT 7%: ค่าน้ำเป็นราคารวมภาษีแล้ว
        subtotal_after_discount = max(0.0, subtotal - discount)
        before_vat = round(subtotal_after_discount / 1.07, 2)
        vat_amount = round(subtotal_after_discount - before_vat, 2)
        grand_total = round(subtotal_after_discount + delivery_fee, 2)

        # จัดการไฟล์สลิป
        slip_file = request.files.get('slip_image')
        slip_filename = ""
        if slip_file and slip_file.filename != "":
            ext = os.path.splitext(slip_file.filename)[1]
            slip_filename = f"slip_{int(time.time())}_{user['id']}{ext}"
            slip_file.save(os.path.join(app.config['UPLOAD_FOLDER'], slip_filename))

        # สร้าง Order No
        order_no = f"MTC{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"

        conn = get_db()
        cursor = conn.cursor()

        # ตรวจสอบและล็อคสต็อกคงเหลือจริง ณ วินาทีที่สั่งซื้อ
        for item in cart:
            prod = cursor.execute("SELECT stock, is_active, name, category FROM products WHERE id = ?", (item['product_id'],)).fetchone()
            if not prod or prod['is_active'] == 0 or prod['stock'] <= 0:
                conn.close()
                flash(f"ขออภัย สินค้า {item['name']} ในคลังหมดแล้วค่ะ", "danger")
                return redirect(url_for('view_cart'))
            total_in_cart = sum(it['quantity'] for it in cart if it['product_id'] == item['product_id'])
            if total_in_cart > prod['stock']:
                conn.close()
                unit_text = "แก้ว" if prod['category'] == 'drink' else "ชิ้น"
                flash(f"ขออภัย สินค้า {item['name']} ในคลังมีเหลือเพียง {prod['stock']} {unit_text} ไม่สามารถสั่งซื้อ {total_in_cart} {unit_text} ได้ค่ะ", "danger")
                return redirect(url_for('view_cart'))

        cursor.execute('''
            INSERT INTO orders (
                order_no, user_id, subtotal, vat_amount, discount_amount, 
                delivery_fee, grand_total, distance_km, customer_lat, customer_lng, 
                address_note, slip_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_no, user['id'], subtotal, vat_amount, discount, 
              delivery_fee, grand_total, distance, lat, lng, address_note, slip_filename))
        
        order_id = cursor.lastrowid

        # บันทึกรายการสินค้า และตัดสต็อค
        for item in cart:
            item_total = item['price'] * item['quantity']
            cursor.execute('''
                INSERT INTO order_items (
                    order_id, product_id, product_name, product_name_th, price_per_unit, 
                    quantity, sweetness, milk_type, total_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['name'], item.get('name_th', ''), item['price'], 
                  item['quantity'], item['sweetness'], item['milk_type'], item_total))

            cursor.execute('UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?', 
                           (item['quantity'], item['product_id']))

        conn.commit()
        conn.close()

        session['cart'] = []
        flash(f'🎉 สั่งซื้อสำเร็จ! เลขที่คำสั่งซื้อ {order_no} บันทึกหลักฐานสลิปเรียบร้อยแล้วค่ะ', 'success')
        return redirect(url_for('order_receipt', order_no=order_no))

    # GET: ค่าเริ่มต้นคำนวณถอย VAT
    init_before_vat = round(subtotal / 1.07, 2)
    init_vat = round(subtotal - init_before_vat, 2)
    init_total = subtotal # ส่งฟรีในระยะ 0 กม.

    return render_template('checkout.html',
                           cart=cart,
                           user=user,
                           subtotal=subtotal,
                           before_vat=init_before_vat,
                           init_vat=init_vat,
                           init_total=init_total,
                           eligible_discount=eligible_discount,
                           has_eligible_drink=bool(eligible_drinks),
                           store_lat=STORE_LAT,
                           store_lng=STORE_LNG,
                           promptpay_number=PROMPTPAY_NUMBER)

# ==========================================
# 4.1 หน้าใบเสร็จรับเงิน (Receipt) & พิมพ์ใบเสร็จ
# ==========================================
@app.route('/order/<order_no>/receipt')
def order_receipt(order_no):
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนเข้าดูใบเสร็จ', 'warning')
        return redirect(url_for('login'))

    conn = get_db()
    order = conn.execute('''
        SELECT o.*, u.name as customer_name, u.phone as customer_phone, u.username as customer_username
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.order_no = ?
    ''', (order_no,)).fetchone()

    if not order:
        conn.close()
        flash('ไม่พบข้อมูลคำสั่งซื้อนี้', 'danger')
        return redirect(url_for('index'))

    # ตรวจสอบสิทธิ์: เจ้าของคำสั่งซื้อ หรือ ผู้ดูแลระบบ (admin)
    if session.get('role') != 'admin' and order['user_id'] != session['user_id']:
        conn.close()
        flash('คุณไม่มีสิทธิ์เข้าดูใบเสร็จนี้', 'danger')
        return redirect(url_for('index'))

    items = conn.execute('''
        SELECT oi.*, p.category, p.drink_category, p.has_milk_option
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order['id'],)).fetchall()
    conn.close()

    return render_template('receipt.html', order=order, items=items)

# ==========================================
# 5. ระบบหลังบ้านแอดมิน (Admin Panel) & โค้ดลับ ImatchaU
# ==========================================
@app.route('/secret-admin', methods=['GET', 'POST'])
def secret_admin():
    """ประตูเข้าสู่ระบบแอดมินด้วยโค้ดลับ ImatchaU"""
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        code = request.form.get('secret_code', '').strip()
        if code == ADMIN_SECRET_KEY:
            conn = get_db()
            admin_user = conn.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1").fetchone()
            conn.close()

            if admin_user:
                session['user_id'] = admin_user['id']
                session['username'] = admin_user['username']
                session['role'] = 'admin'
                session['name'] = admin_user['name']
                flash('🔑 สำเร็จ!', 'success')
                return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ โค้ดลับไม่ถูกต้อง กรุณากรอกใหม่อีกครั้ง', 'danger')

    return render_template('secret_admin.html')

def require_admin():
    return session.get('role') == 'admin'

def format_thai_date(date_str):
    try:
        parts = date_str.split('-')
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        thai_months = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
        return f"{d} {thai_months[m]} {y}"
    except Exception:
        return date_str

def format_thai_month(month_str):
    try:
        parts = month_str.split('-')
        y, m = int(parts[0]), int(parts[1])
        thai_months = ['', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
        return f"{thai_months[m]} {y}"
    except Exception:
        return month_str

def format_thai_year(year_str):
    try:
        y = int(year_str)
        return f"ปี {y} (พ.ศ. {y + 543})"
    except Exception:
        return year_str

@app.route('/admin')
def admin_dashboard():
    if not require_admin():
        flash('หน้านี้สงวนสิทธิ์เฉพาะผู้ดูแลระบบร้าน I wendy Matcha เท่านั้น', 'danger')
        return redirect(url_for('index'))

    conn = get_db()
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    this_month_str = now.strftime('%Y-%m')
    this_year_str = now.strftime('%Y')

    # ตัวเลขสรุปยอดขายตามช่วงเวลา
    # 1. วันนี้ (Daily Summary)
    today_rev = conn.execute("SELECT SUM(grand_total) FROM orders WHERE payment_status = 'verified' AND DATE(created_at) = ?", (today_str,)).fetchone()[0] or 0.0
    today_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = ?", (today_str,)).fetchone()[0]
    today_verified_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'verified' AND DATE(created_at) = ?", (today_str,)).fetchone()[0]

    # 2. เดือนนี้ (Monthly Summary)
    month_rev = conn.execute("SELECT SUM(grand_total) FROM orders WHERE payment_status = 'verified' AND strftime('%Y-%m', created_at) = ?", (this_month_str,)).fetchone()[0] or 0.0
    month_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE strftime('%Y-%m', created_at) = ?", (this_month_str,)).fetchone()[0]
    month_verified_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'verified' AND strftime('%Y-%m', created_at) = ?", (this_month_str,)).fetchone()[0]

    # 3. ปีนี้ (Yearly Summary)
    year_rev = conn.execute("SELECT SUM(grand_total) FROM orders WHERE payment_status = 'verified' AND strftime('%Y', created_at) = ?", (this_year_str,)).fetchone()[0] or 0.0
    year_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE strftime('%Y', created_at) = ?", (this_year_str,)).fetchone()[0]
    year_verified_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'verified' AND strftime('%Y', created_at) = ?", (this_year_str,)).fetchone()[0]

    # 4. ทั้งหมด (All-time Summary)
    total_rev = conn.execute("SELECT SUM(grand_total) FROM orders WHERE payment_status = 'verified'").fetchone()[0] or 0.0
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_members = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0]
    low_stock_count = conn.execute("SELECT COUNT(*) FROM products WHERE stock <= 10").fetchone()[0]

    # รายงานยอดขายรายวัน (Sales by Day)
    raw_daily = conn.execute('''
        SELECT 
            DATE(created_at) as period,
            COUNT(*) as total_orders,
            COUNT(CASE WHEN payment_status = 'verified' THEN 1 END) as verified_orders,
            COUNT(CASE WHEN payment_status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN payment_status = 'rejected' THEN 1 END) as rejected_orders,
            SUM(CASE WHEN payment_status = 'verified' THEN grand_total ELSE 0 END) as verified_sales,
            SUM(grand_total) as all_sales
        FROM orders
        GROUP BY DATE(created_at)
        ORDER BY period DESC
    ''').fetchall()
    
    max_daily_sales = max([r['verified_sales'] for r in raw_daily] + [1])
    sales_daily = []
    for r in raw_daily:
        v_sales = float(r['verified_sales'] or 0.0)
        v_orders = int(r['verified_orders'] or 0)
        sales_daily.append({
            'period': r['period'],
            'label': format_thai_date(r['period']),
            'total_orders': r['total_orders'],
            'verified_orders': v_orders,
            'pending_orders': r['pending_orders'],
            'rejected_orders': r['rejected_orders'],
            'verified_sales': v_sales,
            'all_sales': float(r['all_sales'] or 0.0),
            'avg_ticket': round(v_sales / v_orders, 2) if v_orders > 0 else 0.0,
            'pct_bar': min(100, round((v_sales / max_daily_sales) * 100)) if max_daily_sales > 0 else 0
        })

    # รายงานยอดขายรายเดือน (Sales by Month)
    raw_monthly = conn.execute('''
        SELECT 
            strftime('%Y-%m', created_at) as period,
            COUNT(*) as total_orders,
            COUNT(CASE WHEN payment_status = 'verified' THEN 1 END) as verified_orders,
            COUNT(CASE WHEN payment_status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN payment_status = 'rejected' THEN 1 END) as rejected_orders,
            SUM(CASE WHEN payment_status = 'verified' THEN grand_total ELSE 0 END) as verified_sales,
            SUM(grand_total) as all_sales
        FROM orders
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY period DESC
    ''').fetchall()

    max_monthly_sales = max([r['verified_sales'] for r in raw_monthly] + [1])
    sales_monthly = []
    for r in raw_monthly:
        v_sales = float(r['verified_sales'] or 0.0)
        v_orders = int(r['verified_orders'] or 0)
        sales_monthly.append({
            'period': r['period'],
            'label': format_thai_month(r['period']),
            'total_orders': r['total_orders'],
            'verified_orders': v_orders,
            'pending_orders': r['pending_orders'],
            'rejected_orders': r['rejected_orders'],
            'verified_sales': v_sales,
            'all_sales': float(r['all_sales'] or 0.0),
            'avg_ticket': round(v_sales / v_orders, 2) if v_orders > 0 else 0.0,
            'pct_bar': min(100, round((v_sales / max_monthly_sales) * 100)) if max_monthly_sales > 0 else 0
        })

    # รายงานยอดขายรายปี (Sales by Year)
    raw_yearly = conn.execute('''
        SELECT 
            strftime('%Y', created_at) as period,
            COUNT(*) as total_orders,
            COUNT(CASE WHEN payment_status = 'verified' THEN 1 END) as verified_orders,
            COUNT(CASE WHEN payment_status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN payment_status = 'rejected' THEN 1 END) as rejected_orders,
            SUM(CASE WHEN payment_status = 'verified' THEN grand_total ELSE 0 END) as verified_sales,
            SUM(grand_total) as all_sales
        FROM orders
        GROUP BY strftime('%Y', created_at)
        ORDER BY period DESC
    ''').fetchall()

    max_yearly_sales = max([r['verified_sales'] for r in raw_yearly] + [1])
    sales_yearly = []
    for r in raw_yearly:
        v_sales = float(r['verified_sales'] or 0.0)
        v_orders = int(r['verified_orders'] or 0)
        sales_yearly.append({
            'period': r['period'],
            'label': format_thai_year(r['period']),
            'total_orders': r['total_orders'],
            'verified_orders': v_orders,
            'pending_orders': r['pending_orders'],
            'rejected_orders': r['rejected_orders'],
            'verified_sales': v_sales,
            'all_sales': float(r['all_sales'] or 0.0),
            'avg_ticket': round(v_sales / v_orders, 2) if v_orders > 0 else 0.0,
            'pct_bar': min(100, round((v_sales / max_yearly_sales) * 100)) if max_yearly_sales > 0 else 0
        })

    # สินค้าขายดียอดนิยม (Top 10 Best Sellers)
    top_selling = conn.execute('''
        SELECT 
            oi.product_name,
            p.category,
            p.image_url,
            SUM(oi.quantity) as total_qty,
            SUM(oi.total_price) as total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE o.payment_status = 'verified'
        GROUP BY oi.product_name
        ORDER BY total_qty DESC, total_revenue DESC
        LIMIT 10
    ''').fetchall()

    # ดึงรายการสินค้าทั้งหมด (รวมทั้งที่เปิดขายและหมดชั่วคราว)
    products = conn.execute("SELECT * FROM products ORDER BY category, id").fetchall()

    # ดึงคำสั่งซื้อทั้งหมด
    orders = conn.execute('''
        SELECT o.*, u.name as customer_name, u.phone as customer_phone
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''').fetchall()

    orders_full = []
    for ord_row in orders:
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (ord_row['id'],)).fetchall()
        orders_full.append({'order': ord_row, 'items': items})

    # ดึงรายชื่อสมาชิกสะสมแต้มทั้งหมด พร้อมประวัติและพฤติกรรมการสั่งซื้อ
    members_raw = conn.execute('''
        SELECT 
            u.id, u.username, u.name, u.phone, u.email, u.points, u.created_at,
            COUNT(o.id) as order_count,
            COALESCE(SUM(CASE WHEN o.payment_status = 'verified' THEN o.grand_total ELSE 0 END), 0) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.role = 'customer'
        GROUP BY u.id
        ORDER BY u.points DESC, total_spent DESC, u.id DESC
    ''').fetchall()

    members = []
    for m in members_raw:
        # หาเมนูที่ลูกค้าสั่งบ่อยที่สุด
        fav_row = conn.execute('''
            SELECT oi.product_name, SUM(oi.quantity) as qty
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.user_id = ?
            GROUP BY oi.product_name
            ORDER BY qty DESC
            LIMIT 1
        ''', (m['id'],)).fetchone()
        fav_menu = f"{fav_row['product_name']} ({fav_row['qty']} แก้ว)" if fav_row else "ยังไม่มีคำสั่งซื้อ"

        # รวมรายการสินค้าทั้งหมดที่เคยสั่งซื้อ
        all_ordered = conn.execute('''
            SELECT oi.product_name, SUM(oi.quantity) as qty
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.user_id = ?
            GROUP BY oi.product_name
            ORDER BY qty DESC
        ''', (m['id'],)).fetchall()
        ordered_summary = ", ".join([f"{item['product_name']} x{item['qty']}" for item in all_ordered]) if all_ordered else "ยังไม่มีประวัติการสั่ง"

        m_dict = dict(m)
        m_dict['favorite_menu'] = fav_menu
        m_dict['ordered_summary'] = ordered_summary
        m_dict['all_ordered_items'] = all_ordered
        m_dict['reg_date'] = str(m['created_at'])[:10] if m['created_at'] else '-'
        members.append(m_dict)

    conn.close()

    # เตรียมข้อมูลสำหรับกราฟ Chart.js (เรียงจากอดีต -> ปัจจุบัน)
    chart_daily = list(reversed(sales_daily[:14])) if sales_daily else []
    chart_labels = [d['label'] for d in chart_daily] if chart_daily else [format_thai_date(today_str)]
    chart_sales = [d['verified_sales'] for d in chart_daily] if chart_daily else [round(today_rev, 2)]
    chart_orders = [d['verified_orders'] for d in chart_daily] if chart_daily else [today_orders]

    return render_template('admin_dashboard.html',
                           today_str=today_str,
                           today_rev=round(today_rev, 2),
                           today_orders=today_orders,
                           month_rev=round(month_rev, 2),
                           month_orders=month_orders,
                           year_rev=round(year_rev, 2),
                           year_orders=year_orders,
                           total_rev=round(total_rev, 2),
                           total_orders=total_orders,
                           total_members=total_members,
                           low_stock_count=low_stock_count,
                           sales_daily=sales_daily,
                           sales_monthly=sales_monthly,
                           sales_yearly=sales_yearly,
                           top_selling=top_selling,
                           products=products,
                           orders_full=orders_full,
                           chart_labels=chart_labels,
                           chart_sales=chart_sales,
                           chart_orders=chart_orders,
                           members=members)

@app.route('/admin/update-stock', methods=['POST'])
def admin_update_stock():
    if not require_admin(): return redirect(url_for('login'))
    product_id = int(request.form.get('product_id'))
    added_stock = int(request.form.get('added_stock', 0))

    conn = get_db()
    conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (added_stock, product_id))
    conn.commit()
    conn.close()

    flash(f'เติมสต็อคสินค้า ID #{product_id} จำนวน +{added_stock} สำเร็จ', 'success')
    return redirect(url_for('admin_dashboard') + '#stockTab')

@app.route('/admin/edit-product', methods=['POST'])
def admin_edit_product():
    if not require_admin(): return redirect(url_for('login'))
    product_id = int(request.form.get('product_id'))
    name = request.form.get('name', '').strip()
    name_th = request.form.get('name_th', '').strip()
    category = request.form.get('category', 'drink')
    drink_category = request.form.get('drink_category', '-')
    has_milk_option = 1 if request.form.get('has_milk_option') == '1' else 0
    price = float(request.form.get('price', 0))
    stock = int(request.form.get('stock', 0))
    description = request.form.get('description', '').strip()
    is_active = 0 if request.form.get('is_temporary_out') == '1' else 1
    is_bestseller = 1 if request.form.get('is_bestseller') == '1' else 0

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        flash('ไม่พบสินค้าในระบบ', 'danger')
        return redirect(url_for('admin_dashboard') + '#stockTab')

    image_url = product['image_url']
    image_file = request.files.get('product_image')
    if image_file and image_file.filename != '':
        orig_filename = secure_filename(image_file.filename)
        ext = os.path.splitext(orig_filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            unique_name = f"prod_{int(time.time())}_{random.randint(100, 999)}{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            image_file.save(file_path)
            image_url = url_for('static', filename=f'uploads/{unique_name}')

    conn.execute('''
        UPDATE products 
        SET name = ?, name_th = ?, category = ?, drink_category = ?, has_milk_option = ?, 
            price = ?, stock = ?, description = ?, image_url = ?, is_active = ?, is_bestseller = ?
        WHERE id = ?
    ''', (name, name_th, category, drink_category, has_milk_option, price, stock, description, image_url, is_active, is_bestseller, product_id))
    conn.commit()
    conn.close()

    flash(f'✅ บันทึกการแก้ไขเมนู "{name}" เรียบร้อยแล้ว', 'success')
    return redirect(url_for('admin_dashboard') + '#stockTab')

@app.route('/admin/toggle-product-status', methods=['POST'])
def admin_toggle_product_status():
    if not require_admin(): return redirect(url_for('login'))
    product_id = int(request.form.get('product_id'))
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        new_status = 0 if product['is_active'] == 1 else 1
        conn.execute("UPDATE products SET is_active = ? WHERE id = ?", (new_status, product_id))
        conn.commit()
        status_text = "วางจำหน่ายปกติ 🟢" if new_status == 1 else "หมดชั่วคราว 🟡"
        flash(f'เปลี่ยนสถานะ "{product["name"]}" เป็น: {status_text}', 'info')
    conn.close()
    return redirect(url_for('admin_dashboard') + '#stockTab')

@app.route('/admin/add-product', methods=['POST'])
def admin_add_product():
    if not require_admin(): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    name_th = request.form.get('name_th', '').strip()
    category = request.form.get('category', 'drink')
    drink_category = request.form.get('drink_category', '-')
    has_milk_option = 1 if request.form.get('has_milk_option') == '1' else 0
    price = float(request.form.get('price', 0))
    stock = int(request.form.get('stock', 50))
    description = request.form.get('description', '').strip()
    is_bestseller = 1 if request.form.get('is_bestseller') == '1' else 0

    # จัดการอัปโหลดไฟล์รูปภาพสินค้าแทน URL
    image_file = request.files.get('product_image')
    image_url = ""
    if image_file and image_file.filename != '':
        orig_filename = secure_filename(image_file.filename)
        ext = os.path.splitext(orig_filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            unique_name = f"prod_{int(time.time())}_{random.randint(100, 999)}{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            image_file.save(file_path)
            image_url = url_for('static', filename=f'uploads/{unique_name}')
        else:
            flash('⚠️ กรุณาอัปโหลดไฟล์รูปภาพ (.jpg, .jpeg, .png, .webp) เท่านั้นค่ะ', 'warning')
            return redirect(url_for('admin_dashboard') + '#stockTab')

    # หากไม่มีการอัปโหลดไฟล์ ให้ใช้รูปพื้นฐาน
    if not image_url:
        image_url = "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?w=450"

    conn = get_db()
    conn.execute('''
        INSERT INTO products (name, name_th, category, drink_category, has_milk_option, price, stock, description, image_url, is_bestseller)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, name_th, category, drink_category, has_milk_option, price, stock, description, image_url, is_bestseller))
    conn.commit()
    conn.close()

    flash(f'เพิ่มสินค้าใหม่ "{name} ({name_th})" พร้อมอัปโหลดรูปภาพสำเร็จเรียบร้อย', 'success')
    return redirect(url_for('admin_dashboard') + '#stockTab')

@app.route('/admin/order-status', methods=['POST'])
def admin_order_status():
    if not require_admin(): return redirect(url_for('login'))
    order_id = int(request.form.get('order_id'))
    payment_status = request.form.get('payment_status')
    shipping_status = request.form.get('shipping_status')

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    # กติกาแต้ม: เมื่อสถานะจัดส่งเป็น 'completed' (จัดส่งสำเร็จ) และยังไม่เคยให้แต้ม
    # ระบบจะบวกแต้มสะสมให้ลูกค้า +1 แต้ม ต่อแก้วน้ำในออเดอร์นั้น
    points_message = ""
    if shipping_status == 'completed' and order['points_awarded'] == 0:
        drink_qty = conn.execute('''
            SELECT SUM(oi.quantity) FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ? AND p.category = 'drink'
        ''', (order_id,)).fetchone()[0] or 0

        if drink_qty > 0:
            conn.execute("UPDATE users SET points = points + ? WHERE id = ?", (drink_qty, order['user_id']))
            conn.execute("UPDATE orders SET points_awarded = 1 WHERE id = ?", (order_id,))
            points_message = f" พร้อมบวกแต้มสะสม +{drink_qty} แต้ม ให้ลูกค้าแล้ว"

    conn.execute('''
        UPDATE orders SET payment_status = ?, shipping_status = ? WHERE id = ?
    ''', (payment_status, shipping_status, order_id))
    conn.commit()
    conn.close()

    flash(f'อัปเดตคำสั่งซื้อ #{order["order_no"]} สำเร็จ!{points_message}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-product', methods=['POST'])
def admin_delete_product():
    if not require_admin(): return redirect(url_for('login'))
    product_id = int(request.form.get('product_id'))
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        name_display = f"{product['name']} ({product['name_th']})" if product['name_th'] else product['name']
        try:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        except Exception:
            conn.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
            conn.commit()
        flash(f'🗑️ ลบเมนู "{name_display}" ออกจากระบบเรียบร้อยแล้วค่ะ', 'success')
    conn.close()
    return redirect(url_for('admin_dashboard') + '#stockTab')

@app.route('/api/admin/pending-orders')
def api_admin_pending_orders():
    if not require_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    pending_orders = conn.execute('''
        SELECT o.id, o.order_no, o.grand_total, o.created_at, u.name as customer_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.payment_status = 'pending'
        ORDER BY o.id DESC
    ''').fetchall()

    count = len(pending_orders)
    max_id = pending_orders[0]['id'] if count > 0 else 0
    latest_order_no = pending_orders[0]['order_no'] if count > 0 else None
    latest_customer = pending_orders[0]['customer_name'] if count > 0 else None
    latest_total = pending_orders[0]['grand_total'] if count > 0 else 0

    conn.close()
    return jsonify({
        'count': count,
        'max_id': max_id,
        'latest_order_no': latest_order_no,
        'latest_customer': latest_customer,
        'latest_total': latest_total,
        'orders': [{'id': o['id'], 'order_no': o['order_no'], 'grand_total': o['grand_total'], 'customer_name': o['customer_name']} for o in pending_orders]
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)

