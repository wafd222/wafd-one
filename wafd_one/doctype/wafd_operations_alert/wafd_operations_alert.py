import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class WAFDOperationsAlert(Document):
    def validate(self):
        if self.status == "مغلق / Closed" and not self.resolution:
            frappe.throw("سجل الإجراء أو الحل قبل إغلاق التنبيه / Enter a resolution before closing the alert")
        if self.status == "مغلق / Closed":
            self.resolved_on = self.resolved_on or now_datetime()
            self.resolved_by = self.resolved_by or frappe.session.user
        else:
            self.resolved_on = None
            self.resolved_by = None
