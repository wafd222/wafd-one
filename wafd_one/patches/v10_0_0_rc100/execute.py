from __future__ import annotations

import frappe
from frappe.utils import now_datetime


INGREDIENTS = [
    # name, category, uom, storage, source note
    ("زبادي", "ألبان / Dairy", "حبة / Piece", "مبرد / Chilled", "يُختار النوع والشركة حسب العقد وآخر فاتورة مورد"),
    ("تمر", "فواكه / Fruits", "حبة / Piece", "جاف / Dry", "سكرية القصيم أو عجوة؛ 5 حبات للوجبة حسب العقد"),
    ("ماء 330 مل", "مشروبات / Beverages", "حبة / Piece", "درجة حرارة الغرفة / Ambient", "مياه شرب معبأة 330 مل"),
    ("ماء زمزم 330 مل", "مشروبات / Beverages", "حبة / Piece", "درجة حرارة الغرفة / Ambient", "إضافة اختيارية؛ السعر المرجعي التشغيلي 1.50 ريال ويُحدّث من آخر فاتورة"),
    ("دقة مدينية", "بهارات وصلصات / Spices & Sauces", "حبة / Piece", "جاف / Dry", "عبوة فردية حسب المواصفة المعتمدة"),
    ("ملعقة", "تغليف / Packaging", "حبة / Piece", "جاف / Dry", "أداة أحادية الاستخدام بدرجة غذائية"),
    ("منديل معطر", "تعقيم وسلامة / Hygiene & Safety", "حبة / Piece", "جاف / Dry", "منديل فردي مغلف"),
    ("خبز فتوت", "مخبوزات / Bakery", "حبة / Piece", "حسب تعليمات المصنع / Manufacturer Instructions", "حسب المورد وتاريخ الإنتاج"),
    ("سفرة", "أدوات تشغيل / Operating Supplies", "حبة / Piece", "جاف / Dry", "إلزامية لكل صاحب سفرة/نقطة توزيع حسب خطة التشغيل"),
    ("غلاف إفطار صائم", "تغليف / Packaging", "حبة / Piece", "جاف / Dry", "الغلاف المعتمد للجهة والموقع"),
    ("غلاف شركة وفد المدينة", "تغليف / Packaging", "حبة / Piece", "جاف / Dry", "غلاف توزيع تشغيلي داخلي"),
    ("معمول", "حلويات / Desserts", "حبة / Piece", "جاف / Dry", "إضافة اختيارية حسب العقد"),
    ("لوزين", "حلويات / Desserts", "حبة / Piece", "جاف / Dry", "إضافة اختيارية حسب العقد"),
    ("مكسرات", "فواكه / Fruits", "جرام / Gram", "جاف / Dry", "إضافة اختيارية مع تعريف مسببات الحساسية"),
    ("فواكه مجففة", "فواكه / Fruits", "جرام / Gram", "جاف / Dry", "إضافة اختيارية"),
    ("أكياس نفايات", "منظفات / Cleaning", "حبة / Piece", "جاف / Dry", "تكلفة تشغيل للمشروع وليست مكونًا غذائيًا"),
]


def _ensure_ingredients():
    if not frappe.db.exists("DocType", "WAFD Ingredient"):
        return
    for name, category, uom, storage, note in INGREDIENTS:
        existing = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": name}, "name")
        values = {
            "category": category,
            "uom": uom,
            "storage_condition": storage,
            "status": "نشط / Active",
            "source_authority": "تشغيل شركة وفد المدينة + متطلبات سلامة الغذاء السعودية",
            "verification_status": "تشغيلي داخلي / Internal Operational",
            "source_notes": note,
            "cost_basis": "آخر فاتورة مورد / Latest Supplier Invoice",
            "cost_confidence": "متوسطة / Medium",
            "cost_last_updated": now_datetime(),
        }
        if name == "ماء زمزم 330 مل":
            values.update({
                "latest_market_cost": 1.50,
                "latest_price_source": "سعر تشغيلي مرجعي مقدم من الشركة؛ يجب تحديثه من فاتورة المورد",
            })
        if existing:
            frappe.db.set_value("WAFD Ingredient", existing, values, update_modified=False)
        else:
            frappe.get_doc({"doctype": "WAFD Ingredient", "ingredient_name": name, **values}).insert(ignore_permissions=True)


def execute():
    _ensure_ingredients()
    frappe.clear_cache()
