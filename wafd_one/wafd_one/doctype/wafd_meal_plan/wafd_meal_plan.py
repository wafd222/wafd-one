import frappe
from frappe.model.document import Document
from frappe.utils import flt

class WafdMealPlan(Document):
    def validate(self):
        if flt(self.quantity) <= 0:
            frappe.throw("الكمية يجب أن تكون أكبر من صفر")
        self.total_value = flt(self.quantity) * flt(self.unit_price)
        self.estimated_cost = flt(self.quantity) * flt(self.estimated_unit_cost)
