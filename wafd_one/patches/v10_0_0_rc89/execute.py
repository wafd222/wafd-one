from __future__ import annotations

import frappe

from wafd_one.finance import refresh_project_financials
from wafd_one.master_data import load_reference_master_data


EXTRA_INGREDIENTS = [
    ("منظف أرضيات مركز", "CLN-FLOOR", "منظفات / Cleaning", "لتر / Liter", "مستودع 7 - أدوات النظافة"),
    ("مطهر أسطح غذائي", "CLN-SURFACE", "منظفات / Cleaning", "لتر / Liter", "مستودع 7 - أدوات النظافة"),
    ("سائل غسيل الصحون", "CLN-DISH", "منظفات / Cleaning", "لتر / Liter", "مستودع 7 - أدوات النظافة"),
    ("مزيل دهون المطابخ", "CLN-DEGREASER", "منظفات / Cleaning", "لتر / Liter", "مستودع 7 - أدوات النظافة"),
    ("كلور غذائي مخفف", "CLN-CHLORINE", "منظفات / Cleaning", "لتر / Liter", "مستودع 7 - أدوات النظافة"),
    ("صابون يدين سائل", "CLN-HANDSOAP", "منظفات / Cleaning", "لتر / Liter", "مستودع 7 - أدوات النظافة"),
    ("معقم يدين", "CLN-SANITIZER", "منظفات / Cleaning", "لتر / Liter", "مستودع 7 - أدوات النظافة"),
    ("قفازات نيتريل", "CLN-GLOVES", "تعقيم وسلامة / Hygiene & Safety", "صندوق / Box", "مستودع 7 - أدوات النظافة"),
    ("أكياس نفايات كبيرة", "CLN-BAGS-L", "منظفات / Cleaning", "كرتون / Carton", "مستودع 7 - أدوات النظافة"),
    ("مناديل تنظيف رول", "CLN-WIPES", "منظفات / Cleaning", "كرتون / Carton", "مستودع 7 - أدوات النظافة"),
    ("إسفنجة تنظيف", "CLN-SPONGE", "أدوات تشغيل / Operating Supplies", "حبة / Piece", "مستودع 7 - أدوات النظافة"),
    ("سلك تنظيف ستانلس", "CLN-SCOURER", "أدوات تشغيل / Operating Supplies", "حبة / Piece", "مستودع 7 - أدوات النظافة"),
    ("ممسحة أرضيات", "CLN-MOP", "أدوات تشغيل / Operating Supplies", "حبة / Piece", "مستودع 7 - أدوات النظافة"),
    ("فرشاة تنظيف", "CLN-BRUSH", "أدوات تشغيل / Operating Supplies", "حبة / Piece", "مستودع 7 - أدوات النظافة"),
    ("غطاء رأس استخدام واحد", "CLN-HAIRNET", "تعقيم وسلامة / Hygiene & Safety", "صندوق / Box", "مستودع 7 - أدوات النظافة"),
    ("كمامة استخدام واحد", "CLN-MASK", "تعقيم وسلامة / Hygiene & Safety", "صندوق / Box", "مستودع 7 - أدوات النظافة"),
    ("مريلة استخدام واحد", "CLN-APRON", "تعقيم وسلامة / Hygiene & Safety", "صندوق / Box", "مستودع 7 - أدوات النظافة"),
    ("مقياس تركيز المطهر", "CLN-TESTSTRIP", "تعقيم وسلامة / Hygiene & Safety", "صندوق / Box", "مستودع 7 - أدوات النظافة"),
    ("بازلاء", "PEAS", "خضار / Vegetables", "كجم / Kg", "ثلاجة 1 - الخضار والفواكه"),
]

