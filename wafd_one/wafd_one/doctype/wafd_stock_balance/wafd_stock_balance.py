import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WAFDStockBalance(Document):
    def validate(self):
        self.actual_quantity = flt(self.actual_quantity)
        self.reserved_quantity = flt(self.reserved_quantity)
        self.available_quantity = self.actual_quantity - self.reserved_quantity
        self.stock_value = self.actual_quantity * flt(self.average_cost)
        duplicate = frappe.db.get_value(
            "WAFD Stock Balance",
            {"warehouse": self.warehouse, "ingredient": self.ingredient, "name": ["!=", self.name]},
            "name",
        )
        if duplicate:
            frappe.throw("يوجد سجل رصيد لهذا الصنف في المستودع / A stock balance already exists for this ingredient and warehouse")
