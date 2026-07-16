import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WafdMealPlan(Document):
    def validate(self):
        if flt(self.quantity) <= 0:
            frappe.throw("الكمية يجب أن تكون أكبر من صفر / Quantity must be greater than zero")
        self._load_recipe_cost()
        self.total_value = flt(self.quantity) * flt(self.unit_price)
        self.estimated_cost = flt(self.quantity) * flt(self.estimated_unit_cost)
        self.estimated_profit = flt(self.total_value) - flt(self.estimated_cost)
        self.estimated_margin_percent = (
            flt(self.estimated_profit) / flt(self.total_value) * 100 if self.total_value else 0
        )

    def _load_recipe_cost(self):
        if not self.recipe:
            return
        cost = frappe.db.get_value("WAFD Recipe", self.recipe, "cost_per_portion")
        self.estimated_unit_cost = flt(cost)
