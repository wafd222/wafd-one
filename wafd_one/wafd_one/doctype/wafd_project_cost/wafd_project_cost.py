import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class WAFDProjectCost(Document):
    def validate(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("Amount must be greater than zero"))
    def on_submit(self):
        project = frappe.get_doc('WAFD Catering Project', self.project)
        project.update_totals()
    def on_cancel(self):
        project = frappe.get_doc('WAFD Catering Project', self.project)
        project.update_totals()
