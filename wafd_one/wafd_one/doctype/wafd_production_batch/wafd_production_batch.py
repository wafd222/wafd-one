import uuid
import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, flt, get_datetime, now_datetime


class WAFDProductionBatch(Document):
    def validate(self):
        self._ensure_traceability_code()
        self._sync_from_meal_plan()
        self._validate_quantities()
        self._validate_schedule()
        self._calculate_material_requirements()
        self._validate_workflow()

    def _validate_quantities(self):
        produced = cint(self.produced_quantity)
        rejected = cint(self.rejected_quantity)
        planned = cint(self.planned_quantity)
        packed = cint(self.packed_quantity)
        if planned <= 0:
            frappe.throw("الكمية المخططة يجب أن تكون أكبر من صفر / Planned quantity must be greater than zero")
        if min(produced, rejected, packed) < 0:
            frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
        if produced + rejected > planned:
            frappe.throw("مجموع المنتج والمرفوض لا يمكن أن يتجاوز الكمية المخططة / Produced and rejected quantities exceed plan")
        if packed > produced:
            frappe.throw("الكمية المغلفة لا يمكن أن تتجاوز الكمية المنتجة / Packed quantity cannot exceed produced quantity")
        if cint(self.box_count) and cint(self.units_per_box) and packed > cint(self.box_count) * cint(self.units_per_box):
            frappe.throw("الكمية المغلفة تتجاوز سعة الصناديق / Packed quantity exceeds box capacity")
        self.actual_yield_percent = (flt(produced) / flt(planned) * 100) if planned else 0
        self.completion_percent = (flt(packed) / flt(planned) * 100) if planned else 0

    def _sync_from_meal_plan(self):
        if not self.meal_plan:
            return
        values = frappe.db.get_value(
            "WAFD Meal Plan", self.meal_plan,
            ["project", "recipe", "quantity", "service_date", "status"], as_dict=True,
        )
        if not values:
            frappe.throw("خطة الوجبة غير موجودة / Meal plan was not found")
        if values.status == "ملغي / Cancelled":
            frappe.throw("لا يمكن إنشاء إنتاج لخطة ملغاة / Cannot produce a cancelled meal plan")
        if self.project and self.project != values.project:
            frappe.throw("المشروع لا يطابق خطة الوجبة / Project does not match the meal plan")
        self.project = values.project
        self.recipe = values.recipe
        self.batch_date = self.batch_date or values.service_date
        if not self.planned_quantity:
            self.planned_quantity = cint(values.quantity)

    def _validate_schedule(self):
        if self.meal_plan:
            plan = frappe.db.get_value("WAFD Meal Plan", self.meal_plan, ["service_date", "service_time"], as_dict=True)
            if plan and plan.service_date:
                deadline = get_datetime(f"{plan.service_date} {plan.service_time or '23:59:59'}")
                self.service_deadline = deadline
                current = now_datetime()
                if self.status not in ("جاهز / Ready", "مكتمل / Completed", "موقوف / Stopped"):
                    if current > deadline:
                        self.schedule_status = "متأخر / Delayed"
                    elif current > add_to_date(deadline, hours=-4):
                        self.schedule_status = "معرض للتأخير / At Risk"
                    else:
                        self.schedule_status = "في الوقت / On Time"
                else:
                    self.schedule_status = "في الوقت / On Time"

        timeline = [
            ("start_time", self.start_time),
            ("cooking_start_time", self.cooking_start_time),
            ("packaging_start_time", self.packaging_start_time),
            ("packaging_end_time", self.packaging_end_time),
            ("end_time", self.end_time),
        ]
        previous_name = None
        previous_value = None
        for fieldname, value in timeline:
            if not value:
                continue
            current_value = get_datetime(value)
            if previous_value and current_value < previous_value:
                frappe.throw(f"ترتيب أوقات الإنتاج غير صحيح بين {previous_name} و {fieldname} / Production timeline is out of order")
            previous_name, previous_value = fieldname, current_value
        if self.end_time and self.service_deadline and get_datetime(self.end_time) > get_datetime(self.service_deadline):
            frappe.throw("وقت انتهاء الإنتاج بعد موعد الخدمة / Production end time is after service deadline")

    def _source_rows(self):
        rows = [row for row in (self.source_warehouses or []) if row.warehouse]
        if not rows and self.source_warehouse:
            self.append("source_warehouses", {"warehouse": self.source_warehouse, "priority": 1, "is_default": 1})
            rows = list(self.source_warehouses)
        seen = set()
        for index, row in enumerate(rows, start=1):
            if row.warehouse in seen:
                frappe.throw(f"مصدر صرف مكرر: {row.warehouse} / Duplicate source warehouse")
            seen.add(row.warehouse)
            row.priority = cint(row.priority) or index
        rows.sort(key=lambda x: (0 if cint(x.is_default) else 1, cint(x.priority), x.idx))
        if rows:
            self.source_warehouse = rows[0].warehouse
        return rows

    def _calculate_material_requirements(self):
        previous_movements = {(row.ingredient, row.warehouse): row.stock_movement for row in (self.material_allocations or []) if row.stock_movement}
        self.set("material_requirements", [])
        self.set("material_allocations", [])
        self.total_material_cost = 0
        self.materials_status = "لم تحسب / Not Calculated"
        if not self.recipe or not self.planned_quantity:
            return
        sources = self._source_rows()
        _, requirements = _recipe_requirements(self)
        has_shortage = False
        for req in requirements:
            remaining = flt(req["quantity"])
            available_total = 0
            for source in sources:
                balance = frappe.db.get_value("WAFD Stock Balance", {"warehouse": source.warehouse, "ingredient": req["ingredient"]}, ["available_quantity", "average_cost"], as_dict=True) or {}
                available = max(flt(balance.get("available_quantity")), 0)
                available_total += available
                allocated = min(remaining, available)
                if allocated > 0:
                    unit_cost = flt(balance.get("average_cost")) or flt(req["unit_cost"])
                    self.append("material_allocations", {
                        "ingredient": req["ingredient"], "warehouse": source.warehouse,
                        "allocated_quantity": allocated, "uom": req["uom"],
                        "available_before": available, "unit_cost": unit_cost,
                        "amount": allocated * unit_cost,
                        "stock_movement": previous_movements.get((req["ingredient"], source.warehouse))
                            or (self.material_issue if source.warehouse == self.source_warehouse else None),
                    })
                    remaining -= allocated
                if remaining <= 0:
                    break
            shortage = max(remaining, 0)
            has_shortage = has_shortage or shortage > 0
            amount = flt(req["quantity"]) * flt(req["unit_cost"])
            self.total_material_cost += amount
            self.append("material_requirements", {
                "ingredient": req["ingredient"], "required_quantity": req["quantity"], "uom": req["uom"],
                "available_quantity": available_total, "shortage_quantity": shortage,
                "unit_cost": req["unit_cost"], "amount": amount,
                "availability_status": "ناقص / Shortage" if shortage else "متوفر / Available",
            })
        movements = {row.stock_movement for row in self.material_allocations if row.stock_movement}
        posted = movements and all(frappe.db.get_value("WAFD Stock Movement", name, "status") == "مرحلة / Posted" for name in movements)
        if posted and not has_shortage:
            self.materials_status = "مصروفة / Issued"
        elif not sources:
            self.materials_status = "لم تحسب / Not Calculated"
        else:
            self.materials_status = "عجز / Shortage" if has_shortage else "متوفرة / Available"

    def _validate_workflow(self):
        active = ("تحضير / Preparing", "طبخ / Cooking", "تغليف / Packaging", "جاهز / Ready", "مكتمل / Completed")
        if self.status in active:
            movements = {row.stock_movement for row in (self.material_allocations or []) if row.stock_movement}
            if not movements:
                frappe.throw("يجب إنشاء حركات صرف المواد قبل بدء الإنتاج / Material issues must be created before production")
            unposted = [name for name in movements if frappe.db.get_value("WAFD Stock Movement", name, "status") != "مرحلة / Posted"]
            if unposted:
                frappe.throw("يجب ترحيل جميع حركات الصرف أولاً: " + ", ".join(unposted) + " / Post all material issues first")
        if self.status in ("جاهز / Ready", "مكتمل / Completed") and self.quality_status != "ناجح / Passed":
            frappe.throw("لا يمكن اعتماد الدفعة كجاهزة قبل نجاح فحص الجودة / A passed quality inspection is required")
        if self.status in ("جاهز / Ready", "مكتمل / Completed") and self.food_safety_release_status != "مفرج / Released":
            frappe.throw("لا يمكن اعتماد الدفعة كجاهزة قبل الإفراج الغذائي / Food safety release is required")
        if self.status == "مكتمل / Completed" and cint(self.produced_quantity) <= 0:
            frappe.throw("أدخل الكمية المنتجة قبل إكمال الدفعة / Enter produced quantity before completing the batch")

    def _ensure_traceability_code(self):
        if not self.traceability_code:
            self.traceability_code = "WAFD-TRC-" + uuid.uuid4().hex[:12].upper()

    def before_save(self):
        if self.is_new():
            return
        previous = self.get_doc_before_save()
        if previous and previous.food_safety_release_status == "مفرج / Released":
            protected = ("project", "meal_plan", "recipe", "source_warehouse", "planned_quantity", "produced_quantity", "rejected_quantity", "batch_date")
            changed = [field for field in protected if self.get(field) != previous.get(field)]
            if changed:
                frappe.throw("لا يمكن تعديل بيانات الدفعة الأساسية بعد الإفراج الغذائي / Released batch core data cannot be modified")

    def on_update(self):
        self._update_meal_plan_status()

    def _update_meal_plan_status(self):
        if not self.meal_plan:
            return
        mapped = {
            "مخطط / Planned": "معتمد / Approved",
            "تحضير / Preparing": "قيد الإنتاج / In Production",
            "طبخ / Cooking": "قيد الإنتاج / In Production",
            "تغليف / Packaging": "قيد الإنتاج / In Production",
            "جاهز / Ready": "جاهز / Ready",
            "مكتمل / Completed": "جاهز / Ready",
        }
        status = mapped.get(self.status)
        if status:
            frappe.db.set_value("WAFD Meal Plan", self.meal_plan, "status", status, update_modified=False)


