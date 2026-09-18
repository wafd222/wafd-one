from frappe.model.document import Document

class WAFDCostingSettings(Document):
    def validate(self):
        for field in ("default_waste_percent", "default_overhead_percent", "default_target_margin_percent", "default_vat_rate", "budget_warning_percent", "budget_exceeded_percent"):
            if (self.get(field) or 0) < 0:
                import frappe
                frappe.throw("لا يمكن أن تكون النسبة سالبة / Percentage cannot be negative")
