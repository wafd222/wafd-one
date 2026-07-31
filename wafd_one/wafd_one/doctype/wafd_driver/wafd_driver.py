import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class WAFDDriver(Document):
    def validate(self):
        self.driver_name = (self.driver_name or "").strip()
        self.mobile = (self.mobile or "").strip()
        if not self.driver_name or not self.mobile:
            frappe.throw("اسم السائق ورقم الجوال مطلوبان / Driver name and mobile are required")
        if self.license_expiry and getdate(self.license_expiry) < getdate(nowdate()) and self.status in ("متاح / Available", "في مهمة / On Trip"):
            frappe.throw("رخصة السائق منتهية؛ لا يمكن إبقاؤه متاحاً أو في مهمة / Driver license has expired")

    def on_trash(self):
        active = frappe.db.exists("WAFD Delivery Trip", {"driver": self.name, "status": ["not in", ["تم التسليم / Delivered", "ملغية / Cancelled"]]})
        if active:
            frappe.throw("لا يمكن حذف سائق مرتبط برحلة نشطة / Cannot delete a driver linked to an active trip")
