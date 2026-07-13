from frappe.model.document import Document
from frappe.utils import flt

class WafdInvoice(Document):
    def validate(self):
        self.tax_amount=flt(self.subtotal)*flt(self.tax_rate)/100
        self.grand_total=flt(self.subtotal)+flt(self.tax_amount)
        self.balance=max(flt(self.grand_total)-flt(self.paid_amount),0)
