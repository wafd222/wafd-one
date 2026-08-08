import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class WAFDProcurementPlan(Document):
    def validate(self):
        if self.service_date_from and self.service_date_to and getdate(self.service_date_to) < getdate(self.service_date_from):
            frappe.throw("تاريخ النهاية لا يمكن أن يسبق تاريخ البداية / End date cannot precede start date")
        seen = set()
        required_value = shortage_value = 0.0
        shortages = 0
        for row in self.items or []:
            if row.ingredient in seen:
                frappe.throw(f"المكون مكرر: {row.ingredient} / Duplicate ingredient")
            seen.add(row.ingredient)
            if flt(row.required_quantity) < 0 or flt(row.shortage_quantity) < 0:
                frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
            required_value += flt(row.required_quantity) * flt(row.unit_cost)
            shortage_value += flt(row.shortage_quantity) * flt(row.unit_cost)
            shortages += 1 if flt(row.shortage_quantity) > 0 else 0
        self.total_required_value = required_value
        self.total_shortage_value = shortage_value
        self.shortage_items_count = shortages
