import frappe
from frappe.model.document import Document


class WAFDDeliveryLocation(Document):
    def validate(self):
        self.location_name_ar = (self.location_name_ar or "").strip()
        self.location_name_en = (self.location_name_en or self.location_name_ar).strip()
        if not self.location_name_ar:
            frappe.throw("اسم الموقع مطلوب / Location name is required")

