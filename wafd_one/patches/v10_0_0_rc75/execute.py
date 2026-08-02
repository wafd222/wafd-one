import frappe
from frappe.utils import nowdate

NATIONALITIES = [
    ("سعودي / Saudi", "SA", "Saudi Arabia", "العربية"),
    ("إندونيسي / Indonesian", "ID", "Indonesia", "Bahasa Indonesia"),
    ("هندي / Indian", "IN", "India", "Hindi / English"),
    ("باكستاني / Pakistani", "PK", "Pakistan", "Urdu"),
    ("بنغلاديشي / Bangladeshi", "BD", "Bangladesh", "Bengali"),
    ("ماليزي / Malaysian", "MY", "Malaysia", "Bahasa Melayu"),
    ("نيجيري / Nigerian", "NG", "Nigeria", "English"),
    ("مالي / Malian", "ML", "Mali", "Français"),
    ("تركي / Turkish", "TR", "Türkiye", "Türkçe"),
    ("أوزبكي / Uzbek", "UZ", "Uzbekistan", "Oʻzbek"),
    ("مصري / Egyptian", "EG", "Egypt", "العربية"),
    ("سوداني / Sudanese", "SD", "Sudan", "العربية"),
    ("يمني / Yemeni", "YE", "Yemen", "العربية"),
    ("مغربي / Moroccan", "MA", "Morocco", "العربية / Français"),
    ("جزائري / Algerian", "DZ", "Algeria", "العربية / Français"),
    ("تونسي / Tunisian", "TN", "Tunisia", "العربية / Français"),
    ("سنغالي / Senegalese", "SN", "Senegal", "Français"),
    ("أفغاني / Afghan", "AF", "Afghanistan", "Dari / Pashto"),
    ("فلبيني / Filipino", "PH", "Philippines", "Filipino / English"),
    ("تايلندي / Thai", "TH", "Thailand", "Thai"),
]

IFTAR_METADATA = {
    "إفطار صائم — المسجد النبوي": "محتوى تشغيلي مستند إلى وصف وكالة الأنباء السعودية لوجبة المسجد النبوي: ماء، سبع تمرات، لبن/زبادي، ودقة؛ أضيف الخبز وأدوات التعبئة وفق نموذج وفد المدينة.",
    "إفطار صائم — مسجد قباء": "نموذج تشغيلي للمساجد التاريخية؛ يجب مطابقته مع الأصناف المعتمدة في تصريح هيئة تطوير المدينة المنورة قبل الموسم.",
    "إفطار صائم — مسجد القبلتين": "نموذج تشغيلي للمساجد التاريخية؛ يجب مطابقته مع الأصناف المعتمدة في تصريح هيئة تطوير المدينة المنورة قبل الموسم.",
    "إفطار صائم — مسجد الميقات": "نموذج تشغيلي للمساجد التاريخية؛ يجب مطابقته مع الأصناف المعتمدة في تصريح هيئة تطوير المدينة المنورة قبل الموسم.",
}

def execute():
    if frappe.db.exists("DocType", "WAFD Nationality"):
        for name, code, country_en, language in NATIONALITIES:
            if not frappe.db.exists("WAFD Nationality", name):
                frappe.get_doc({"doctype":"WAFD Nationality","nationality_name":name,"country_code":code,"country_name_en":country_en,"default_language":language,"status":"نشطة / Active"}).insert(ignore_permissions=True)

    # The Indonesian mission must always be available in the mission selector.
    mission_name = "البعثة الإندونيسية للحج"
    if frappe.db.exists("DocType", "WAFD Mission") and not frappe.db.exists("WAFD Mission", {"mission_name": mission_name}):
        frappe.get_doc({"doctype":"WAFD Mission","mission_name":mission_name,"official_name":"مكتب شؤون الحج الإندونيسي / Indonesian Hajj Affairs Office","country":"إندونيسيا","mission_type":"مكتب شؤون حجاج / Hajj Affairs Office","address":"المدينة المنورة","status":"نشط / Active","verification_status":"يحتاج مراجعة / Needs Review","source_notes":"أضيف لضمان توفر البعثة في التشغيل؛ تستكمل بيانات الاتصال من العقد أو المصدر الرسمي المعتمد."}).insert(ignore_permissions=True)

    # Install/refresh reference recipes first, then add source and costing assumptions.
    from wafd_one.master_data import load_reference_master_data
    load_reference_master_data()
    for recipe_name, notes in IFTAR_METADATA.items():
        if not frappe.db.exists("WAFD Recipe", recipe_name):
            continue
        doc = frappe.get_doc("WAFD Recipe", recipe_name)
        doc.source_authority = "وكالة الأنباء السعودية / هيئة تطوير منطقة المدينة المنورة"
        doc.verification_status = "تشغيلي داخلي / Internal Operational"
        doc.last_verified_on = nowdate()
        doc.source_notes = notes + " أسعار التكلفة تقديرية من أسعار المكونات القياسية داخل النظام وتُحدّث تلقائياً بأسعار الشراء الفعلية."
        doc.food_safety_notes = "الالتزام بدرجات الحفظ والنقل والنظافة وتاريخ الصلاحية، وعدم اعتماد الإنتاج قبل مراجعة تصريح الموقع واشتراطات سلامة الغذاء للموسم."
        doc.packaging_cost_per_portion = 0
        doc.labor_cost_per_portion = 0.35
        doc.utilities_cost_per_portion = 0.08
        doc.delivery_cost_per_portion = 0.25
        doc.waste_percent = 2
        doc.overhead_percent = 8
        doc.profit_margin_percent = 15
        doc.save(ignore_permissions=True)
    frappe.clear_cache()
