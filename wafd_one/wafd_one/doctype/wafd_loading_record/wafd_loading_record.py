import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class WAFDLoadingRecord(Document):
    def validate(self):
        approved = frappe.db.get_value('WAFD Quality Inspection', self.quality_inspection, 'approved_qty') or 0
        if flt(self.loaded_qty) > flt(approved):
            frappe.throw(_("Loaded quantity cannot exceed approved quantity"))
        if frappe.db.get_value('WAFD Vehicle', self.vehicle, 'status') == 'صيانة':
            frappe.throw(_("The selected vehicle is under maintenance"))
    def on_submit(self):
        frappe.db.set_value('WAFD Meal Plan', self.meal_plan, {'loaded_qty': self.loaded_qty, 'status': 'محمل'}, update_modified=False)
        frappe.db.set_value('WAFD Vehicle', self.vehicle, 'status', 'في مهمة', update_modified=False)
        frappe.db.set_value('WAFD Driver', self.driver, 'status', 'في مهمة', update_modified=False)
    def on_cancel(self):
        frappe.db.set_value('WAFD Vehicle', self.vehicle, 'status', 'متاحة', update_modified=False)
        frappe.db.set_value('WAFD Driver', self.driver, 'status', 'متاح', update_modified=False)
