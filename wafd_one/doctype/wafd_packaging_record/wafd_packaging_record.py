import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime, nowdate


class WAFDPackagingRecord(Document):
    def validate(self):
        self._sync_batch()
        self._validate_quantities()
        self._derive_status()
        self._validate_gate()

    def _sync_batch(self):
        values = frappe.db.get_value(
            "WAFD Production Batch",
            self.production_batch,
            ["project", "meal_plan", "planned_quantity", "produced_quantity", "quality_status", "batch_date"],
            as_dict=True,
        )
        if not values:
            frappe.throw("دفعة الإنتاج غير موجودة / Production batch not found")

        self.project = values.project
        self.meal_plan = values.meal_plan
        self.packaging_date = self.packaging_date or values.batch_date or nowdate()
        quantity = cint(values.produced_quantity) or cint(values.planned_quantity)
        if quantity <= 0:
            frappe.throw("الكمية المنتجة أو المخططة مطلوبة / Produced or planned quantity is required")

        self.planned_quantity = quantity
        if not self.packed_quantity:
            self.packed_quantity = quantity
        if not self.supervisor:
            self.supervisor = frappe.session.user

    def _validate_quantities(self):
        planned = cint(self.planned_quantity)
        packed = cint(self.packed_quantity)
        rejected = cint(self.rejected_quantity)

        if min(planned, packed, rejected) < 0:
            frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
        if packed + rejected > planned:
            frappe.throw("المغلف والمرفوض يتجاوزان الكمية المنتجة / Packed and rejected quantities exceed produced quantity")
        if cint(self.box_count) and cint(self.units_per_box) and packed > cint(self.box_count) * cint(self.units_per_box):
            frappe.throw("الكمية المغلفة تتجاوز سعة الصناديق / Packed quantity exceeds box capacity")

        self.completion_percent = flt(packed + rejected) / flt(planned) * 100 if planned else 0

    def _derive_status(self):
        """Keep the workflow status consistent with the recorded quantities.

        Existing records created before v4.4 may have 100% completion while still
        marked Planned. This method repairs them automatically on the next save or
        when loading is created.
        """
        if self.status == "موقوف / Stopped":
            return

        planned = cint(self.planned_quantity)
        processed = cint(self.packed_quantity) + cint(self.rejected_quantity)

        if planned > 0 and processed == planned:
            self.status = "مكتمل / Completed"
            self.start_time = self.start_time or now_datetime()
            self.end_time = self.end_time or now_datetime()
        elif processed > 0:
            self.status = "قيد التغليف / In Progress"
            self.start_time = self.start_time or now_datetime()
            self.end_time = None
        else:
            self.status = "مخطط / Planned"
            self.end_time = None

    def _validate_gate(self):
        quality = frappe.db.get_value("WAFD Production Batch", self.production_batch, "quality_status")
        if self.status in ("قيد التغليف / In Progress", "مكتمل / Completed") and quality != "ناجح / Passed":
            frappe.throw("لا يمكن بدء التغليف قبل نجاح فحص الجودة / Quality inspection must pass before packaging")

    def on_update(self):
        values = {
            "packed_quantity": cint(self.packed_quantity),
            "box_count": cint(self.box_count),
            "units_per_box": cint(self.units_per_box),
            "packaging_start_time": self.start_time,
            "packaging_end_time": self.end_time,
            "packaging_supervisor": self.supervisor,
        }
        if self.status == "مكتمل / Completed":
            values["status"] = "جاهز / Ready"
        elif self.status == "قيد التغليف / In Progress":
            values["status"] = "قيد الإنتاج / In Production"
        frappe.db.set_value("WAFD Production Batch", self.production_batch, values, update_modified=False)
