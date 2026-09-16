from frappe.model.document import Document
from frappe.utils import cint
import frappe


class WAFDKitchen(Document):
    def validate(self):
        if cint(self.daily_capacity) < 0:
            frappe.throw("الطاقة الإنتاجية اليومية لا يمكن أن تكون سالبة / Daily capacity cannot be negative")
        if cint(self.production_lines) < 0:
            frappe.throw("عدد خطوط الإنتاج لا يمكن أن يكون سالبًا / Production lines cannot be negative")
