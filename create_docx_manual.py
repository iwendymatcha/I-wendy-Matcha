import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}>'
                      f'<w:top w:w="{top}" w:type="dxa"/>'
                      f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
                      f'<w:left w:w="{left}" w:type="dxa"/>'
                      f'<w:right w:w="{right}" w:type="dxa"/>'
                      f'</w:tcMar>')
    tcPr.append(tcMar)

def add_callout(doc, text, title="คำแนะนำ / ข้อควรรู้", border_hex="879f48", bg_hex="f4f7ee"):
    """Create a stylized callout box."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)
    
    # Left border only (thick highlight)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}>'
                        f'<w:top w:val="none"/>'
                        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{border_hex}"/>'
                        f'<w:bottom w:val="none"/>'
                        f'<w:right w:val="none"/>'
                        f'</w:tcBorders>')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run_t = p.add_run(f"📌 {title}: ")
    run_t.bold = True
    run_t.font.name = "TH Sarabun PSK"
    run_t.font.size = Pt(14)
    run_t.font.color.rgb = RGBColor(0x38, 0x52, 0x23)
    
    run_b = p.add_run(text)
    run_b.font.name = "TH Sarabun PSK"
    run_b.font.size = Pt(14)
    run_b.font.color.rgb = RGBColor(0x22, 0x31, 0x1c)
    
    # spacing after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

def build_manual_docx():
    doc = Document()
    
    # Page Setup (Standard A4 with 1 inch / 2.54 cm margins)
    for section in doc.sections:
        section.page_width = Inches(8.27)  # A4 width
        section.page_height = Inches(11.69) # A4 height
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.2)
        section.right_margin = Inches(1.0)

    # Base Style Config
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'TH Sarabun PSK'
    style_normal.font.size = Pt(15)
    style_normal.font.color.rgb = RGBColor(0x22, 0x31, 0x1c)
    style_normal.paragraph_format.line_spacing = 1.15

    # ----------------------------------------------------
    # COVER PAGE (หน้าปก)
    # ----------------------------------------------------
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_before = Pt(20)
    p_logo.paragraph_format.space_after = Pt(15)
    
    logo_path = 'static/images/kku_education_logo.png'
    if os.path.exists(logo_path):
        p_logo.add_run().add_picture(logo_path, width=Inches(1.6))
        
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(8)
    run_doc_type = p_title.add_run("เอกสารคู่มือและคำอธิบายการใช้งาน\n")
    run_doc_type.font.size = Pt(22)
    run_doc_type.bold = True
    run_doc_type.font.color.rgb = RGBColor(0x20, 0x33, 0x14)
    
    run_prog_name = p_title.add_run("โปรแกรมระบบสั่งซื้อและบริหารจัดการร้านชาเขียวมัทฉะแท้\n( I wendy Matcha )")
    run_prog_name.font.size = Pt(20)
    run_prog_name.bold = True
    run_prog_name.font.color.rgb = RGBColor(0x38, 0x52, 0x23)

    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_before = Pt(40)
    p_by.paragraph_format.space_after = Pt(4)
    r = p_by.add_run("โดย\n")
    r.font.size = Pt(16)
    r.bold = True
    r = p_by.add_run("นางสาวฐิติรัตน์ เสรี  รหัสนักศึกษา 673050515-0")
    r.font.size = Pt(16)

    p_adv = doc.add_paragraph()
    p_adv.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_adv.paragraph_format.space_before = Pt(30)
    p_adv.paragraph_format.space_after = Pt(4)
    r = p_adv.add_run("เสนอ\n")
    r.font.size = Pt(16)
    r.bold = True
    r = p_adv.add_run("ผศ.ดร.นฏกร ประมายันต์")
    r.font.size = Pt(16)

    p_course = doc.add_paragraph()
    p_course.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_course.paragraph_format.space_before = Pt(50)
    p_course.paragraph_format.space_after = Pt(0)
    p_course.paragraph_format.line_spacing = 1.2
    
    r = p_course.add_run("เอกสารคู่มือการใช้งานเล่มนี้เป็นส่วนหนึ่งของรายวิชา ED251007\n")
    r.font.size = Pt(15)
    r = p_course.add_run("( การเขียนโปรแกรมคอมพิวเตอร์สำหรับครู )\n")
    r.font.size = Pt(15)
    r = p_course.add_run("คณะศึกษาศาสตร์ สาขาคอมพิวเตอร์ศึกษา มหาวิทยาลัยขอนแก่น\n")
    r.font.size = Pt(15)
    r = p_course.add_run("ภาคเรียนที่ 1 ชั้นปีที่ 2 ปีการศึกษา 2568")
    r.font.size = Pt(15)

    doc.add_page_break()

    # ----------------------------------------------------
    # PREFACE (คำนำ)
    # ----------------------------------------------------
    p_pref_title = doc.add_paragraph()
    p_pref_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_pref_title.paragraph_format.space_before = Pt(20)
    p_pref_title.paragraph_format.space_after = Pt(24)
    r = p_pref_title.add_run("คำนำ")
    r.font.size = Pt(22)
    r.bold = True
    r.font.color.rgb = RGBColor(0x20, 0x33, 0x14)

    p1 = doc.add_paragraph()
    p1.paragraph_format.first_line_indent = Inches(0.5)
    p1.paragraph_format.space_after = Pt(10)
    p1.paragraph_format.line_spacing = 1.15
    p1.add_run(
        "เอกสารคู่มือการใช้งานโปรแกรม “ระบบสั่งซื้อและบริหารจัดการร้านชาเขียวมัทฉะแท้ I wendy Matcha” ฉบับนี้ "
        "จัดทำขึ้นเพื่อใช้ประกอบการจัดการเรียนรู้และการสอนเกี่ยวกับการออกแบบ พัฒนา และบริหารจัดการระบบร้านค้าพาณิชย์อิเล็กทรอนิกส์ (E-Commerce Web Application) "
        "รวมทั้งเป็นส่วนหนึ่งของการศึกษารายวิชา ED251007 การเขียนโปรแกรมคอมพิวเตอร์สำหรับครู สาขาคอมพิวเตอร์ศึกษา คณะศึกษาศาสตร์ มหาวิทยาลัยขอนแก่น "
        "โดยโปรแกรมดังกล่าวได้รับการพัฒนาขึ้นด้วยภาษา Python ร่วมกับ Flask Web Framework และฐานข้อมูลเชิงสัมพันธ์ SQLite "
        "เพื่อจำลองระบบการดำเนินงานร้านค้าออนไลน์ที่ทันสมัยและครบวงจร ตอบสนองพฤติกรรมผู้บริโภคในยุคดิจิทัลอย่างแท้จริง"
    )

    p2 = doc.add_paragraph()
    p2.paragraph_format.first_line_indent = Inches(0.5)
    p2.paragraph_format.space_after = Pt(10)
    p2.paragraph_format.line_spacing = 1.15
    p2.add_run(
        "ระบบ I wendy Matcha ถูกออกแบบสถาปัตยกรรมครอบคลุมทั้ง 2 ส่วนหลัก ได้แก่ ระบบฝั่งลูกค้า (Customer Storefront) "
        "ประกอบด้วย หน้าสแปลชสกรีนเปิดร้านแบบ Interactive Animation, การคัดเลือกสินค้าตามหมวดหมู่ Flavor Notes ทั้ง Pure Matcha, "
        "Matcha Latte, Matcha Fusion, ผงมัทฉะเกรดพิธีการ และเซ็ตอุปกรณ์ชงชา Handmade, การเลือกปรับระดับความหวานและประเภทนมทางเลือก, "
        "ระบบตะกร้าสินค้าแบบตอบสนองทันที, การปักหมุดแผนที่ GPS คำนวณระยะทางและค่าจัดส่งจริงจาก Central Khon Kaen Campus, "
        "การชำระเงินผ่าน QR Code พร้อมเพย์แบบแนบสลิปโอนเงิน, ระบบออกใบเสร็จรับเงินอิเล็กทรอนิกส์ (E-Receipt Slip), ระบบติดตามสถานะคำสั่งซื้อแบบ Live Stepper, "
        "และระบบสะสมแต้มสมาชิก 10 แต้มฟรี 1 แก้ว สำหรับส่วนที่สองคือ ระบบผู้ดูแลระบบหลังบ้าน (Admin Dashboard) ประกอบด้วย แดชบอร์ดวิเคราะห์ยอดขายและสถิติ KPI, "
        "ระบบแจ้งเตือนคำสั่งซื้อใหม่และตรวจสอบสลิปการโอน, ระบบคลังสินค้าจัดการสต็อกและปรับปรุงเมนู, ระบบตรวจสอบสมาชิก และระบบตั้งค่าข้อมูลร้านค้า"
    )

    p3 = doc.add_paragraph()
    p3.paragraph_format.first_line_indent = Inches(0.5)
    p3.paragraph_format.space_after = Pt(10)
    p3.paragraph_format.line_spacing = 1.15
    p3.add_run(
        "คู่มือฉบับนี้มีวัตถุประสงค์เพื่อให้ผู้เรียน ครูผู้สอน และผู้สนใจทั่วไปเข้าใจโครงสร้าง สถาปัตยกรรม และขั้นตอนการใช้งานระบบได้อย่างชัดเจน "
        "ผ่านคำอธิบายส่วนประกอบหน้าจออย่างเป็นลำดับขั้นตอน การจัดการข้อมูลในฐานข้อมูล และตัวอย่างการแก้ปัญหาในสถานการณ์จริง "
        "ซึ่งช่วยส่งเสริมทักษะการบูรณาการองค์ความรู้ด้านวิทยาการคำนวณ เทคโนโลยีสารสนเทศ และการพัฒนานวัตกรรมทางการศึกษาในฐานะครูยุคดิจิทัล "
        "ผู้จัดทำหวังเป็นอย่างยิ่งว่าเอกสารคู่มือฉบับนี้จะเป็นประโยชน์ต่อการเรียนรู้และการพัฒนาต่อยอด หากมีข้อเสนอแนะประการใด ผู้จัดทำขอน้อมรับไว้ด้วยความขอบคุณยิ่ง"
    )

    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sign.paragraph_format.space_before = Pt(36)
    p_sign.paragraph_format.space_after = Pt(2)
    p_sign.add_run("นางสาวฐิติรัตน์ เสรี\nผู้จัดทำ")

    doc.add_page_break()

    # ----------------------------------------------------
    # TABLE OF CONTENTS (สารบัญ)
    # ----------------------------------------------------
    p_toc_title = doc.add_paragraph()
    p_toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_title.paragraph_format.space_before = Pt(20)
    p_toc_title.paragraph_format.space_after = Pt(20)
    r = p_toc_title.add_run("สารบัญ")
    r.font.size = Pt(22)
    r.bold = True
    r.font.color.rgb = RGBColor(0x20, 0x33, 0x14)

    toc_items = [
        ("คำนำ", "ก"),
        ("สารบัญ", "ข"),
        ("บทที่ 1: ระบบลงทะเบียนและเข้าสู่ระบบ (Authentication System)", "1"),
        ("   1.1 การเข้าสู่ระบบสมาชิก (User Login)", "1"),
        ("   1.2 การสมัครสมาชิกใหม่ (Member Registration)", "3"),
        ("   1.3 ระบบลืมรหัสผ่านและรีเซ็ตรหัสผ่านด้วย OTP ทางอีเมล (Forgot & Reset Password)", "6"),
        ("บทที่ 2: ระบบสั่งซื้อสินค้าหน้าร้านสำหรับลูกค้า (Storefront & Ordering)", "9"),
        ("   2.1 หน้าปกและสแปลชสกรีนต้อนรับ (Interactive Splash Cover)", "9"),
        ("   2.2 เมนูเครื่องดื่มและหมวดหมู่สินค้า (Matcha Categories & Flavor Notes)", "11"),
        ("   2.3 การปรับแต่งระดับความหวานและประเภทนม (Customization Options)", "13"),
        ("   2.4 ตะกร้าสินค้าและการคำนวณราคาภาษี (Shopping Cart & VAT Calculation)", "15"),
        ("   2.5 ระบบปักหมุด GPS และคำนวณค่าจัดส่งตามระยะทางจริง (GPS Distance Matrix)", "18"),
        ("   2.6 การชำระเงินด้วย QR Code PromptPay และการแนบสลิปโอนเงิน (QR Payment)", "21"),
        ("   2.7 ใบเสร็จรับเงินอิเล็กทรอนิกส์ (E-Receipt Slip & Verification)", "24"),
        ("   2.8 การติดตามสถานะคำสั่งซื้อแบบสด (Live Order Tracking & Stepper)", "26"),
        ("   2.9 ระบบสะสมแต้มสมาชิก (Loyalty Points System 10 ฟรี 1)", "28"),
        ("   2.10 ข้อมูลส่วนตัวและการแก้ไขโปรไฟล์ (Member Profile)", "30"),
        ("บทที่ 3: ระบบผู้ดูแลระบบหลังบ้าน (Admin Management System)", "32"),
        ("   3.1 การเข้าสู่ระบบแอดมินและรหัสผ่านลับ (Admin Auth & Secret Portal)", "32"),
        ("   3.2 แดชบอร์ดสรุปยอดขายและสถิติธุรกิจ (Sales Analytics & KPI Bento Dashboard)", "34"),
        ("   3.3 การจัดการคำสั่งซื้อและตรวจสอบสลิป (Order Verification & Bell Notification)", "37"),
        ("   3.4 การจัดการคลังสินค้า สต็อก และเมนูสินค้า (Product & Inventory Management)", "41"),
        ("   3.5 การจัดการข้อมูลสมาชิกและคะแนนสะสม (Member Management)", "44"),
        ("   3.6 การตั้งค่าข้อมูลร้านค้าและช่องทางติดต่อ (Store Settings)", "46"),
        ("บทที่ 4: โครงสร้างฐานข้อมูลระบบ (SQLite Database Schema)", "48"),
        ("   4.1 ตารางข้อมูลผู้ใช้งาน (users)", "48"),
        ("   4.2 ตารางข้อมูลสินค้าและสต็อก (products)", "50"),
        ("   4.3 ตารางข้อมูลคำสั่งซื้อ (orders)", "52"),
        ("   4.4 ตารางข้อมูลรายการสินค้าในคำสั่งซื้อ (order_items)", "54"),
        ("   4.5 ข้อมูลการตั้งค่าระบบและค่าจัดส่ง (System Configuration & Constants)", "56"),
    ]

    for item, page in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        
        is_main = item.startswith("บทที่") or item in ["คำนำ", "สารบัญ"]
        r1 = p.add_run(item)
        r1.font.size = Pt(15)
        if is_main:
            r1.bold = True
            r1.font.color.rgb = RGBColor(0x38, 0x52, 0x23)
            
        dots_count = max(5, 75 - len(item) * 2)
        r2 = p.add_run(" " + "." * dots_count + " ")
        r2.font.color.rgb = RGBColor(0x94, 0xa3, 0xb8)
        
        r3 = p.add_run(page)
        r3.font.size = Pt(15)
        if is_main:
            r3.bold = True

    doc.add_page_break()

    # Helper function for Chapter Headings
    def add_chapter_heading(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(12)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.size = Pt(20)
        r.bold = True
        r.font.color.rgb = RGBColor(0x20, 0x33, 0x14)
        return p

    def add_section_heading(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.size = Pt(17)
        r.bold = True
        r.font.color.rgb = RGBColor(0x38, 0x52, 0x23)
        return p

    def add_step(num_text, desc_text):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r_num = p.add_run(num_text + " ")
        r_num.bold = True
        r_num.font.color.rgb = RGBColor(0x20, 0x33, 0x14)
        r_desc = p.add_run(desc_text)
        return p

    # ----------------------------------------------------
    # CHAPTER 1: AUTHENTICATION
    # ----------------------------------------------------
    add_chapter_heading("บทที่ 1: ระบบลงทะเบียนและเข้าสู่ระบบ (Authentication System)")

    add_section_heading("1.1 การเข้าสู่ระบบสมาชิก (User Login)")
    p = doc.add_paragraph()
    p.add_run(
        "ระบบเข้าสู่ระบบของ I wendy Matcha ออกแบบให้สมาชิกสามารถเข้าถึงสิทธิประโยชน์ต่างๆ เช่น การสะสมแต้มครบ 10 แก้ว ฟรี 1 แก้ว "
        "การติดตามออเดอร์ และการบันทึกที่อยู่จัดส่ง โดยหน้าเข้าสู่ระบบมีองค์ประกอบและขั้นตอนการใช้งานดังนี้:"
    )
    add_step("1.", "ช่องกรอกชื่อผู้ใช้ (Username): สำหรับระบุชื่อผู้ใช้ที่ได้ลงทะเบียนไว้กับระบบ โดยมีระบบบันทึกตัวพิมพ์เล็ก-ใหญ่ตามจริง")
    add_step("2.", "ช่องกรอกรหัสผ่าน (Password): ช่องป้อนรหัสผ่านที่มีระบบความปลอดภัย และมีข้อความตัวอย่างสีอ่อนสบายตา (Placeholder) เพื่อความโปร่งโล่ง")
    add_step("3.", "ปุ่มเปิด-ปิดการแสดงรหัสผ่าน (Show/Hide Password): ไอคอนรูปดวงตาช่วยให้ผู้ใช้ตรวจสอบความถูกต้องของรหัสผ่านได้ก่อนกดยืนยัน")
    add_step("4.", "ลิงก์ 'ลืมรหัสผ่าน?': สำหรับกรณีที่ผู้ใช้ลืมรหัสผ่าน ระบบจะนำทางไปยังหน้ารับรหัส OTP 6 หลักผ่านทางอีเมล")
    add_step("5.", "ปุ่ม 'เข้าสู่ระบบ' (Login Button): กดเพื่อส่งข้อมูลเข้าสู่ระบบ โดยระบบจะตรวจสอบความถูกต้องของรหัสผ่านที่เข้ารหัสแบบ Hashing")
    add_step("6.", "การตรวจสอบสิทธิ์และแจ้งเตือน: หากชื่อผู้ใช้หรือรหัสผ่านถูกต้อง ระบบจะนำทางเข้าสู่หน้าหลักของร้าน พร้อมแสดงชื่อและแต้มสะสมทันที "
                    "หากไม่ถูกต้อง ระบบจะแสดงกล่องแจ้งเตือนสีแดงพร้อมข้อความระบุข้อผิดพลาดอย่างชัดเจน")
    add_step("7.", "ลิงก์สมัครสมาชิกใหม่: สำหรับผู้ใช้งานใหม่ที่ยังไม่มีบัญชี สามารถคลิกเพื่อสลับไปยังหน้าลงทะเบียนได้ทันที")
    
    add_callout(doc, "ระบบรักษาความปลอดภัยรหัสผ่านของ I wendy Matcha ใช้ฟังก์ชัน werkzeug.security.check_password_hash เพื่อเข้ารหัสแบบทางเดียว ป้องกันการรั่วไหลของรหัสผ่านอย่างสมบูรณ์", "ความปลอดภัยของระบบ")

    add_section_heading("1.2 การสมัครสมาชิกใหม่ (Member Registration)")
    p = doc.add_paragraph()
    p.add_run(
        "หน้าลงทะเบียนสมาชิกใหม่ได้รับการออกแบบตามหลัก User Experience (UX) ที่กระชับ ไม่รกตา "
        "พร้อมระบบตรวจสอบความถูกต้องของข้อมูลแบบเรียลไทม์ (Client-side & Server-side Validation) โดยมีเงื่อนไขดังนี้:"
    )
    add_step("1.", "ชื่อ-นามสกุล (Name): กรอกชื่อและนามสกุลจริงของลูกค้า สำหรับใช้จ่าหน้าบนใบเสร็จรับเงินและการติดต่อจัดส่งสินค้า")
    add_step("2.", "เบอร์โทรศัพท์ (Telephone): บังคับกรอกเป็นตัวเลข 10 หลักที่ขึ้นต้นด้วยเลข 0 เท่านั้น (Regex: 0[0-9]{9}) และต้องไม่ซ้ำกับสมาชิกท่านอื่น")
    add_step("3.", "อีเมล (Email): กรอกอีเมลที่ใช้งานได้จริง (ต้องมีเครื่องหมาย @ และโดเมนที่ถูกต้อง) ใช้สำหรับรับรหัส OTP เมื่อต้องการรีเซ็ตรหัสผ่าน")
    add_step("4.", "ชื่อผู้ใช้ (Username): บัญชีผู้ใช้ภาษาอังกฤษหรือตัวเลขความยาวตั้งแต่ 4-20 ตัวอักษร สำหรับล็อกอินเข้าใช้งาน")
    add_step("5.", "รหัสผ่าน (Password): ต้องมีความยาวอย่างน้อย 8 ตัวอักษร และประกอบด้วยตัวอักษรภาษาอังกฤษและตัวเลขรวมกัน (Alphanumeric)")
    add_step("6.", "การตรวจสอบแบบสด (Live Validation): ขณะพิมพ์รหัสผ่าน หากยังไม่ครบตามเงื่อนไข ระบบจะแสดงข้อความแจ้งเตือนสีแดงด้านล่างช่องกรอกทันที")
    add_step("7.", "ปุ่ม 'สมัครสมาชิก & รับสิทธิ์สะสมแต้ม': เมื่อกรอกข้อมูลถูกต้องครบทุกช่องและกดยืนยัน ระบบจะสร้างบัญชีและนำทางไปหน้าเข้าสู่ระบบอัตโนมัติ")

    add_section_heading("1.3 ระบบลืมรหัสผ่านและรีเซ็ตรหัสผ่านด้วย OTP ทางอีเมล (Forgot & Reset Password)")
    p = doc.add_paragraph()
    p.add_run(
        "เพื่ออำนวยความสะดวกให้แก่ลูกค้ากรณีลืมรหัสผ่าน ระบบมีฟังก์ชันกู้คืนรหัสผ่านด้วย One-Time Password (OTP) ส่งตรงถึงอีเมลผู้ใช้งานจริง:"
    )
    add_step("1.", "ระบุอีเมลหรือชื่อผู้ใช้: ลูกค้ากรอกอีเมลที่ผูกไว้กับบัญชีในหน้า /forgot-password แล้วกดปุ่ม 'ส่งรหัส OTP ไปยังอีเมล'")
    add_step("2.", "การสร้างและส่ง OTP: ระบบทำการสุ่มตัวเลข 6 หลักแบบปลอดภัย กำหนดเวลาหมดอายุ 15 นาที และส่งเข้ากล่องจดหมายอีเมลของลูกค้าด้วย SMTP")
    add_step("3.", "ยืนยันรหัส OTP (6 หลัก): ลูกค้านำรหัส 6 หลักที่ได้รับมากรอกในหน้า /reset-password พร้อมตั้งรหัสผ่านใหม่และยืนยันรหัสผ่านอีกครั้ง")
    add_step("4.", "อัปเดตและแจ้งเตือน: หากรหัส OTP ถูกต้องและยังไม่หมดอายุ ระบบจะทำการ Hash รหัสผ่านใหม่ บันทึกลงฐานข้อมูล และแจ้งเตือนสำเร็จ")

    doc.add_page_break()

    # ----------------------------------------------------
    # CHAPTER 2: STOREFRONT & CUSTOMER ORDERING
    # ----------------------------------------------------
    add_chapter_heading("บทที่ 2: ระบบสั่งซื้อสินค้าหน้าร้านสำหรับลูกค้า (Storefront & Ordering)")

    add_section_heading("2.1 หน้าปกและสแปลชสกรีนต้อนรับ (Interactive Splash Cover)")
    p = doc.add_paragraph()
    p.add_run(
        "เมื่อลูกค้าเปิดเข้าสู่เว็บไซต์ I wendy Matcha จะพบกับหน้าปกเปิดร้านแบบพรีเมียม (Splash Screen) "
        "ซึ่งสร้างบรรยากาศร้านชาสไตล์ญี่ปุ่นมินิมอล โดยมีคุณสมบัติดังนี้:"
    )
    add_step("1.", "ฉากหลังลายลูกไม้สีขาวบริสุทธิ์: ใช้ภาพลายลูกไม้ธรรมชาติที่สะอาดตา สอดรับกับความพรีเมียมของชาเขียวมัทฉะ")
    add_step("2.", "โลโก้ตัวเขียนภาษาอังกฤษ 'I wendy Matcha': จัดวางตรงกึ่งกลางหน้าจออย่างสมดุล")
    add_step("3.", "แก้วมัทฉะซิกเนเจอร์พร้อมวิปครีมชมพูและดอกลิลลี่: ภาพเครื่องดื่มมัทฉะแท้ที่มีมิติและหยดวิปครีมชมพูลงบนโต๊ะอย่างประณีต")
    add_step("4.", "แอนิเมชันคลิกเพื่อเข้าสู่ร้าน (Click Animation): เมื่อผู้ใช้คลิกหรือแตะบนหน้าจอ 1 ครั้ง แก้วมัทฉะจะเคลื่อนลอยขึ้นด้านบน "
                    "พร้อมตัวหนังสือที่ลอยขึ้นและค่อยๆ จางมูฟส่งผ่านเข้าสู่หน้าหลักของร้านอย่างนุ่มนวล")
    add_step("5.", "ระบบจำสถานะ (Session Storage): เมื่อเข้าสู่ร้านแล้ว หน้าปกจะไม่แสดงซ้ำขณะเปลี่ยนหน้า แต่ลูกค้าสามารถคลิกที่โลโก้บนแถบ Navbar เพื่อดูหน้าปกซ้ำได้ตลอดเวลา")

    add_section_heading("2.2 เมนูเครื่องดื่มและหมวดหมู่สินค้า (Matcha Categories & Flavor Notes)")
    p = doc.add_paragraph()
    p.add_run(
        "หน้าหลักของร้านจัดแสดงรายการสินค้าด้วย Bento Grid Layout ที่มีรูปภาพสินค้าคมชัด และแบ่งตามแถบหมวดหมู่แคปซูล (Category Pills):"
    )
    add_step("1.", "All (ทั้งหมด): แสดงสินค้าทุกรายการในร้าน เพื่อให้ลูกค้าเลือกชมได้อย่างอิสระ")
    add_step("2.", "Best Sellers (สินค้าขายดี): เมนูที่ได้รับความนิยมสูงสุดของร้าน พร้อมป้ายดาวสีทองสะดุดตา")
    add_step("3.", "Pure Matcha (มัทฉะเข้มข้นไม่ผสมนม): สายมัทฉะแท้ เช่น Uji Hikari Usucha, Ceremonial Fukuoka Yame")
    add_step("4.", "Matcha Latte (มัทฉะลาเต้นมสด): ผสมผสานความนุ่มละมุน เช่น Samidori Premium Latte, Okumidori Velvety Latte")
    add_step("5.", "Matcha Fusion (มัทฉะฟิวชันสูตรพิเศษ): เครื่องดื่มมัทฉะแนวสร้างสรรค์ เช่น Yuzu Sparkling Matcha, Coconut Cloud Matcha")
    add_step("6.", "Matcha Powder (ผงมัทฉะคัดเกรด): ผงชาเกรดพิธีการนำเข้าจากเกียวโตและฟุกุโอกะ สำหรับชงดื่มเองที่บ้าน")
    add_step("7.", "Matcha Sets (เซ็ตอุปกรณ์ชงชา): เซ็ตถ้วยชงชา Chawan, แปรงไม้ไผ่ Chasen, ช้อนตักชา Chashaku พร้อมขาตั้งเซรามิก")

    add_section_heading("2.3 การปรับแต่งระดับความหวานและประเภทนม (Customization Options)")
    p = doc.add_paragraph()
    p.add_run(
        "สำหรับสินค้าหมวดเครื่องดื่ม ลูกค้าสามารถปรับแต่งรสชาติตามความชอบส่วนบุคคลได้ก่อนกดสั่งซื้อ:"
    )
    add_step("1.", "ระดับความหวาน (Sweetness Level): ปรับได้ 4 ระดับ ได้แก่ ปกติ 100%, หวานน้อย 50%, หวานน้อยมาก 25%, และไม่หวานเลย 0% (No Sugar)")
    add_step("2.", "ประเภทนมทางเลือก (Milk Options): มีให้เลือกทั้ง นมสดฮอกไกโดแท้ (Hokkaido Fresh Milk), นมข้าวโอ๊ตบาริสต้า (Oat Milk +15 บ.), "
                    "และนมถั่วเหลืองออร์แกนิก (Soy Milk +10 บ.) สำหรับผู้ที่แพ้นมวัวหรือรับประทานมังสวิรัติ")
    add_step("3.", "การเลือกจำนวน (Quantity Selector): ระบุจำนวนแก้วที่ต้องการสั่งซื้อ โดยระบบจะตรวจสอบไม่ให้สั่งเกินจำนวนสต็อกที่มีอยู่จริงในคลัง")

    add_section_heading("2.4 ตะกร้าสินค้าและการคำนวณราคาภาษี (Shopping Cart & VAT Calculation)")
    p = doc.add_paragraph()
    p.add_run(
        "ระบบตะกร้าสินค้าของ I wendy Matcha คำนวณราคาสินค้าตามหลักการบัญชีที่ถูกต้องและโปร่งใส:"
    )
    add_step("1.", "การเพิ่มและปรับปรุงสินค้า: ลูกค้าสามารถเพิ่ม ลดจำนวน หรือลบรายการสินค้าในตะกร้าได้ตลอดเวลา")
    add_step("2.", "ปุ่มล้างตะกร้า (Clear Cart): กดเพื่อลบสินค้าทั้งหมดในคราวเดียว เพื่อเริ่มต้นสั่งซื้อใหม่")
    add_step("3.", "ราคารวมก่อนภาษี (Subtotal): ยอดรวมของราคาสินค้าทั้งหมดที่เลือกไว้ในตะกร้า")
    add_step("4.", "ภาษีมูลค่าเพิ่ม (VAT 7%): ระบบจะคำนวณภาษีมูลค่าเพิ่ม 7% จากยอดรวมสินค้าตามข้อกำหนดของกฎหมาย")
    add_step("5.", "ยอดรวมทั้งสิ้น (Grand Total): รวมค่าสินค้า ภาษีมูลค่าเพิ่ม และค่าจัดส่งสุทธิที่ลูกค้าต้องชำระ")

    add_section_heading("2.5 ระบบปักหมุด GPS และคำนวณค่าจัดส่งตามระยะทางจริง (GPS Distance Matrix)")
    p = doc.add_paragraph()
    p.add_run(
        "จุดเด่นสำคัญของระบบ I wendy Matcha คือการคำนวณค่าจัดส่งตามระยะทางจริงด้วยระบบพิกัดภูมิศาสตร์ (Haversine Formula) "
        "โดยอิงจากจุดเริ่มต้นที่ร้านตั้งอยู่ ณ มหาวิทยาลัยขอนแก่น (Central Khon Kaen Campus: ละติจูด 16.4322, ลองจิจูด 102.8236):"
    )
    add_step("1.", "การปักหมุดแผนที่ (Interactive Map): ลูกค้าสามารถคลิกปักหมุดบนแผนที่ หรือกดปุ่ม 'ใช้พิกัดปัจจุบันของฉัน' (Current GPS Location)")
    add_step("2.", "การคำนวณระยะทาง (Distance Calculation): ระบบคำนวณระยะห่างระหว่างร้านค้ากับพิกัดจัดส่งของลูกค้าเป็นกิโลเมตรแบบทศนิยม")
    add_step("3.", "สูตรการคิดค่าจัดส่ง (Delivery Fee Policy): "
                    "- ระยะทาง 0 - 3 กิโลเมตรแรก: คิดค่าบริการเริ่มต้น 20 บาท\n"
                    "- กิโลเมตรถัดไป: คิดเพิ่มกิโลเมตรละ 8 บาท\n"
                    "- โปรโมชั่นพิเศษ: หากสั่งซื้อยอดสินค้าครบ 500 บาทขึ้นไป จัดส่งฟรีทันที (Free Delivery)")
    add_step("4.", "ช่องระบุรายละเอียดที่อยู่: ลูกค้ากรอกบ้านเลขที่ ซอย ถนน และจุดสังเกตเพื่อความสะดวกแก่พนักงานจัดส่ง")

    add_section_heading("2.6 การชำระเงินด้วย QR Code PromptPay และการแนบสลิปโอนเงิน (QR Payment)")
    p = doc.add_paragraph()
    p.add_run(
        "ระบบรองรับการชำระเงินแบบไร้เงินสด (Cashless Payment) ผ่านมาตรฐาน QR PromptPay ของธนาคารแห่งประเทศไทย:"
    )
    add_step("1.", "แสดง QR Code พร้อมเพย์: เมื่อเข้าสู่ขั้นตอนชำระเงิน ระบบจะแสดง QR Code พร้อมระบุยอดเงินที่ต้องโอนสุทธิตรงตามบิล")
    add_step("2.", "การอัปโหลดสลิปโอนเงิน (Slip Upload): ลูกค้าทำการสแกนจ่ายเงินผ่านแอปพลิเคชันธนาคาร จากนั้นอัปโหลดไฟล์ภาพสลิปเข้าสู่ระบบ")
    add_step("3.", "ระบบตรวจสอบความถูกต้อง: หากลูกค้ายังไม่อัปโหลดภาพสลิป ระบบจะไม่อนุญาตให้กดยืนยันคำสั่งซื้อ เพื่อป้องกันออเดอร์ค้างชำระ")
    add_step("4.", "การบันทึกคำสั่งซื้อ: เมื่อแนบสลิปและกดยืนยัน ระบบจะส่งต่อข้อมูลไปยังแอดมินหลังบ้านเพื่อรอการตรวจสอบ และล้างตะกร้าสินค้าให้พร้อมสั่งครั้งถัดไป")

    add_section_heading("2.7 ใบเสร็จรับเงินอิเล็กทรอนิกส์ (E-Receipt Slip & Verification)")
    p = doc.add_paragraph()
    p.add_run(
        "เมื่อสั่งซื้อสำเร็จ ลูกค้าจะได้รับใบเสร็จรับเงินอิเล็กทรอนิกส์ที่มีดีไซน์คลาสสิกสวยงาม และมีรายละเอียดครบถ้วน:"
    )
    add_step("1.", "หัวใบเสร็จ: แสดงโลโก้ร้าน I wendy Matcha, ที่อยู่สาขา, เบอร์โทรศัพท์ และเลขประจำตัวผู้เสียภาษี")
    add_step("2.", "ข้อมูลคำสั่งซื้อ: เลขที่ออเดอร์ (Order No.), วันที่และเวลาที่สั่งซื้อ, ชื่อผู้สั่งซื้อ และเบอร์โทรศัพท์")
    add_step("3.", "ตารางรายการสินค้า: แสดงชื่อเมนู, ระดับความหวาน, ประเภทนม, จำนวนชิ้น, ราคาต่อหน่วย และราคารวมแต่ละบรรทัด")
    add_step("4.", "สรุปยอดเงิน: ยอดรวมสินค้า, ภาษีมูลค่าเพิ่ม 7%, ค่าจัดส่งตามระยะทาง, ส่วนลด (ถ้ามี) และยอดชำระสุทธิ")
    add_step("5.", "ปุ่มบันทึก/พิมพ์ใบเสร็จ: ลูกค้าสามารถคลิกปุ่ม 'พิมพ์ใบเสร็จ / บันทึกภาพ' เพื่อเก็บไว้เป็นหลักฐานการสั่งซื้อได้")

    add_section_heading("2.8 การติดตามสถานะคำสั่งซื้อแบบสด (Live Order Tracking & Stepper)")
    p = doc.add_paragraph()
    p.add_run(
        "ลูกค้าสามารถตรวจสอบสถานะคำสั่งซื้อได้ที่หน้า /order-status โดยระบบแสดงผลผ่านแถบกระบวนการ 4 ขั้นตอน (Order Stepper):"
    )
    add_step("1.", "ขั้นตอนที่ 1 - รับออเดอร์แล้ว (Order Placed): ออเดอร์และสลิปถูกส่งเข้าสู่ระบบ รอแอดมินตรวจสอบ")
    add_step("2.", "ขั้นตอนที่ 2 - ยืนยันการชำระเงินแล้ว (Payment Verified): แอดมินตรวจสอบสลิปถูกต้อง และบาริสต้ากำลังเริ่มชงชา")
    add_step("3.", "ขั้นตอนที่ 3 - กำลังจัดส่ง (Out for Delivery): พนักงานจัดส่งกำลังนำส่งเครื่องดื่มตามพิกัด GPS ของลูกค้า")
    add_step("4.", "ขั้นตอนที่ 4 - จัดส่งสำเร็จ (Completed): ลูกค้าได้รับเครื่องดื่มเรียบร้อยแล้ว และระบบเพิ่มแต้มสะสมให้บัญชีลูกค้าทันที")

    add_section_heading("2.9 ระบบสะสมแต้มสมาชิก (Loyalty Points System 10 ฟรี 1)")
    p = doc.add_paragraph()
    p.add_run(
        "เพื่อตอบแทนลูกค้าประจำ ร้าน I wendy Matcha มีแคมเปญสะสมแต้มอัตโนมัติ:"
    )
    add_step("1.", "เกณฑ์การได้รับแต้ม: ซื้อเครื่องดื่มมัทฉะครบทุกๆ 1 แก้ว จะได้รับแต้มสะสม 1 แต้ม (1 Glass = 1 Point)")
    add_step("2.", "การแสดงผลแต้มสะสม: ลูกค้าสามารถดูแต้มปัจจุบันได้จากปุ่มแคปซูลดาวสีทองบน Navbar หรือในหน้า Profile")
    add_step("3.", "สิทธิประโยชน์: เมื่อสะสมแต้มครบ 10 แต้ม ลูกค้าจะได้รับสิทธิ์แลกฟรีเครื่องดื่มมัทฉะ 1 แก้วทันทีในออเดอร์ถัดไป")

    add_section_heading("2.10 ข้อมูลส่วนตัวและการแก้ไขโปรไฟล์ (Member Profile)")
    p = doc.add_paragraph()
    p.add_run(
        "ลูกค้าสามารถจัดการข้อมูลบัญชีของตนเองได้ตลอด 24 ชั่วโมง ผ่านหน้า /profile โดยสามารถแก้ไขชื่อ-นามสกุล, "
        "เบอร์โทรศัพท์ติดต่อ, และที่อยู่จัดส่งเริ่มต้น เพื่อความสะดวกรวดเร็วในการสั่งซื้อครั้งต่อไป"
    )

    doc.add_page_break()

    # ----------------------------------------------------
    # CHAPTER 3: ADMIN MANAGEMENT SYSTEM
    # ----------------------------------------------------
    add_chapter_heading("บทที่ 3: ระบบผู้ดูแลระบบหลังบ้าน (Admin Management System)")

    add_section_heading("3.1 การเข้าสู่ระบบแอดมินและรหัสผ่านลับ (Admin Auth & Secret Portal)")
    p = doc.add_paragraph()
    p.add_run(
        "ระบบรักษาความปลอดภัยของหลังบ้าน I wendy Matcha มีการป้องกัน 2 ชั้น เพื่อป้องกันบุคคลภายนอกเข้าถึงข้อมูลร้านค้า:"
    )
    add_step("1.", "บัญชีผู้ดูแลระบบ (Admin Role): ผู้ใช้ต้องล็อกอินด้วยบัญชีที่มีฟิลด์ role = 'admin' ในฐานข้อมูล")
    add_step("2.", "ประตูลับสำหรับแอดมิน (/secret-admin): หน้ากรอกรหัสผ่านลับพิเศษเพื่อยกระดับสิทธิ์ผู้ใช้งานเป็นผู้ดูแลระบบทันที")
    add_step("3.", "แถบเมนูป้องกัน (Route Protection): ทุกเส้นทางหลังบ้านมีการตรวจสอบฟังก์ชัน require_admin() หากไม่ใช่แอดมิน ระบบจะ Redirect กลับหน้าแรกทันที")

    add_section_heading("3.2 แดชบอร์ดสรุปยอดขายและการวิเคราะห์ข้อมูล (Sales Analytics & KPI Bento Dashboard)")
    p = doc.add_paragraph()
    p.add_run(
        "หน้าแดชบอร์ดแอดมินได้รับการพัฒนาด้วยดีไซน์ Bento Grid สีสันสดใสตามธีมร้าน สรุปข้อมูลเชิงลึกทางธุรกิจได้อย่างมีประสิทธิภาพ:"
    )
    add_step("1.", "กล่องสถิติหลัก (KPI Cards): "
                    "- ยอดขายรวม (Total Revenue): แสดงรายได้สุทธิทั้งหมดที่ตรวจสอบแล้ว\n"
                    "- จำนวนคำสั่งซื้อ (Total Orders): จำนวนออเดอร์ทั้งหมดในระบบ\n"
                    "- ออเดอร์รอตรวจสอบ (Pending Verification): แจ้งเตือนสลิปที่ต้องเร่งตรวจสอบ\n"
                    "- สต็อกสินค้าคงเหลือ (Total Stock): สรุปจำนวนแก้วและชิ้นสินค้าในคลัง")
    add_step("2.", "ฟังก์ชันเลือกช่วงเวลาสรุปยอดขาย: "
                    "- วันนี้ (Today)\n"
                    "- สัปดาห์นี้ (This Week)\n"
                    "- เดือนนี้ (This Month)\n"
                    "- ปีนี้ (This Year)\n"
                    "- กำหนดช่วงวันเอง (Custom Date Range): มีระบบปฏิทินเลือกวันเริ่มต้นและวันสิ้นสุดได้อย่างอิสระ")
    add_step("3.", "กราฟแสดงแนวโน้มยอดขาย: แสดงยอดขายเปรียบเทียบในแต่ละช่วงเวลา ช่วยให้เจ้าของร้านวางแผนการเตรียมวัตถุดิบชาเขียวได้อย่างแม่นยำ")

    add_section_heading("3.3 การจัดการคำสั่งซื้อและตรวจสอบสลิป (Order Verification & Bell Notification)")
    p = doc.add_paragraph()
    p.add_run(
        "แอดมินสามารถจัดการออเดอร์ของลูกค้าได้อย่างรวดเร็วผ่านแท็บ 'จัดการคำสั่งซื้อ & สลิป':"
    )
    add_step("1.", "กระดิ่งแจ้งเตือนด่วน (Floating Bell): เมื่อมีคำสั่งซื้อใหม่ที่แนบสลิปเข้ามา กระดิ่งมุมขวาล่างจะมีตัวเลขแจ้งเตือนสีแดง "
                    "และเมื่อคลิกกระดิ่ง ระบบจะพุ่งตรงมายังตารางออเดอร์รอตรวจสอบสลิปทันที")
    add_step("2.", "ปุ่มตัวกรองสถานะ: แยกดูตามสถานะ 'ทั้งหมด', 'รอตรวจสอบสลิป', 'ชำระเงินแล้ว', 'จัดส่งสำเร็จ' หรือ 'ยกเลิก'")
    add_step("3.", "การตรวจสอบสลิป (View Slip Modal): แอดมินสามารถคลิกดูรูปสลิปขนาดใหญ่เพื่อเปรียบเทียบยอดเงิน วันที่ และเวลาโอนจริง")
    add_step("4.", "การอนุมัติสลิป: กดปุ่ม 'อนุมัติสลิป & เริ่มเตรียมสินค้า' เมื่อเงินเข้าบัญชีจริง หรือกด 'ปฏิเสธสลิป' หากภาพไม่ถูกต้อง")
    add_step("5.", "การอัปเดตการจัดส่ง: แอดมินสามารถเปลี่ยนสถานะเป็น 'กำลังจัดส่ง' และ 'จัดส่งสำเร็จ' เพื่อให้ลูกค้าติดตามสถานะได้แบบเรียลไทม์")

    add_section_heading("3.4 การจัดการคลังสินค้า สต็อก และเมนูสินค้า (Product & Inventory Management)")
    p = doc.add_paragraph()
    p.add_run(
        "แท็บ 'คลังสินค้า & เมนู' ช่วยให้ร้านค้าควบคุมสต็อกผงชาและเครื่องดื่มได้อย่างมีประสิทธิภาพ:"
    )
    add_step("1.", "การเพิ่มสินค้าใหม่ (Add Product): กรอกชื่อภาษาอังกฤษ, ชื่อภาษาไทย, หมวดหมู่, ระดับราคา, จำนวนสต็อก, คำอธิบาย Flavor Notes และอัปโหลดรูปภาพ")
    add_step("2.", "การแก้ไขเมนู (Edit Product): ปรับปรุงราคา ข้อมูล หรือรูปภาพสินค้าได้ตลอดเวลา")
    add_step("3.", "การเติมสต็อกด่วน (Quick Stock Update): มีปุ่มปรับเพิ่มจำนวนสินค้า (+10, +20, +50) เพื่อความรวดเร็วในการเปิดร้าน")
    add_step("4.", "การตั้งค่า Best Seller: ทำเครื่องหมายติดดาวให้สินค้าขายดี เพื่อนำไปแสดงในแถบ Best Sellers หน้าร้าน")
    add_step("5.", "การเปิด-ปิดการขาย (Toggle Status): ปรับสถานะเป็น 'หมดชั่วคราว' (Out of Stock) เพื่อระงับการสั่งซื้อเมนูที่วัตถุดิบหมด")

    add_section_heading("3.5 การจัดการข้อมูลสมาชิกและคะแนนสะสม (Member Management)")
    p = doc.add_paragraph()
    p.add_run(
        "แอดมินสามารถดูรายชื่อสมาชิกทั้งหมด ค้นหาตามชื่อ เบอร์โทร หรืออีเมล ตรวจสอบประวัติการสั่งซื้อ และแก้ไขแต้มสะสมของสมาชิกได้โดยตรง"
    )

    add_section_heading("3.6 การตั้งค่าข้อมูลร้านค้าและช่องทางติดต่อ (Store Settings)")
    p = doc.add_paragraph()
    p.add_run(
        "แอดมินสามารถกำหนดเบอร์โทรศัพท์ของร้านค้า บัญชีพร้อมเพย์สำหรับรับเงิน และข้อมูลพิกัดร้านค้า "
        "ซึ่งข้อมูลเหล่านี้จะถูกนำไปใช้อัตโนมัติในหน้าสั่งซื้อ หน้าติดต่อเรา และบนใบเสร็จรับเงิน"
    )

    doc.add_page_break()

    # ----------------------------------------------------
    # CHAPTER 4: DATABASE SCHEMA
    # ----------------------------------------------------
    add_chapter_heading("บทที่ 4: โครงสร้างฐานข้อมูลระบบ (SQLite Database Schema)")

    p = doc.add_paragraph()
    p.add_run(
        "ระบบ I wendy Matcha ใช้ฐานข้อมูล SQLite (ไฟล์ matcha_online.db) ซึ่งมีประสิทธิภาพสูง เบา และสะดวกต่อการสำรองข้อมูล "
        "โดยประกอบด้วยตารางข้อมูลหลักที่เชื่อมโยงความสัมพันธ์กัน ดังนี้:"
    )

    def create_schema_table(headers, rows_data):
        table = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        
        # Header Row
        hdr_cells = table.rows[0].cells
        for idx, header_text in enumerate(headers):
            hdr_cells[idx].text = header_text
            set_cell_background(hdr_cells[idx], "a9b762")
            set_cell_margins(hdr_cells[idx], top=100, bottom=100, left=120, right=120)
            p = hdr_cells[idx].paragraphs[0]
            p.runs[0].bold = True
            p.runs[0].font.name = "TH Sarabun PSK"
            p.runs[0].font.size = Pt(14)
            p.runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)
            
        # Data Rows
        for r_idx, row in enumerate(rows_data):
            row_cells = table.rows[r_idx + 1].cells
            bg_color = "ffffff" if r_idx % 2 == 0 else "f9fbf7"
            for c_idx, val in enumerate(row):
                row_cells[c_idx].text = str(val)
                set_cell_background(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=120, right=120)
                p = row_cells[c_idx].paragraphs[0]
                p.runs[0].font.name = "TH Sarabun PSK"
                p.runs[0].font.size = Pt(13)
                p.runs[0].font.color.rgb = RGBColor(0x22, 0x31, 0x1c)

        # Spacing after table
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(2)
        sp.paragraph_format.space_after = Pt(8)

    # 4.1 Users Table
    add_section_heading("4.1 ตารางข้อมูลผู้ใช้งาน (users)")
    p = doc.add_paragraph()
    p.add_run("ใช้สำหรับจัดเก็บข้อมูลบัญชีผู้ใช้งาน ทั้งสมาชิกลูกค้าทั่วไปและผู้ดูแลระบบ:")
    create_schema_table(
        ["ชื่อฟิลด์ (Field)", "ประเภทข้อมูล (Type)", "เงื่อนไข (Constraint)", "คำอธิบาย"],
        [
            ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "รหัสประจำตัวผู้ใช้งาน (ID อัตโนมัติ)"],
            ["username", "TEXT", "UNIQUE NOT NULL", "ชื่อบัญชีผู้ใช้สำหรับใช้เข้าสู่ระบบ"],
            ["password_hash", "TEXT", "NOT NULL", "รหัสผ่านที่ผ่านการเข้ารหัสความปลอดภัยทางเดียว (Hash)"],
            ["name", "TEXT", "NOT NULL", "ชื่อ-นามสกุลจริงของลูกค้า"],
            ["phone", "TEXT", "UNIQUE NOT NULL", "เบอร์โทรศัพท์ 10 หลักของลูกค้า"],
            ["email", "TEXT", "NULL", "อีเมลสำหรับใช้รับรหัส OTP รีเซ็ตรหัสผ่าน"],
            ["reset_otp", "TEXT", "NULL", "รหัส OTP 6 หลักสำหรับการกู้คืนรหัสผ่าน"],
            ["reset_otp_expiry", "TIMESTAMP", "NULL", "วันและเวลาหมดอายุของรหัส OTP (15 นาที)"],
            ["points", "INTEGER", "DEFAULT 0", "จำนวนแต้มสะสมของสมาชิก (ครบ 10 ฟรี 1)"],
            ["role", "TEXT", "DEFAULT 'customer'", "ระดับสิทธิ์ผู้ใช้ ('customer' หรือ 'admin')"],
            ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "วันและเวลาที่ลงทะเบียนเข้าใช้งาน"],
        ]
    )

    # 4.2 Products Table
    add_section_heading("4.2 ตารางข้อมูลสินค้าและสต็อก (products)")
    p = doc.add_paragraph()
    p.add_run("ใช้สำหรับบันทึกรายการสินค้า เมนูเครื่องดื่ม ผงชาเขียว เซ็ตอุปกรณ์ และจำนวนคงเหลือในคลัง:")
    create_schema_table(
        ["ชื่อฟิลด์ (Field)", "ประเภทข้อมูล (Type)", "เงื่อนไข (Constraint)", "คำอธิบาย"],
        [
            ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "รหัสประจำตัวสินค้า"],
            ["name", "TEXT", "NOT NULL", "ชื่อสินค้าภาษาอังกฤษ (เช่น Uji Hikari Latte)"],
            ["name_th", "TEXT", "NULL", "ชื่อสินค้าภาษาไทย (เช่น อูจิ ฮิคาริ มัทฉะลาเต้)"],
            ["category", "TEXT", "NOT NULL", "หมวดหมู่หลัก ('drink', 'powder', 'equipment')"],
            ["drink_category", "TEXT", "DEFAULT '-'", "ประเภทย่อยเครื่องดื่ม ('Pure', 'Latte', 'Fusion')"],
            ["has_milk_option", "INTEGER", "DEFAULT 0", "สิทธิ์เลือกประเภทนม (1 = มีตัวเลือกนม, 0 = ไม่มี)"],
            ["price", "REAL", "NOT NULL", "ราคาจำหน่ายต่อหน่วย (บาท)"],
            ["stock", "INTEGER", "NOT NULL DEFAULT 50", "จำนวนสินค้าคงเหลือในคลังสต็อก"],
            ["description", "TEXT", "NULL", "คำอธิบายสินค้า จุดเด่น และ Flavor Notes"],
            ["image_url", "TEXT", "NULL", "เส้นทางไฟล์รูปภาพสินค้า (Path)"],
            ["is_active", "INTEGER", "DEFAULT 1", "สถานะการขาย (1 = วางขายปกติ, 0 = หมดชั่วคราว)"],
            ["is_bestseller", "INTEGER", "DEFAULT 0", "สถานะสินค้าขายดี (1 = สินค้าติดดาวขายดี)"],
        ]
    )

    # 4.3 Orders Table
    add_section_heading("4.3 ตารางข้อมูลคำสั่งซื้อ (orders)")
    p = doc.add_paragraph()
    p.add_run("ใช้บันทึกประวัติการสั่งซื้อ ข้อมูลการจัดส่ง พิกัด GPS สลิปโอนเงิน และสถานะการชำระเงิน:")
    create_schema_table(
        ["ชื่อฟิลด์ (Field)", "ประเภทข้อมูล (Type)", "เงื่อนไข (Constraint)", "คำอธิบาย"],
        [
            ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "รหัสประจำตัวออเดอร์"],
            ["order_no", "TEXT", "UNIQUE NOT NULL", "เลขที่ใบสั่งซื้อ (เช่น ORD-20261029-XXXX)"],
            ["user_id", "INTEGER", "FOREIGN KEY -> users(id)", "รหัสลูกค้าที่ทำการสั่งซื้อ"],
            ["subtotal", "REAL", "NOT NULL", "ยอดรวมราคาสินค้าก่อนภาษีและค่าส่ง"],
            ["vat_amount", "REAL", "NOT NULL", "ภาษีมูลค่าเพิ่ม 7%"],
            ["discount_amount", "REAL", "DEFAULT 0", "ส่วนลดสิทธิพิเศษหรือแต้มสะสม"],
            ["delivery_fee", "REAL", "NOT NULL", "ค่าจัดส่งที่คำนวณตามระยะทาง GPS"],
            ["distance_km", "REAL", "NOT NULL", "ระยะทางคำนวณจริงจากร้านค้า (กิโลเมตร)"],
            ["customer_lat", "REAL", "NULL", "พิกัดละติจูดจุดจัดส่งของลูกค้า"],
            ["customer_lng", "REAL", "NULL", "พิกัดลองจิจูดจุดจัดส่งของลูกค้า"],
            ["address_note", "TEXT", "NOT NULL", "รายละเอียดที่อยู่จัดส่งและจุดสังเกต"],
            ["slip_filename", "TEXT", "NULL", "ชื่อไฟล์ภาพสลิปโอนเงิน PromptPay ที่อัปโหลด"],
            ["payment_status", "TEXT", "DEFAULT 'pending'", "สถานะชำระเงิน ('pending', 'verified', 'rejected')"],
            ["shipping_status", "TEXT", "DEFAULT 'preparing'", "สถานะจัดส่ง ('preparing', 'delivering', 'completed', 'cancelled')"],
            ["points_awarded", "INTEGER", "DEFAULT 0", "แต้มสะสมที่ได้รับจากออเดอร์นี้"],
            ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "วันและเวลาที่กดสั่งซื้อ"],
        ]
    )

    # 4.4 Order Items Table
    add_section_heading("4.4 ตารางข้อมูลรายการสินค้าในคำสั่งซื้อ (order_items)")
    p = doc.add_paragraph()
    p.add_run("ใช้บันทึกรายละเอียดของสินค้าแต่ละชิ้นในแต่ละบิลคำสั่งซื้อ พร้อมตัวเลือกรสชาติที่ลูกค้าเลือก:")
    create_schema_table(
        ["ชื่อฟิลด์ (Field)", "ประเภทข้อมูล (Type)", "เงื่อนไข (Constraint)", "คำอธิบาย"],
        [
            ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "รหัสประจำตัวรายการ"],
            ["order_id", "INTEGER", "FOREIGN KEY -> orders(id)", "รหัสออเดอร์ที่รายการนี้สังกัดอยู่"],
            ["product_id", "INTEGER", "FOREIGN KEY -> products(id)", "รหัสสินค้าที่สั่งซื้อ"],
            ["product_name", "TEXT", "NOT NULL", "ชื่อสินค้าภาษาอังกฤษ ณ เวลาสั่งซื้อ"],
            ["product_name_th", "TEXT", "NULL", "ชื่อสินค้าภาษาไทย"],
            ["price_per_unit", "REAL", "NOT NULL", "ราคาต่อหน่วย ณ เวลาสั่งซื้อ"],
            ["quantity", "INTEGER", "NOT NULL", "จำนวนชิ้นที่สั่ง"],
            ["sweetness", "TEXT", "DEFAULT '-'", "ระดับความหวานที่ลูกค้าเลือก (เช่น 50% หวานน้อย)"],
            ["milk_type", "TEXT", "DEFAULT '-'", "ประเภทนมที่ลูกค้าเลือก (เช่น นมโอ๊ต)"],
            ["total_price", "REAL", "NOT NULL", "ราคารวมของรายการนี้ (ราคา x จำนวน)"],
        ]
    )

    # 4.5 System Configuration
    add_section_heading("4.5 ข้อมูลการตั้งค่าระบบและค่าจัดส่ง (System Configuration & Constants)")
    p = doc.add_paragraph()
    p.add_run("ค่าคงที่และพารามิเตอร์การทำงานหลักของระบบ I wendy Matcha ที่กำหนดไว้ในโค้ดระบบ:")
    create_schema_table(
        ["ชื่อพารามิเตอร์ (Parameter)", "ค่าที่กำหนด (Value)", "คำอธิบายและการใช้งาน"],
        [
            ["STORE_NAME", "I wendy Matcha", "ชื่อแบรนด์ร้านค้า แสดงผลทั่วทั้งเว็บไซต์และใบเสร็จ"],
            ["STORE_PHONE", "081-234-5678", "เบอร์โทรศัพท์ติดต่อของร้านค้า"],
            ["STORE_LOCATION", "16.4322, 102.8236", "พิกัด GPS จุดเริ่มต้นคำนวณค่าส่ง (Central Khon Kaen Campus)"],
            ["PROMPTPAY_NUMBER", "081-234-5678", "หมายเลขพร้อมเพย์สำหรับสร้าง QR Code รับเงิน"],
            ["BASE_DELIVERY_FEE", "20.00 บาท", "ค่าจัดส่งเริ่มต้นในระยะ 3 กิโลเมตรแรก"],
            ["FEE_PER_KM", "8.00 บาท / กม.", "อัตราค่าจัดส่งส่วนเพิ่มต่อกิโลเมตร"],
            ["FREE_DELIVERY_THRESHOLD", "500.00 บาท", "ยอดสั่งซื้อขั้นต่ำที่ได้รับสิทธิ์จัดส่งฟรี"],
            ["VAT_RATE", "0.07 (7%)", "อัตราภาษีมูลค่าเพิ่มคำนวณในระบบ"],
            ["LOYALTY_GOAL", "10 แต้ม", "จำนวนแต้มสะสมเพื่อรับสิทธิ์แลกเครื่องดื่มฟรี 1 แก้ว"],
        ]
    )

    # Save Document
    target_path = 'static/docs/manual_i_wendy_matcha.docx'
    doc.save(target_path)
    print(f"Word Document created successfully at: {target_path}")

if __name__ == '__main__':
    build_manual_docx()
