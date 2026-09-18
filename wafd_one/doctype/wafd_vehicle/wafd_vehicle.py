import frappe
from frappe.model.document import Document
from frappe.utils import cint, getdate, nowdate


class WAFDVehicle(Document):
    def validate(self):
        self.plate_number = (self.plate_number or "").strip()
        if not self.plate_number:
            frappe.throw("رقم اللوحة مطلوب / Plate number is required")
        if cint(self.capacity_meals) < 0:
            frappe.throw("سعة المركبة لا يمكن أن تكون سالبة / Vehicle capacity cannot be negative")
        for fieldname, label in (("registration_expiry", "استمارة المركبة / Registration"), ("insurance_expiry", "التأمين / Insurance")):
            value = self.get(fieldname)
            if value and getdate(value) < getdate(nowdate()) and self.status in ("متاحة / Available", "في مهمة / On Trip"):
                frappe.throw(f"{label} منتهي؛ لا يمكن إبقاء المركبة متاحة أو في مهمة / Expired document")

    def on_trash(self):
        active = frappe.db.exists("WAFD Delivery Trip", {"vehicle": self.name, "status": ["not in", ["تم التسليم / Delivered", "ملغية / Cancelled"]]})
        if active:
            frappe.throw("لا يمكن حذف مركبة مرتبطة برحلة نشطة / Cannot delete a vehicle linked to an active trip")
