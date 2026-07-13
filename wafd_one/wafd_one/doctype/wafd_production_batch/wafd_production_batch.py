import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class WAFDProductionBatch(Document):
    def validate(self):
        if flt(self.produced_qty) <= 0:
            frappe.throw(_("Produced quantity must be greater than zero"))
        if flt(self.waste_qty) > flt(self.produced_qty):
            frappe.throw(_("Waste quantity cannot exceed produced quantity"))
    def on_update(self):
        if self.meal_plan:
            total = frappe.db.sql("select coalesce(sum(produced_qty),0) from `tabWAFD Production Batch` where meal_plan=%s and status!='ملغي'", self.meal_plan)[0][0]
            frappe.db.set_value('WAFD Meal Plan', self.meal_plan, {'produced_qty': total, 'status': 'قيد الإنتاج' if self.status!='مكتمل' else 'جاهز'}, update_modified=False)
