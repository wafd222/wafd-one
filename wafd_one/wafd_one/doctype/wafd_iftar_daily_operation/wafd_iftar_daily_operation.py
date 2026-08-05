from __future__ import annotations
import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime

class WAFDIftarDailyOperation(Document):
    def validate(self):
        if not self.project or not self.operation_date:
            return
        duplicate = frappe.db.exists("WAFD Iftar Daily Operation", {"project": self.project, "operation_date": self.operation_date, "name": ["!=", self.name]})
        if duplicate:
            frappe.throw("يوجد سجل تشغيل لهذا المشروع في نفس التاريخ / A daily operation already exists for this project and date")
        project = frappe.get_doc("WAFD Iftar Project", self.project)
        if self.operation_date < project.start_date or self.operation_date > project.end_date:
            frappe.throw("تاريخ التشغيل خارج مدة المشروع / Operation date is outside the project period")
        self.planned_meals = cint(project.daily_meals)
        values=[cint(self.produced_meals),cint(self.packaged_meals),cint(self.loaded_meals),cint(self.delivered_meals),cint(self.received_meals)]
        if any(v < 0 for v in values + [cint(self.surplus_meals),cint(self.waste_meals),cint(self.preservation_society_quantity)]):
            frappe.throw("لا يمكن إدخال كميات سالبة / Negative quantities are not allowed")
        if self.packaged_meals > self.produced_meals: frappe.throw("التغليف لا يتجاوز الإنتاج / Packaged cannot exceed produced")
        if self.loaded_meals > self.packaged_meals: frappe.throw("التحميل لا يتجاوز التغليف / Loaded cannot exceed packaged")
        if self.delivered_meals > self.loaded_meals: frappe.throw("التسليم لا يتجاوز التحميل / Delivered cannot exceed loaded")
        if self.received_meals > self.delivered_meals: frappe.throw("الاستلام لا يتجاوز التسليم / Received cannot exceed delivered")
        if cint(self.surplus_meals)+cint(self.waste_meals)+cint(self.preservation_society_quantity) > cint(self.produced_meals):
            frappe.throw("الفائض والتالف وحفظ النعمة لا تتجاوز الإنتاج / Closing quantities cannot exceed production")
        self.completion_percent = min(100, flt(self.received_meals) / flt(self.planned_meals) * 100) if self.planned_meals else 0
        if self.received_meals >= self.planned_meals and self.planned_meals:
            self.status = "مستلم / Received"
            if not self.receipt_time: self.receipt_time = now_datetime()
        elif self.delivered_meals: self.status = "في التوزيع / Distributing"
        elif self.loaded_meals: self.status = "جاهز للتحميل / Ready to Load"
        elif self.produced_meals: self.status = "قيد الإنتاج / In Production"
