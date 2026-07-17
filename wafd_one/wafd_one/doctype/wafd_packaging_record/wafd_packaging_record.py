import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate


class WafdPackagingRecord(Document):
    def validate(self):
        self._sync_batch()
        self._validate_quantities()
        self._validate_gate()

    def _sync_batch(self):
        values = frappe.db.get_value("WAFD Production Batch", self.production_batch, ["project", "meal_plan", "produced_quantity", "quality_status"], as_dict=True)
        if not values:
            frappe.throw("دفعة الإنتاج غير موجودة / Production batch not found")
        self.project = values.project
        self.meal_plan = values.meal_plan
        self.packaging_date = self.packaging_date or nowdate()
        self.planned_quantity = cint(values.produced_quantity)

    def _validate_quantities(self):
        planned, packed, rejected = cint(self.planned_quantity), cint(self.packed_quantity), cint(self.rejected_quantity)
        if min(planned, packed, rejected) < 0:
            frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
        if packed + rejected > planned:
            frappe.throw("المغلف والمرفوض يتجاوزان الكمية المنتجة / Packed and rejected quantities exceed produced quantity")
        if cint(self.box_count) and cint(self.units_per_box) and packed > cint(self.box_count) * cint(self.units_per_box):
            frappe.throw("الكمية المغلفة تتجاوز سعة الصناديق / Packed quantity exceeds box capacity")
        self.completion_percent = flt(packed) / flt(planned) * 100 if planned else 0
        if self.status == "مكتمل / Completed":
            if packed <= 0:
                frappe.throw("أدخل الكمية المغلفة / Enter packed quantity")
            if not self.label_verified:
                frappe.throw("يجب التحقق من الملصقات / Labels must be verified")
            if not self.end_time:
                frappe.throw("وقت انتهاء التغليف مطلوب / Packaging end time is required")

    def _validate_gate(self):
        quality = frappe.db.get_value("WAFD Production Batch", self.production_batch, "quality_status")
        if self.status in ("قيد التغليف / In Progress", "مكتمل / Completed") and quality != "ناجح / Passed":
            frappe.throw("لا يمكن بدء التغليف قبل نجاح فحص الجودة / Quality inspection must pass before packaging")

    def on_update(self):
        if self.status == "مكتمل / Completed":
            frappe.db.set_value("WAFD Production Batch", self.production_batch, {"packed_quantity": cint(self.packed_quantity), "box_count": cint(self.box_count), "units_per_box": cint(self.units_per_box), "packaging_start_time": self.start_time, "packaging_end_time": self.end_time, "packaging_supervisor": self.supervisor, "status": "جاهز / Ready"}, update_modified=False)
