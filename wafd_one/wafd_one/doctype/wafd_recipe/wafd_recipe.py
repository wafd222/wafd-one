import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class WAFDRecipe(Document):
    def validate(self):
        yield_qty = flt(self.yield_quantity)
        if yield_qty <= 0:
            frappe.throw("عدد الحصص يجب أن يكون أكبر من صفر / Yield must be greater than zero")

        for fieldname, label in (
            ("waste_percent", "نسبة الهدر / Waste percentage"),
            ("overhead_percent", "نسبة المصاريف غير المباشرة / Overhead percentage"),
            ("profit_margin_percent", "هامش الربح / Profit margin"),
        ):
            value = flt(self.get(fieldname))
            if value < 0:
                frappe.throw(f"{label} لا يمكن أن تكون سالبة / cannot be negative")
            if fieldname == "profit_margin_percent" and value >= 100:
                frappe.throw("هامش الربح يجب أن يكون أقل من 100% / Profit margin must be below 100%")

        direct_total = 0.0
        seen = set()
        for row in self.items or []:
            if not row.ingredient:
                continue
            if row.ingredient in seen:
                frappe.throw(f"المكون مكرر في الوصفة: {row.ingredient} / Duplicate ingredient")
            seen.add(row.ingredient)
            if flt(row.quantity) <= 0:
                frappe.throw(f"كمية المكون يجب أن تكون أكبر من صفر: {row.ingredient}")
            ingredient = frappe.db.get_value(
                "WAFD Ingredient", row.ingredient, ["uom", "standard_cost", "status"], as_dict=True
            )
            if not ingredient:
                frappe.throw(f"المكون غير موجود: {row.ingredient} / Ingredient not found")
            if ingredient.status == "غير نشط / Inactive":
                frappe.throw(f"المكون غير نشط: {row.ingredient} / Ingredient is inactive")
            row.uom = ingredient.uom
            row.unit_cost = flt(ingredient.standard_cost)
            row.amount = flt(row.quantity) * flt(row.unit_cost)
            direct_total += flt(row.amount)

        direct_per_portion = direct_total / yield_qty
        waste_cost = direct_per_portion * flt(self.waste_percent) / 100
        subtotal = (
            direct_per_portion
            + waste_cost
            + flt(self.packaging_cost_per_portion)
            + flt(self.labor_cost_per_portion)
            + flt(self.utilities_cost_per_portion)
            + flt(self.delivery_cost_per_portion)
        )
        overhead = subtotal * flt(self.overhead_percent) / 100
        full_cost = subtotal + overhead
        margin = flt(self.profit_margin_percent) / 100
        selling_ex_vat = full_cost / (1 - margin)

        self.direct_ingredient_cost = direct_total
        self.total_cost = direct_total
        self.cost_per_portion = direct_per_portion
        self.full_cost_per_portion = full_cost
        self.recommended_price_ex_vat = selling_ex_vat
        self.recommended_price_incl_vat = selling_ex_vat * 1.15
        self.costed_on = now_datetime()