EXTRA_RECIPES = [
    ("أرز جولوف بالدجاج", "غداء / Lunch", "غرب إفريقي / West African", "نيجيريا، غانا، غامبيا", [("أرز بسمتي",18),("دجاج كامل مبرد",45),("طماطم",6),("بصل",4),("معجون طماطم",3),("فلفل حار",0.5)]),
    ("أرز جولوف باللحم", "غداء / Lunch", "غرب إفريقي / West African", "نيجيريا، غانا، مالي", [("أرز بسمتي",18),("لحم بقري",22),("طماطم",6),("بصل",4),("معجون طماطم",3)]),
    ("مافِه لحم بالفول السوداني", "غداء / Lunch", "غرب إفريقي / West African", "مالي، السنغال، غينيا", [("لحم بقري",22),("بطاطس",10),("جزر",5),("طماطم",4),("بصل",3)]),
    ("ياسا دجاج", "غداء / Lunch", "غرب إفريقي / West African", "السنغال، مالي، غامبيا", [("دجاج كامل مبرد",45),("بصل",8),("ليمون",5),("أرز بسمتي",17)]),
    ("أرز مقلي إندونيسي", "عشاء / Dinner", "إندونيسي / Indonesian", "إندونيسيا، ماليزيا", [("أرز ياسمين",18),("صدور دجاج",18),("بيض",80),("صلصة صويا",3),("جزر",3),("بصل",3)]),
    ("مي جورينغ بالدجاج", "عشاء / Dinner", "إندونيسي / Indonesian", "إندونيسيا، ماليزيا", [("مكرونة",16),("صدور دجاج",20),("صلصة صويا",3),("جزر",3),("فلفل رومي",2)]),
    ("سوتو دجاج مع الأرز", "غداء / Lunch", "إندونيسي / Indonesian", "إندونيسيا", [("دجاج كامل مبرد",40),("أرز ياسمين",15),("بطاطس",8),("بصل",3),("ثوم",1),("زنجبيل",1)]),
    ("قورمة دجاج باكستانية", "غداء / Lunch", "باكستاني / Pakistani", "باكستان، الهند", [("صدور دجاج",24),("زبادي",10),("بصل",5),("طماطم",3),("زنجبيل",1),("ثوم",1)]),
    ("نهاري لحم", "غداء / Lunch", "باكستاني / Pakistani", "باكستان، الهند", [("لحم بقري",25),("بصل",4),("دقيق أبيض",2),("زنجبيل",1),("ثوم",1),("خبز نان",100)]),
    ("تشانا ماسالا", "عشاء / Dinner", "هندي / Indian", "الهند، باكستان، بنغلاديش", [("حمص حب",13),("طماطم",5),("بصل",4),("زنجبيل",0.7),("ثوم",0.7),("كركم",0.25)]),
    ("خيشدي عدس وأرز", "عشاء / Dinner", "جنوب آسيوي / South Asian", "الهند، بنغلاديش، باكستان", [("أرز بسمتي",12),("عدس أحمر",8),("بصل",3),("طماطم",3),("كركم",0.2)]),
    ("أرز بسمتي بالخضار", "غداء / Lunch", "نباتي / Vegetarian", "جميع البعثات", [("أرز بسمتي",18),("جزر",4),("فاصوليا خضراء",3),("بازلاء",3),("فلفل رومي",2)]),
    ("مكرونة خضار نباتية", "عشاء / Dinner", "نباتي / Vegetarian", "جميع البعثات", [("مكرونة",16),("طماطم",5),("كوسة",4),("فلفل رومي",3),("بصل",3)]),
    ("دجاج بصوص الليمون والأعشاب", "غداء / Lunch", "عالمي / International", "الشركات والبعثات الأوروبية", [("صدور دجاج",24),("ليمون",4),("بطاطس",12),("ثوم",1),("بقدونس",1)]),
    ("لحم بالخضار وصوص الصويا", "غداء / Lunch", "آسيوي / Asian", "الصين وشرق آسيا", [("لحم بقري",22),("بروكلي",7),("جزر",4),("فلفل رومي",3),("صلصة صويا",3)]),
    ("سمك مشوي بالأرز والخضار", "غداء / Lunch", "عالمي / International", "جميع البعثات", [("سمك فيليه",25),("أرز بسمتي",17),("جزر",4),("كوسة",4),("ليمون",3)]),
    ("إفطار جنوب آسيوي", "إفطار / Breakfast", "جنوب آسيوي / South Asian", "الهند، باكستان، بنغلاديش", [("بيض",100),("حمص حب",8),("خبز نان",100),("شاي",300),("ماء 330 مل",100)]),
    ("إفطار إندونيسي", "إفطار / Breakfast", "إندونيسي / Indonesian", "إندونيسيا، ماليزيا", [("أرز ياسمين",10),("بيض",100),("صدور دجاج",10),("خيار",4),("شاي",300)]),
    ("إفطار إفريقي", "إفطار / Breakfast", "إفريقي / African", "بعثات إفريقيا", [("بيض",100),("فول",10),("خبز عربي",120),("موز",12),("شاي",300)]),
    ("وجبة خفيفة للحافلات", "وجبة خفيفة / Snack", "عام / General", "جميع البعثات", [("كيك فردي",100),("عصير 200 مل",100),("ماء 330 مل",100),("منديل معطر",100),("كيس ورقي",100)]),
    ("وجبة استقبال دولية", "غداء / Lunch", "عام / General", "جميع البعثات والشركات", [("أرز بسمتي",17),("دجاج كامل مبرد",45),("سلطة خضراء",1),("عصير 200 مل",100),("ماء 330 مل",100)]),
    ("بوفيه بعثات آسيوي", "بوفيه / Buffet", "آسيوي / Asian", "بعثات آسيا", [("أرز ياسمين",14),("صدور دجاج",22),("لحم بقري",14),("مكرونة",8),("خيار",5),("عصير 200 مل",100)]),
    ("بوفيه بعثات إفريقي", "بوفيه / Buffet", "إفريقي / African", "بعثات إفريقيا", [("أرز بسمتي",16),("دجاج كامل مبرد",40),("لحم بقري",15),("بطاطس",10),("طماطم",6),("عصير 200 مل",100)]),
    ("سحور متوازن", "إفطار / Breakfast", "عام / General", "شركات وبعثات رمضان", [("أرز بسمتي",12),("صدور دجاج",18),("زبادي",100),("موز",12),("ماء 330 مل",100)]),
]


