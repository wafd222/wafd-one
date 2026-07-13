from frappe.model.document import Document
from frappe.utils import flt

class WafdPurchaseOrder(Document):
    def validate(self):
        subtotal=0
        for row in self.items or []:
            row.amount=flt(row.quantity)*flt(row.rate)
            subtotal += row.amount
        self.subtotal=subtotal
        self.tax_amount=subtotal*flt(self.tax_rate)/100
        self.grand_total=subtotal+self.tax_amount
