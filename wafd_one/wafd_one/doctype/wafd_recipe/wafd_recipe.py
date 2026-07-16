import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WafdRecipe(Document):
    def validate(self):
        if flt(self.yield_quantity) <= 0:
            frappe.throw("عدد الحصص يجب أن يكون أكبر من صفر / Yield must be greater than zero")
        total = 0
        for row in self.items or []:
            if row.ingredient:
                ingredient = frappe.db.get_value(
                    "WAFD Ingredient", row.ingredient, ["uom", "standard_cost"], as_dict=True
                )
                if ingredient:
                    row.uom = ingredient.uom
                    row.unit_cost = flt(ingredient.standard_cost)
            row.amount = flt(row.quantity) * flt(row.unit_cost)
            total += row.amount
        self.total_cost = total
        self.cost_per_portion = total / flt(self.yield_quantity)
