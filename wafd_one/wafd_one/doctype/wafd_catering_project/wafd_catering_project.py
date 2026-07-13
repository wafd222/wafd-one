import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class WAFDCateringProject(Document):
    def validate(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw(_("End Date cannot be before Start Date"))
        self.number_of_hotels = len(self.hotels or [])
        self.expected_profit = flt(self.contract_value) - flt(self.estimated_cost)
        self.actual_profit = flt(self.contract_value) - flt(self.actual_cost)
        self.remaining_meals = max(flt(self.total_meals) - flt(self.completed_meals), 0)
        self.progress_percent = (flt(self.completed_meals) / flt(self.total_meals) * 100) if flt(self.total_meals) else 0

    def on_update(self):
        self.update_totals()

    def update_totals(self):
        total = frappe.db.sql("""select coalesce(sum(planned_qty),0) from `tabWAFD Meal Plan` where project=%s and status!='ملغي'""", self.name)[0][0]
        delivered = frappe.db.sql("""select coalesce(sum(delivered_qty),0) from `tabWAFD Delivery Proof` where project=%s and docstatus=1""", self.name)[0][0]
        cost = frappe.db.sql("""select coalesce(sum(amount),0) from `tabWAFD Project Cost` where project=%s and docstatus=1""", self.name)[0][0]
        values={
            'total_meals': total, 'completed_meals': delivered,
            'remaining_meals': max(flt(total)-flt(delivered),0),
            'progress_percent': (flt(delivered)/flt(total)*100) if flt(total) else 0,
            'actual_cost': cost, 'actual_profit': flt(self.contract_value)-flt(cost),
            'number_of_hotels': len(self.hotels or [])
        }
        frappe.db.set_value(self.doctype,self.name,values,update_modified=False)
