import frappe
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


class WAFDDeliveryTrip(Document):
    def validate(self):
        loading = frappe.db.get_value("WAFD Loading Record", self.loading_record, ["project","meal_plan","vehicle","driver","hotel","quantity","status"], as_dict=True)
        if not loading: frappe.throw("سجل التحميل غير موجود / Loading record not found")
        if loading.status not in ("تم التحميل / Loaded", "خرجت / Dispatched"): frappe.throw("يجب إكمال التحميل أولاً / Loading must be completed first")
        self.project, self.meal_plan, self.vehicle, self.driver, self.hotel = loading.project, loading.meal_plan, loading.vehicle, loading.driver, loading.hotel
        self.quantity = cint(loading.quantity)
        if self.status == "في الطريق / In Transit" and not self.actual_departure: self.actual_departure = now_datetime()
        if self.status in ("وصلت / Arrived", "تم التسليم / Delivered") and not self.actual_arrival: self.actual_arrival = now_datetime()
        if self.status == "متأخرة / Delayed" and not self.delay_reason: frappe.throw("سبب التأخير مطلوب / Delay reason is required")

    def on_update(self):
        if self.loading_record and self.status == "في الطريق / In Transit": frappe.db.set_value("WAFD Loading Record", self.loading_record, "status", "خرجت / Dispatched", update_modified=False)
