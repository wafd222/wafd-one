import frappe
from frappe.model.document import Document
from frappe.utils import flt

class WAFDIngredientPriceObservation(Document):
    def validate(self):
        qty = flt(self.package_quantity)
        if qty <= 0:
            frappe.throw("Package quantity must be greater than zero")
        divisor = qty
        if self.package_uom == "جرام / Gram":
            divisor = qty / 1000
        elif self.package_uom == "مل / ml":
            divisor = qty / 1000
        self.normalized_unit_cost = flt(self.package_price) / divisor
