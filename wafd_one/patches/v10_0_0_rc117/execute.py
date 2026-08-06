import frappe

PRICES = {'زبادي': 1.15, 'تمر': 0.25, 'ماء 330 مل': 0.62, 'ماء زمزم 330 مل': 1.5, 'دقة مدينية': 0.04, 'ملعقة': 0.04, 'منديل معطر': 0.12, 'خبز فتوت': 0.45, 'غلاف إفطار صائم': 0.12, 'غلاف شركة وفد المدينة': 0.1, 'معمول': 0.75, 'فواكه مجففة': 1.2, 'مكسرات مشكلة': 1.5, 'لوزين': 0.6, 'عصير برتقال 200 مل': 1.2, 'عصير تفاح 200 مل': 1.6}

def execute():
    for ingredient, price in PRICES.items():
        name = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": ingredient}, "name")
        if not name:
            doc = frappe.get_doc({"doctype":"WAFD Ingredient","ingredient_name":ingredient,"uom":"حبة / Piece","standard_cost":price,"latest_market_cost":price,"latest_price_source":"سعر مرجعي سعودي 2026 / Saudi reference 2026","cost_basis":"مرجعي قابل للتعديل / Editable reference"})
            doc.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("WAFD Ingredient", name, {"standard_cost":price,"latest_market_cost":price,"latest_price_source":"سعر مرجعي سعودي 2026 / Saudi reference 2026","cost_basis":"مرجعي قابل للتعديل / Editable reference"}, update_modified=False)
