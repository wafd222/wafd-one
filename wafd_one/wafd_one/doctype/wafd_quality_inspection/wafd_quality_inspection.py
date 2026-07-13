import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class WAFDQualityInspection(Document):
    def validate(self):
        if flt(self.approved_qty) + flt(self.rejected_qty) > flt(self.inspected_qty):
            frappe.throw(_("Approved and rejected quantities cannot exceed inspected quantity"))
        if self.result == 'مرفوض' and not self.corrective_action:
            frappe.throw(_("Corrective Action is required for rejected inspections"))
    def on_submit(self):
        if self.meal_plan:
            frappe.db.set_value('WAFD Meal Plan', self.meal_plan, {'approved_qty': self.approved_qty, 'status': 'جاهز' if self.result in ('مقبول','مقبول بملاحظة') else 'قيد الإنتاج'}, update_modified=False)
