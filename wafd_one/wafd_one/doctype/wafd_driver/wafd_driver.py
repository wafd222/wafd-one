import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class WAFDDriver(Document):
    def validate(self):
        self.driver_name = (self.driver_name or "").strip()
        self.mobile = (self.mobile or "").strip()
        if not self.driver_name or not self.mobile:
            frappe.throw("اسم السائق ورقم الجوال مطلوبان / Driver name and mobile are required")
        self._validate_system_user_link()
        if self.license_expiry and getdate(self.license_expiry) < getdate(nowdate()) and self.status in ("متاح / Available", "في مهمة / On Trip"):
            frappe.throw("رخصة السائق منتهية؛ لا يمكن إبقاؤه متاحاً أو في مهمة / Driver license has expired")


    def _validate_system_user_link(self):
        if not self.system_user:
            return
        user = frappe.db.get_value("User", self.system_user, ["enabled", "user_type"], as_dict=True)
        if not user or not user.enabled or user.user_type != "System User":
            frappe.throw("يجب ربط السائق بمستخدم نظام نشط / Driver must be linked to an active System User")
        duplicate = frappe.db.exists(
            "WAFD Driver",
            {"system_user": self.system_user, "name": ["!=", self.name or ""]},
        )
        if duplicate:
            frappe.throw("هذا المستخدم مرتبط بسائق آخر / This system user is already linked to another driver")
        if "WAFD Driver" not in frappe.get_roles(self.system_user):
            frappe.throw("يجب منح المستخدم دور WAFD Driver أولاً / Assign the WAFD Driver role to this user first")

    def on_trash(self):
        active = frappe.db.exists("WAFD Delivery Trip", {"driver": self.name, "status": ["not in", ["تم التسليم / Delivered", "ملغية / Cancelled"]]})
        if active:
            frappe.throw("لا يمكن حذف سائق مرتبط برحلة نشطة / Cannot delete a driver linked to an active trip")
