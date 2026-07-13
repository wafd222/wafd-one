import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class WAFDDeliveryProof(Document):
    def validate(self):
        loaded, trip_status = frappe.db.get_value('WAFD Delivery Trip', self.delivery_trip, ['loaded_qty','status']) or (0,None)
        if flt(self.delivered_qty) <= 0:
            frappe.throw(_("Delivered quantity must be greater than zero"))
        if flt(self.delivered_qty) > flt(loaded):
            frappe.throw(_("Delivered quantity cannot exceed loaded quantity"))
    def on_submit(self):
        trip = frappe.get_doc('WAFD Delivery Trip', self.delivery_trip)
        frappe.db.set_value('WAFD Delivery Trip', trip.name, {'status':'تم التسليم','arrival_time':self.delivery_time}, update_modified=False)
        frappe.db.set_value('WAFD Meal Plan', trip.meal_plan, {'delivered_qty':self.delivered_qty,'status':'تم التسليم'}, update_modified=False)
        frappe.db.set_value('WAFD Vehicle', trip.vehicle, 'status', 'متاحة', update_modified=False)
        frappe.db.set_value('WAFD Driver', trip.driver, 'status', 'متاح', update_modified=False)
        project = frappe.get_doc('WAFD Catering Project', trip.project)
        project.update_totals()
    def on_cancel(self):
        trip = frappe.get_doc('WAFD Delivery Trip', self.delivery_trip)
        frappe.db.set_value('WAFD Delivery Trip', trip.name, 'status', 'وصلت', update_modified=False)
        frappe.db.set_value('WAFD Meal Plan', trip.meal_plan, 'status', 'محمل', update_modified=False)
