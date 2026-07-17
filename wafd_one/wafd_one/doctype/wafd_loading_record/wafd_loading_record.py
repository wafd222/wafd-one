import frappe
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


class WAFDLoadingRecord(Document):
    def validate(self):
        packaging = frappe.get_doc("WAFD Packaging Record", self.packaging_record)
        if not packaging:
            frappe.throw("سجل التغليف غير موجود / Packaging record not found")

        # Repair legacy records whose quantities are complete but status is still Planned.
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

        if cint(self.quantity) <= 0:
            frappe.throw("كمية التحميل يجب أن تكون أكبر من صفر / Loaded quantity must be greater than zero")

        previous = frappe.db.sql(
            """select coalesce(sum(quantity),0)
               from `tabWAFD Loading Record`
               where packaging_record=%s and name!=%s
                 and status in ('تم التحميل / Loaded','خرجت / Dispatched')""",
            (self.packaging_record, self.name or ""),
        )[0][0]
        if cint(previous) + cint(self.quantity) > cint(packaging.packed_quantity):
            frappe.throw("إجمالي التحميل يتجاوز الكمية المغلفة / Total loaded quantity exceeds packed quantity")
        if cint(self.box_count) > cint(packaging.box_count) and cint(packaging.box_count):
            frappe.throw("عدد الصناديق يتجاوز الصناديق المغلفة / Box count exceeds packaged boxes")

        # A saved loading record with complete operational data is ready for dispatch.
        if self.status != "خرجت / Dispatched" and self.vehicle and self.driver and cint(self.quantity) > 0:
            self.status = "تم التحميل / Loaded"
        if self.status == "خرجت / Dispatched" and not self.dispatch_time:
            self.dispatch_time = now_datetime()
