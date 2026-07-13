import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class WAFDMealPlan(Document):
    def validate(self):
        if self.planned_qty is not None and self.planned_qty <= 0:
            frappe.throw(_("Planned quantity must be greater than zero"))
        if self.project and self.service_date:
            start_date, end_date = frappe.db.get_value("WAFD Catering Project", self.project, ["start_date", "end_date"]) or (None, None)
            if start_date and end_date and not (getdate(start_date) <= getdate(self.service_date) <= getdate(end_date)):
                frappe.throw(_("Service Date must be within the project dates"))
        if self.project and self.hotel:
            mission = frappe.db.get_value("WAFD Catering Project", self.project, "mission")
            hotel_mission = frappe.db.get_value("WAFD Hotel", self.hotel, "mission")
            if mission and hotel_mission and mission != hotel_mission:
                frappe.throw(_("The selected hotel belongs to another mission"))