def _recipe_requirements(batch):
    if not batch.recipe:
        frappe.throw("حدد الوصفة أولاً / Select a recipe first")
    recipe = frappe.get_doc("WAFD Recipe", batch.recipe)
    if recipe.status != "نشطة / Active":
        frappe.throw("الوصفة غير نشطة / Recipe is inactive")
    yield_quantity = flt(recipe.yield_quantity)
    if yield_quantity <= 0:
        frappe.throw("كمية إنتاج الوصفة يجب أن تكون أكبر من صفر / Recipe yield must be greater than zero")
    if not recipe.items:
        frappe.throw("الوصفة لا تحتوي على مكونات / Recipe has no ingredients")
    factor = flt(batch.planned_quantity) / yield_quantity
    requirements = []
    for row in recipe.items:
        requirements.append({
            "ingredient": row.ingredient,
            "quantity": flt(row.quantity) * factor,
            "uom": row.uom,
            "unit_cost": flt(row.unit_cost),
        })
    return recipe, requirements


@frappe.whitelist()
def refresh_material_requirements(batch_name):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    batch._calculate_material_requirements()
    batch.save()
    return {
        "name": batch.name,
        "materials_status": batch.materials_status,
        "total_material_cost": batch.total_material_cost,
        "requirements": len(batch.material_requirements),
    }


