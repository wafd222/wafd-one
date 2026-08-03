import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class WAFDComplaint(Document):
    def validate(self):
        if self.delivery_trip:
            trip = frappe.db.get_value("WAFD Delivery Trip", self.delivery_trip, ["project", "hotel"], as_dict=True)
            if not trip:
                frappe.throw("رحلة التوصيل غير موجودة / Delivery trip not found")
            if self.project and self.project != trip.project:
                frappe.throw("المشروع لا يطابق رحلة التوصيل / Project does not match delivery trip")
            if self.hotel and self.hotel != trip.hotel:
                frappe.throw("الفندق لا يطابق رحلة التوصيل / Hotel does not match delivery trip")
            self.project, self.hotel = trip.project, trip.hotel
        if self.complaint_date and get_datetime(self.complaint_date) > now_datetime():
            frappe.throw("تاريخ الشكوى لا يمكن أن يكون في المستقبل / Complaint date cannot be in the future")
        if self.status in ("تم الحل / Resolved", "مغلقة / Closed") and not (self.resolution or "").strip():
            frappe.throw("وصف الحل مطلوب قبل إغلاق الشكوى / Resolution is required before resolving or closing")
        if self.status == "مغلقة / Closed" and not self.assigned_to:
            frappe.throw("يجب تحديد المسؤول قبل إغلاق الشكوى / Assign a responsible user before closing")
