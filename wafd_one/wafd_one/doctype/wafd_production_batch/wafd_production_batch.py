import frappe
from frappe.model.document import Document
from frappe.utils import cint

class WafdProductionBatch(Document):
    def validate(self):
        if cint(self.produced_quantity) + cint(self.rejected_quantity) > cint(self.planned_quantity):
            frappe.throw("مجموع المنتج والمرفوض لا يمكن أن يتجاوز الكمية المخططة")
