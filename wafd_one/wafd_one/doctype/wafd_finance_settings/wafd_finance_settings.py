import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt


class WAFDFinanceSettings(Document):
    def validate(self):
        if flt(self.default_tax_rate) < 0 or flt(self.default_tax_rate) > 100:
            frappe.throw("نسبة الضريبة يجب أن تكون بين 0 و100 / Tax rate must be between 0 and 100")
        if cint(self.default_due_days) < 0 or cint(self.default_due_days) > 3650:
            frappe.throw("أيام الاستحقاق يجب أن تكون بين 0 و3650 / Due days must be between 0 and 3650")
        if flt(self.minimum_auto_invoice_amount) < 0:
            frappe.throw("الحد الأدنى للفاتورة لا يمكن أن يكون سالباً / Minimum invoice amount cannot be negative")
        if cint(self.overdue_alert_days) < 0:
            frappe.throw("أيام تنبيه التأخر لا يمكن أن تكون سالبة / Overdue alert days cannot be negative")
