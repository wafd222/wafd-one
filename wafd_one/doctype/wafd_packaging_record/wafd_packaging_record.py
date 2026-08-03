import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime, nowdate


class WAFDPackagingRecord(Document):
    def validate(self):
        self._sync_batch()
        self._apply_packaging_profile()
        self._validate_quantities()
        self._derive_status()
        self._build_box_manifest()
        self._validate_hot_cabinets()
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
        if cint(self.units_per_box) > 0 and cint(self.packed_quantity) > 0 and not cint(self.box_count):
            self.box_count = (cint(self.packed_quantity) + cint(self.units_per_box) - 1) // cint(self.units_per_box)


    def _apply_packaging_profile(self):
        if not self.packaging_profile:
            return
        values = frappe.db.get_value("WAFD Packaging Profile", self.packaging_profile, ["units_per_box", "total_cost_per_meal", "label_template"], as_dict=True)
        if not values:
            return
        if not self.units_per_box:
            self.units_per_box = cint(values.units_per_box)
        self.packaging_cost_per_meal = flt(values.total_cost_per_meal)
        self.total_packaging_cost = flt(self.packaging_cost_per_meal) * cint(self.packed_quantity or self.planned_quantity)
        if not self.label_text:
            self.label_text = (values.label_template or "").replace("{project}", self.project or "").replace("{batch}", self.production_batch or "").replace("{quantity}", str(cint(self.packed_quantity or self.planned_quantity)))

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
            self.status = "جاهز للتحميل / Ready for Loading" if self.label_verified else "مكتمل / Completed"
            self.start_time = self.start_time or now_datetime()
            self.end_time = self.end_time or now_datetime()
        elif processed > 0:
            self.status = "قيد التغليف / In Progress"
            self.start_time = self.start_time or now_datetime()
            self.end_time = None
        else:
            self.status = "مخطط / Planned"
            self.end_time = None

    def _build_box_manifest(self):
        if not self.tracking_code:
            self.tracking_code = frappe.generate_hash(length=12).upper()
        boxes = cint(self.box_count)
        units = cint(self.units_per_box)
        packed = cint(self.packed_quantity)
        if boxes <= 0 and units > 0 and packed > 0:
            boxes = (packed + units - 1) // units
            self.box_count = boxes
        lines = []
        remaining = packed
        for number in range(1, boxes + 1):
            qty = min(units or remaining, remaining) if remaining > 0 else 0
            code = f"{self.tracking_code}-{number:03d}"
            lines.append(f"{number}/{boxes} | {code} | Qty {qty}")
            remaining = max(remaining - qty, 0)
        self.box_manifest = "\n".join(lines)
        self.ready_for_loading = 1 if self.status == "جاهز للتحميل / Ready for Loading" else 0

    def _validate_hot_cabinets(self):
        """Validate optional hot cabinets without making them a workflow gate."""
        if not cint(self.use_hot_cabinets):
            self.hot_cabinet_count = 0
            self.hot_cabinet_sandwich_total = 0
            return

        rows = self.get("hot_cabinet_allocations") or []
        if not rows:
            frappe.throw("أضف سخاناً واحداً على الأقل أو ألغِ خيار استخدام السخانات / Add at least one cabinet or disable the option")

        seen = set()
        total = 0
        for row in rows:
            if row.hot_cabinet in seen:
                frappe.throw(f"تم تكرار السخان {row.hot_cabinet} / Duplicate hot cabinet")
            seen.add(row.hot_cabinet)
            values = frappe.db.get_value("WAFD Hot Cabinet", row.hot_cabinet, ["capacity", "status"], as_dict=True)
            if not values:
                frappe.throw(f"السخان غير موجود: {row.hot_cabinet}")
            row.capacity = cint(values.capacity)
            qty = cint(row.sandwich_count)
            if qty <= 0:
                frappe.throw("عدد السفندشات داخل كل سخان يجب أن يكون أكبر من صفر")
            if qty > cint(values.capacity):
                frappe.throw(f"عدد السفندشات في {row.hot_cabinet} يتجاوز سعته ({values.capacity})")
            if values.status in ("صيانة / Maintenance", "غير نشط / Inactive"):
                frappe.throw(f"السخان {row.hot_cabinet} غير متاح للاستخدام")
            total += qty

        if total > cint(self.packed_quantity):
            frappe.throw("إجمالي السفندشات داخل السخانات يتجاوز الكمية المغلفة")
        self.hot_cabinet_count = len(rows)
        self.hot_cabinet_sandwich_total = total

    def _validate_gate(self):
        quality = frappe.db.get_value("WAFD Production Batch", self.production_batch, "quality_status")
        if self.status in ("قيد التغليف / In Progress", "مكتمل / Completed", "جاهز للتحميل / Ready for Loading") and quality != "ناجح / Passed":
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
        if self.status in ("مكتمل / Completed", "جاهز للتحميل / Ready for Loading"):
            values["status"] = "جاهز / Ready"
        elif self.status == "قيد التغليف / In Progress":
            values["status"] = "قيد الإنتاج / In Production"
        frappe.db.set_value("WAFD Production Batch", self.production_batch, values, update_modified=False)
