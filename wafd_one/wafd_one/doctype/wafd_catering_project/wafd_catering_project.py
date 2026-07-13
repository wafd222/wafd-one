import frappe
from frappe.model.document import Document
from frappe.utils import flt

class WafdCateringProject(Document):
    def validate(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw("تاريخ النهاية يجب أن يكون بعد تاريخ البداية")
        self.remaining_meals = max((self.total_meals or 0) - (self.delivered_meals or 0), 0)
        self.progress_percent = (flt(self.delivered_meals) / flt(self.total_meals) * 100) if self.total_meals else 0
        self.profit = flt(self.revenue) - flt(self.actual_cost)