@frappe.whitelist()
def check_material_availability(batch_name):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("read")
    if not batch.recipe:
        frappe.throw("حدد الوصفة أولاً / Select recipe first")
    batch._calculate_material_requirements()
    shortages = [
        {"ingredient": row.ingredient, "quantity": row.required_quantity,
         "available_quantity": row.available_quantity, "shortage_quantity": row.shortage_quantity, "uom": row.uom}
        for row in batch.material_requirements if flt(row.shortage_quantity) > 0
    ]
    return {
        "requirements": [row.as_dict() for row in batch.material_requirements],
        "allocations": [row.as_dict() for row in batch.material_allocations],
        "shortages": shortages, "available": not shortages,
    }


@frappe.whitelist()
def create_material_issue(batch_name):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    batch._calculate_material_requirements()
    shortages = [row for row in batch.material_requirements if flt(row.shortage_quantity) > 0]
    if shortages:
        lines = [f"{r.ingredient}: مطلوب {r.required_quantity}, متاح {r.available_quantity}" for r in shortages]
        frappe.throw("المخزون الإجمالي غير كافٍ / Combined stock is insufficient:<br>" + "<br>".join(lines))
    if not batch.material_allocations:
        frappe.throw("لا توجد تخصيصات صرف / No material allocations were generated")
    # Persist allocation child rows before linking generated stock movements.
    batch.save(ignore_permissions=True)
    batch.reload()

    by_warehouse = {}
    for row in batch.material_allocations:
        by_warehouse.setdefault(row.warehouse, []).append(row)
    created = []
    existing = []
    first_movement = None
    for warehouse, allocations in by_warehouse.items():
        linked = next((row.stock_movement for row in allocations if row.stock_movement and frappe.db.exists("WAFD Stock Movement", row.stock_movement)), None)
        if linked:
            existing.append(linked); first_movement = first_movement or linked; continue
        movement = frappe.get_doc({
            "doctype": "WAFD Stock Movement", "movement_type": "صرف / Issue", "posting_date": now_datetime(),
            "project": batch.project, "production_batch": batch.name, "source_warehouse": warehouse,
            "reference_type": "WAFD Production Batch", "reference_name": batch.name, "status": "مسودة / Draft",
            "notes": f"صرف مواد تلقائي لدفعة الإنتاج {batch.name} من {warehouse}",
        })
        for row in allocations:
            movement.append("items", {
                "ingredient": row.ingredient, "quantity": row.allocated_quantity, "uom": row.uom,
                "unit_cost": row.unit_cost, "amount": row.amount,
            })
        movement.insert()
        created.append(movement.name); first_movement = first_movement or movement.name
        for row in allocations:
            frappe.db.set_value(row.doctype, row.name, "stock_movement", movement.name, update_modified=False)
    if first_movement:
        batch.db_set("material_issue", first_movement, update_modified=False)
    batch.reload()
    return {"created": created, "existing": existing, "count": len(created) + len(existing), "primary": first_movement}


