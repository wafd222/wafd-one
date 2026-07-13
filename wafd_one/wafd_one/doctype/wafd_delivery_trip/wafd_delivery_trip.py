import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class WAFDDeliveryTrip(Document):
    def validate(self):
        if flt(self.loaded_qty) <= 0:
            frappe.throw(_("Loaded quantity must be greater than zero"))
        capacity = frappe.db.get_value('WAFD Vehicle', self.vehicle, 'capacity') or 0
        if capacity and flt(self.loaded_qty) > flt(capacity):
            frappe.throw(_("Loaded quantity exceeds vehicle capacity"))
        if self.scheduled_departure and self.required_arrival and self.required_arrival < self.scheduled_departure:
            frappe.throw(_("Required arrival cannot be before scheduled departure"))
