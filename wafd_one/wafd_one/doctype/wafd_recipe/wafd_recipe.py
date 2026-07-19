import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

class WAFDRecipe(Document):
    def validate(self):
        direct_total = 0.0
        for row in self.items or []:
            if row.ingredient:
                ingredient = frappe.db.get_value("WAFD Ingredient", row.ingredient, ["uom", "standard_cost"], as_dict=True)
                if ingredient:
                    row.uom = ingredient.uom
                    row.unit_cost = flt(ingredient.standard_cost)
            row.amount = flt(row.quantity) * flt(row.unit_cost)
            direct_total += flt(row.amount)
        yield_qty = flt(self.yield_quantity) or 1
        direct_per_portion = direct_total / yield_qty
        waste_cost = direct_per_portion * flt(self.waste_percent) / 100
        subtotal = direct_per_portion + waste_cost + flt(self.packaging_cost_per_portion) + flt(self.labor_cost_per_portion) + flt(self.utilities_cost_per_portion) + flt(self.delivery_cost_per_portion)
        overhead = subtotal * flt(self.overhead_percent) / 100
        full_cost = subtotal + overhead
        margin = flt(self.profit_margin_percent) / 100
        selling_ex_vat = full_cost / (1 - margin) if margin < 1 else 0
        self.direct_ingredient_cost = direct_total
        self.total_cost = direct_total
        self.cost_per_portion = direct_per_portion
        self.full_cost_per_portion = full_cost
        self.recommended_price_ex_vat = selling_ex_vat
        self.recommended_price_incl_vat = selling_ex_vat * 1.15
        self.costed_on = now_datetime()
