from frappe.model.document import Document
from frappe.utils import flt

class WAFDPackagingProfile(Document):
    def validate(self):
        total=0
        for row in self.materials:
            row.line_cost=flt(row.quantity_per_meal)*flt(row.unit_cost)
            total += row.line_cost
        self.total_cost_per_meal=total