@frappe.whitelist()
def create_quality_inspection(batch_name):
    """Return an existing inspection or safe defaults for a new one.

    A quality inspection cannot be inserted before the inspector enters the
    decision and verification fields. Returning defaults avoids creating an
    invalid Conditional record that requires a corrective action.
    """
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    existing = frappe.db.get_value("WAFD Quality Inspection", {"production_batch": batch.name}, "name")
    if existing:
        return {"name": existing, "created": False}
    return {
        "created": True,
        "values": {
            "production_batch": batch.name,
            "inspection_date": now_datetime(),
            "inspector": frappe.session.user,
        },
    }


@frappe.whitelist()
def create_packaging_record(batch_name):
    """Backward-compatible endpoint using the canonical workflow service."""
    from wafd_one.operations import create_packaging_record as create_record

    return create_record(batch_name)


def _open_noncompliant_ccp_checks(batch_name):
    return frappe.get_all(
        "WAFD CCP Check",
        filters={
            "production_batch": batch_name,
            "compliance_status": "غير مطابق / Noncompliant",
            "verification_status": ["!=", "تم التحقق / Verified"],
        },
        pluck="name",
    )


@frappe.whitelist()
def release_food_safety_batch(batch_name):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    frappe.db.sql("select name from `tabWAFD Production Batch` where name=%s for update", batch.name)
    batch.reload()
    if batch.food_safety_release_status == "مفرج / Released":
        return {"name": batch.name, "released": False}
    settings = frappe.get_single("WAFD Food Safety Settings")
    if settings.require_passed_quality_before_release and batch.quality_status != "ناجح / Passed":
        frappe.throw("يجب نجاح فحص الجودة قبل الإفراج / A passed quality inspection is required before release")
    checks = frappe.get_all("WAFD CCP Check", filters={"production_batch": batch.name}, fields=["name", "compliance_status", "verification_status"])
    if settings.require_ccp_checks_before_release and not checks:
        frappe.throw("يجب تسجيل فحص نقطة تحكم حرجة واحد على الأقل / At least one CCP check is required")
    unverified = [row.name for row in checks if row.verification_status != "تم التحقق / Verified"]
    if unverified:
        frappe.throw("توجد فحوص لم يتم التحقق منها: " + ", ".join(unverified) + " / Unverified CCP checks exist")
    unresolved = [
        row.name for row in checks
        if row.compliance_status == "غير مطابق / Noncompliant"
        and row.verification_status != "تم التحقق / Verified"
    ]
    if unresolved:
        frappe.throw("لا يمكن الإفراج مع وجود انحرافات غير مطابقة: " + ", ".join(unresolved) + " / Noncompliant CCP checks block release")
    batch.db_set({
        "food_safety_release_status": "مفرج / Released",
        "released_by": frappe.session.user,
        "released_on": now_datetime(),
    }, update_modified=True)
    return {"name": batch.name, "released": True, "traceability_code": batch.traceability_code}


@frappe.whitelist()
def hold_food_safety_batch(batch_name, reason=None):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    if batch.food_safety_release_status == "مفرج / Released":
        frappe.throw("لا يمكن إيقاف دفعة مفرج عنها دون إجراء سحب رسمي / A released batch requires a formal recall process")
    batch.db_set("food_safety_release_status", "موقوف / On Hold", update_modified=True)
    if reason:
        batch.add_comment("Comment", "Food safety hold: " + reason)
    return {"name": batch.name, "held": True}
