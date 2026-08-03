from frappe.model.document import Document
from frappe.utils import cint, flt
import frappe


class WAFDOperationsSettings(Document):
    def validate(self):
        if cint(self.daily_production_capacity) < 0:
            frappe.throw("الطاقة الإنتاجية اليومية لا يمكن أن تكون سالبة / Daily production capacity cannot be negative")
        if flt(self.capacity_warning_percent) <= 0 or flt(self.capacity_warning_percent) > 100:
            frappe.throw("نسبة تنبيه الطاقة يجب أن تكون أكبر من صفر وحتى 100 / Capacity warning percent must be between 0 and 100")
        if cint(self.default_production_lead_hours) < 0:
            frappe.throw("ساعات التجهيز لا يمكن أن تكون سالبة / Production lead hours cannot be negative")
        if cint(self.shortage_warning_hours) < 0:
            frappe.throw("ساعات تنبيه العجز لا يمكن أن تكون سالبة / Shortage warning hours cannot be negative")
