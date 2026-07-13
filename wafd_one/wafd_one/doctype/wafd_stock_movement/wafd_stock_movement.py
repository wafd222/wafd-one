from frappe.model.document import Document
from frappe.utils import flt

class WafdStockMovement(Document):
    def validate(self):
        total = 0
        for row in self.items or []:
            row.amount = flt(row.quantity) * flt(row.unit_cost)
            total += row.amount
        self.total_amount = total