def _ensure_extra_ingredients():
    if not frappe.db.exists("DocType", "WAFD Ingredient"):
        return 0
    count = 0
    for name, code, category, uom, warehouse in EXTRA_INGREDIENTS:
        if frappe.db.exists("WAFD Ingredient", {"ingredient_name": name}):
            continue
        frappe.get_doc({
            "doctype": "WAFD Ingredient",
            "ingredient_name": name,
            "item_code": code,
            "category": category,
            "uom": uom,
            "standard_cost": 0,
            "minimum_stock": 0,
            "preferred_warehouse": warehouse if frappe.db.exists("WAFD Warehouse", warehouse) else None,
            "status": "نشط / Active",
        }).insert(ignore_permissions=True)
        count += 1
    return count


def _ensure_extra_recipes():
    if not frappe.db.exists("DocType", "WAFD Recipe"):
        return 0

    # Keep imported recipe categories strictly within the Select options of
    # WAFD Recipe.  Suhoor is operationally treated as breakfast until the
    # recipe DocType formally supports it, preventing migrate validation errors.
    field = frappe.get_meta("WAFD Recipe").get_field("meal_category")
    allowed_categories = {
        row.strip() for row in (field.options or "").splitlines() if row.strip()
    } if field else set()
    category_aliases = {
        "سحور / Suhoor": "إفطار / Breakfast",
    }

    count = 0
    for name, category, cuisine, nationalities, items in EXTRA_RECIPES:
        category = category_aliases.get(category, category)
        if allowed_categories and category not in allowed_categories:
            frappe.log_error(
                f"Skipped recipe {name}: unsupported category {category}",
                "RC89 recipe category validation",
            )
            continue
        if frappe.db.exists("WAFD Recipe", {"recipe_name": name}):
            continue
        doc = frappe.get_doc({
            "doctype": "WAFD Recipe",
            "recipe_name": name,
            "meal_category": category,
            "yield_quantity": 100,
            "status": "نشطة / Active",
            "cuisine": cuisine,
            "suitable_nationalities": nationalities,
            "verification_status": "تشغيلي داخلي / Internal Operational",
            "source_notes": "مرجع تشغيلي داخلي لبعثات الحج والشركات؛ تعتمد الكميات النهائية بعد تذوق واعتماد ممثل العميل.",
            "instructions": "وصفة مرجعية لعدد 100 حصة قابلة للتعديل حسب العقد والجنسية والحساسية الغذائية.",
            "items": [],
        })
        for ingredient, quantity in items:
            if frappe.db.exists("WAFD Ingredient", ingredient):
                doc.append("items", {"ingredient": ingredient, "quantity": quantity})
        doc.insert(ignore_permissions=True)
        count += 1
    return count


def execute():
    # RC78 creates the bilingual WAFD Nationality master. Reload it first and
    # ensure Indonesia exists before inserting missions through the master loader.
    # This prevents LinkValidationError when an older site has an incomplete
    # nationality master.
    if frappe.db.exists("DocType", "WAFD Nationality"):
        if not frappe.db.get_value("WAFD Nationality", {"country_name_ar": "إندونيسيا"}, "name"):
            frappe.get_doc({
                "doctype": "WAFD Nationality",
                "nationality_name": "إندونيسيا / Indonesia",
                "country_name_ar": "إندونيسيا",
                "country_name_en": "Indonesia",
                "iso2": "ID",
                "iso3": "IDN",
                "is_hajj_source": 1,
                "enabled": 1,
            }).insert(ignore_permissions=True)

    # Re-run the idempotent master loader so every active warehouse, including
    # cleaning supplies, is present without overwriting user data.
    load_reference_master_data()
    _ensure_extra_ingredients()
    _ensure_extra_recipes()

    if frappe.db.exists("DocType", "WAFD Catering Project"):
        for name in frappe.get_all("WAFD Catering Project", pluck="name"):
            try:
                refresh_project_financials(name)
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"RC89 financial refresh: {name}")
    frappe.clear_cache()
