import frappe

CATEGORY_OPTIONS = "\n".join([
    "إفطار / Breakfast", "غداء / Lunch", "عشاء / Dinner", "سحور / Suhoor",
    "إفطار رمضان / Ramadan Iftar", "وجبة ترحيبية / Welcome Meal",
    "كوفي بريك / Coffee Break", "بوفيه / Buffet", "وجبة خفيفة / Snack",
])
SERVICE_OPTIONS = "\n".join([
    "إفطار / Breakfast", "غداء / Lunch", "عشاء / Dinner", "سحور / Suhoor",
    "إفطار رمضان / Ramadan Iftar", "كوفي بريك / Coffee Break", "بوفيه / Buffet",
    "وجبة ترحيبية / Welcome Meal", "أخرى / Other",
])

WELCOME = [
    ("وجبة ترحيبية إندونيسية", "إندونيسي / Indonesian"),
    ("وجبة ترحيبية هندية", "هندي / Indian"),
    ("وجبة ترحيبية باكستانية", "باكستاني / Pakistani"),
    ("وجبة ترحيبية ماليزية", "ماليزي / Malaysian"),
    ("وجبة ترحيبية إفريقية", "إفريقي / African"),
    ("وجبة ترحيبية عربية", "عربي / Arabic"),
    ("وجبة ترحيبية VIP", "عالمي / International"),
]
SUHOOR = ["سحور متوازن", "سحور آسيوي", "سحور عربي", "سحور هندي", "سحور إندونيسي"]
RAMADAN = ["إفطار رمضان اقتصادي", "إفطار رمضان قياسي", "إفطار رمضان فاخر", "إفطار رمضان آسيوي", "إفطار رمضان عربي"]


def _set_select_options(doctype, fieldname, options):
    if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
        return
    frappe.db.set_value("DocField", {"parent": doctype, "fieldname": fieldname}, "options", options, update_modified=False)


def _ensure_recipe(name, category, cuisine="عام / General"):
    if frappe.db.exists("WAFD Recipe", name):
        frappe.db.set_value("WAFD Recipe", name, {"meal_category": category, "status": "نشطة / Active"}, update_modified=False)
        return
    frappe.get_doc({
        "doctype": "WAFD Recipe", "recipe_name": name, "meal_category": category,
        "yield_quantity": 100, "status": "نشطة / Active", "cuisine": cuisine,
        "instructions": "وصفة تشغيلية مرجعية قابلة للتعديل حسب العقد والبعثة.",
    }).insert(ignore_permissions=True)


def execute():
    _set_select_options("WAFD Recipe", "meal_category", CATEGORY_OPTIONS)
    _set_select_options("WAFD Project Service", "service_type", SERVICE_OPTIONS)
    for old in ("إفطار صائم / Iftar", "إفطار صائم / Iftar Saem"):
        frappe.db.sql("update `tabWAFD Recipe` set meal_category=%s where meal_category=%s", ("إفطار رمضان / Ramadan Iftar", old))
        frappe.db.sql("update `tabWAFD Project Service` set service_type=%s where service_type=%s", ("إفطار رمضان / Ramadan Iftar", old))
    # Previously-created suhoor references were stored under breakfast; move only clearly named suhoor recipes.
    frappe.db.sql("update `tabWAFD Recipe` set meal_category=%s where recipe_name like %s", ("سحور / Suhoor", "%سحور%"))
    for name in SUHOOR: _ensure_recipe(name, "سحور / Suhoor")
    for name in RAMADAN: _ensure_recipe(name, "إفطار رمضان / Ramadan Iftar")
    for name, cuisine in WELCOME: _ensure_recipe(name, "وجبة ترحيبية / Welcome Meal", cuisine)
    frappe.clear_cache()
