import frappe
from frappe.model.document import Document
from frappe.utils import cint, getdate, nowdate

class WAFDHotCabinet(Document):
    def validate(self):
        if cint(self.capacity) <= 0:
            frappe.throw("سعة السخان يجب أن تكون أكبر من صفر / Cabinet capacity must be greater than zero")
        for fieldname in ("last_cleaned_on", "last_maintenance_on"):
            value = self.get(fieldname)
            if value and getdate(value) > getdate(nowdate()):
                frappe.throw("تواريخ التنظيف والصيانة لا يمكن أن تكون في المستقبل / Dates cannot be in the future")
