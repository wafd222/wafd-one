import frappe
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


class WafdLoadingRecord(Document):
    def validate(self):
        pack = frappe.db.get_value("WAFD Packaging Record", self.packaging_record, ["project","meal_plan","production_batch","packed_quantity","box_count","status"], as_dict=True)
        if not pack: frappe.throw("سجل التغليف غير موجود / Packaging record not found")
        if pack.status != "مكتمل / Completed": frappe.throw("يجب إكمال التغليف قبل التحميل / Packaging must be completed before loading")
        self.project, self.meal_plan, self.production_batch = pack.project, pack.meal_plan, pack.production_batch
        if cint(self.quantity) <= 0: frappe.throw("كمية التحميل يجب أن تكون أكبر من صفر / Loaded quantity must be greater than zero")
        previous = frappe.db.sql("select coalesce(sum(quantity),0) from `tabWAFD Loading Record` where packaging_record=%s and name!=%s and status in ('تم التحميل / Loaded','خرجت / Dispatched')", (self.packaging_record, self.name or ''))[0][0]
        if cint(previous) + cint(self.quantity) > cint(pack.packed_quantity): frappe.throw("إجمالي التحميل يتجاوز الكمية المغلفة / Total loaded quantity exceeds packed quantity")
        if cint(self.box_count) > cint(pack.box_count) and cint(pack.box_count): frappe.throw("عدد الصناديق يتجاوز الصناديق المغلفة / Box count exceeds packaged boxes")
        if self.status == "خرجت / Dispatched" and not self.dispatch_time: self.dispatch_time = now_datetime()
