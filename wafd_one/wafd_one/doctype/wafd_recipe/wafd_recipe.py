from frappe.model.document import Document
from frappe.utils import flt

class WafdRecipe(Document):
    def validate(self):
        total = 0
        for row in self.items or []:
            row.amount = flt(row.quantity) * flt(row.unit_cost)
            total += row.amount
        self.total_cost = total
        self.cost_per_portion = total / flt(self.yield_quantity) if self.yield_quantity else 0
