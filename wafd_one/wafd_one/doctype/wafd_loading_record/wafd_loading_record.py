import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now_datetime


class WAFDLoadingRecord(Document):
    def validate(self):
        packaging = frappe.get_doc("WAFD Packaging Record", self.packaging_record)
        original_status = packaging.status
        packaging._validate_quantities()
        packaging._derive_status()
        if packaging.status != original_status:
            packaging.save(ignore_permissions=True)
        if packaging.status != "مكتمل / Completed":
            frappe.throw("يجب إكمال التغليف قبل التحميل / Packaging must be completed before loading")

        self.project = packaging.project
        self.meal_plan = packaging.meal_plan
        self.production_batch = packaging.production_batch
        meal_hotel = frappe.db.get_value("WAFD Meal Plan", self.meal_plan, "hotel")
        if meal_hotel and self.hotel != meal_hotel:
            frappe.throw("الفندق لا يطابق خطة الوجبة / Hotel does not match the meal plan")

        quantity = cint(self.quantity)
        if quantity <= 0:
            frappe.throw("كمية التحميل يجب أن تكون أكبر من صفر / Loaded quantity must be greater than zero")
        if cint(self.box_count) < 0:
            frappe.throw("عدد الصناديق لا يمكن أن يكون سالباً / Box count cannot be negative")
        if self.loading_date and get_datetime(self.loading_date) > now_datetime():
            frappe.throw("وقت التحميل لا يمكن أن يكون في المستقبل / Loading time cannot be in the future")

        previous = frappe.db.sql("""select coalesce(sum(quantity),0) from `tabWAFD Loading Record`
            where packaging_record=%s and name!=%s and status in ('تم التحميل / Loaded','خرجت / Dispatched')""",
            (self.packaging_record, self.name or ""))[0][0]
        if cint(previous) + quantity > cint(packaging.packed_quantity):
            frappe.throw("إجمالي التحميل يتجاوز الكمية المغلفة / Total loaded quantity exceeds packed quantity")
        previous_boxes = frappe.db.sql("""select coalesce(sum(box_count),0) from `tabWAFD Loading Record`
            where packaging_record=%s and name!=%s and status in ('تم التحميل / Loaded','خرجت / Dispatched')""",
            (self.packaging_record, self.name or ""))[0][0]
        if cint(packaging.box_count) and cint(previous_boxes) + cint(self.box_count) > cint(packaging.box_count):
            frappe.throw("إجمالي الصناديق المحملة يتجاوز الصناديق المغلفة / Total loaded boxes exceed packaged boxes")

        if self.vehicle:
            vehicle = frappe.db.get_value("WAFD Vehicle", self.vehicle, ["status", "capacity_meals", "registration_expiry", "insurance_expiry"], as_dict=True)
            if not vehicle:
                frappe.throw("المركبة غير موجودة / Vehicle not found")
            if vehicle.status in ("صيانة / Maintenance", "غير نشطة / Inactive"):
                frappe.throw("المركبة غير متاحة للتحميل / Vehicle is not available")
            self.vehicle_capacity = cint(vehicle.capacity_meals)
            self.capacity_utilization_percent = (flt(quantity) / flt(vehicle.capacity_meals) * 100) if cint(vehicle.capacity_meals) else 0
            if cint(vehicle.capacity_meals) and quantity > cint(vehicle.capacity_meals):
                frappe.throw("كمية التحميل تتجاوز سعة المركبة / Loaded quantity exceeds vehicle capacity")
        if not self.vehicle:
            self.vehicle_capacity = 0
            self.capacity_utilization_percent = 0
        if self.driver:
            driver_status = frappe.db.get_value("WAFD Driver", self.driver, "status")
            if driver_status in ("إجازة / Leave", "غير نشط / Inactive"):
                frappe.throw("السائق غير متاح / Driver is not available")

        if self.status == "خرجت / Dispatched":
            if not self.vehicle or not self.driver:
                frappe.throw("المركبة والسائق مطلوبان قبل الخروج / Vehicle and driver are required before dispatch")
            self.dispatch_time = self.dispatch_time or now_datetime()
            if not self.loading_photo:
                frappe.throw("صورة التحميل مطلوبة قبل الخروج / Loading photo is required before dispatch")
        elif self.vehicle and self.driver:
            self.status = "تم التحميل / Loaded"

    def on_trash(self):
        if frappe.db.exists("WAFD Delivery Trip", {"loading_record": self.name, "status": ["!=", "ملغية / Cancelled"]}):
            frappe.throw("لا يمكن حذف سجل تحميل مرتبط برحلة غير ملغاة / Cannot delete loading linked to a non-cancelled trip")
