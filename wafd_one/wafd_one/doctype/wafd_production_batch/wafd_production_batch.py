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
        self.completion_percent = (flt(produced) / flt(planned) * 100) if planned else 0
        self.remaining_quantity = max(planned - produced - rejected, 0)

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

    def _ensure_recipe_source_warehouses(self):
        """Add the appropriate WAFD warehouse for every recipe ingredient category.

        This keeps mixed recipes (dry, chilled, frozen and vegetables) from being
        diagnosed against a single warehouse only. Existing user-selected sources
        remain first and are never removed.
        """
        if not self.recipe:
            return
        from wafd_one.master_data import CATEGORY_WAREHOUSE_MAP
        existing = {row.warehouse for row in (self.source_warehouses or []) if row.warehouse}
        recipe = frappe.get_doc("WAFD Recipe", self.recipe)
        priority = max([cint(row.priority) for row in (self.source_warehouses or [])] or [0])
        for item in recipe.items:
            category = frappe.db.get_value("WAFD Ingredient", item.ingredient, "category")
            warehouse = CATEGORY_WAREHOUSE_MAP.get(category)
            if warehouse and frappe.db.exists("WAFD Warehouse", warehouse) and warehouse not in existing:
                priority += 1
                self.append("source_warehouses", {"warehouse": warehouse, "priority": priority, "is_default": 0})
                existing.add(warehouse)

    def _calculate_material_requirements(self):
        self._ensure_recipe_source_warehouses()
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
                balance = frappe.db.get_value(
                    "WAFD Stock Balance",
                    {"warehouse": source.warehouse, "ingredient": req["ingredient"]},
                    ["actual_quantity", "reserved_quantity", "available_quantity", "average_cost"],
                    as_dict=True,
                ) or {}
                # available_quantity can be stale on legacy/imported rows. Always derive a
                # safe live value from actual minus reserved when those fields are present.
                actual = flt(balance.get("actual_quantity"))
                reserved = flt(balance.get("reserved_quantity"))
                stored_available = flt(balance.get("available_quantity"))
                derived_available = max(actual - reserved, 0)
                available = derived_available if ("actual_quantity" in balance or "reserved_quantity" in balance) else max(stored_available, 0)
                if balance and abs(stored_available - derived_available) > 0.000001:
                    frappe.db.set_value(
                        "WAFD Stock Balance",
                        {"warehouse": source.warehouse, "ingredient": req["ingredient"]},
                        "available_quantity",
                        derived_available,
                        update_modified=False,
                    )
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
            issued_quantity = 0
            for allocation in (self.material_allocations or []):
                if allocation.ingredient != req["ingredient"] or not allocation.stock_movement:
                    continue
                if frappe.db.get_value("WAFD Stock Movement", allocation.stock_movement, "status") == "مرحلة / Posted":
                    issued_quantity += flt(allocation.allocated_quantity)
            self.append("material_requirements", {
                "ingredient": req["ingredient"], "required_quantity": req["quantity"], "uom": req["uom"],
                "available_quantity": available_total, "issued_quantity": issued_quantity, "shortage_quantity": shortage,
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
        previous = self.get_doc_before_save() if not self.is_new() else None
        entering_active = self.status in active and (not previous or previous.status not in active)
        # Only validate stock movement prerequisites when the document is actually
        # transitioning into production. Normal saves while still Planned must never
        # be blocked, otherwise the user cannot save the batch and create the issue.
        if entering_active:
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
def get_stock_diagnostics(batch_name):
    """Return precise reasons for zero availability without guessing stock."""
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("read")
    batch._calculate_material_requirements()
    sources = [row.warehouse for row in batch._source_rows()]
    missing = []
    zero = []
    for row in batch.material_requirements:
        balances = frappe.get_all(
            "WAFD Stock Balance",
            filters={"warehouse": ["in", sources], "ingredient": row.ingredient},
            fields=["warehouse", "actual_quantity", "reserved_quantity", "available_quantity"],
        ) if sources else []
        if not balances:
            missing.append(row.ingredient)
        elif sum(max(flt(x.actual_quantity) - flt(x.reserved_quantity), 0) for x in balances) <= 0:
            zero.append(row.ingredient)
    return {
        "sources": sources,
        "missing_balance_rows": missing,
        "zero_balance_items": zero,
        "materials_status": batch.materials_status,
        "available": not missing and not zero,
    }


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
def start_production(batch_name):
    """Start production without leaving the form in an unsaved deadlock state."""
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    if batch.status != "مخطط / Planned":
        return {"name": batch.name, "status": batch.status, "started": False}
    batch._calculate_material_requirements()
    movements = {row.stock_movement for row in (batch.material_allocations or []) if row.stock_movement}
    if not movements:
        frappe.throw("يجب إنشاء حركات صرف المواد قبل بدء الإنتاج / Material issues must be created before production")
    unposted = [name for name in movements if frappe.db.get_value("WAFD Stock Movement", name, "status") != "مرحلة / Posted"]
    if unposted:
        frappe.throw("يجب ترحيل جميع حركات الصرف أولاً: " + ", ".join(unposted) + " / Post all material issues first")
    batch.status = "تحضير / Preparing"
    batch.start_time = batch.start_time or now_datetime()
    batch.save()
    return {"name": batch.name, "status": batch.status, "started": True}


@frappe.whitelist()
def complete_production(batch_name, produced_quantity=None, rejected_quantity=None):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    if batch.status not in ("تحضير / Preparing", "طبخ / Cooking"):
        frappe.throw("يمكن إكمال الإنتاج فقط بعد بدء الدفعة / Production can only be completed after it starts")
    if produced_quantity is not None:
        batch.produced_quantity = cint(produced_quantity)
    elif not cint(batch.produced_quantity):
        batch.produced_quantity = cint(batch.planned_quantity)
    if rejected_quantity is not None:
        batch.rejected_quantity = cint(rejected_quantity)
    batch.status = "جاهز / Ready"
    batch.end_time = now_datetime()
    batch.save()
    return {"name": batch.name, "status": batch.status, "completed": True}


@frappe.whitelist()
def prepare_uat_test_stock(batch_name, buffer_percent=25):
    """Create and post clearly-labelled test receipt movements for current shortages.

    This is an explicit UAT helper, never an automatic migration. It adds only the
    quantity required by the selected production batch plus a small configurable
    buffer, and records every addition through auditable WAFD Stock Movements.
    """
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")

    allowed_roles = {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}
    if not allowed_roles.intersection(set(frappe.get_roles())):
        frappe.throw("هذه الأداة مخصصة لمسؤول النظام أو العمليات أو المستودع / This UAT stock tool requires an authorized role")

    if batch.status != "مخطط / Planned":
        frappe.throw("يمكن تجهيز مخزون الاختبار للدفعات المخططة فقط / UAT stock can only be prepared for Planned batches")

    buffer_percent = max(0, min(flt(buffer_percent), 100))
    batch._calculate_material_requirements()
    shortages = [row for row in batch.material_requirements if flt(row.shortage_quantity) > 0]
    if not shortages:
        return {"created": [], "posted": [], "count": 0, "already_available": True}

    from wafd_one.master_data import CATEGORY_WAREHOUSE_MAP
    from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import post_movement

    source_names = {row.warehouse for row in (batch.source_warehouses or []) if row.warehouse}
    priority = max([cint(row.priority) for row in (batch.source_warehouses or [])] or [0])
    grouped = {}

    for req in shortages:
        ingredient = frappe.db.get_value(
            "WAFD Ingredient", req.ingredient, ["category", "uom"], as_dict=True
        ) or {}
        warehouse = CATEGORY_WAREHOUSE_MAP.get(ingredient.get("category")) or batch.source_warehouse
        if not warehouse or not frappe.db.exists("WAFD Warehouse", warehouse):
            frappe.throw(f"لا يوجد مستودع اختبار مناسب للصنف {req.ingredient} / No suitable UAT warehouse for ingredient")

        if warehouse not in source_names:
            priority += 1
            batch.append("source_warehouses", {"warehouse": warehouse, "priority": priority, "is_default": 0})
            source_names.add(warehouse)

        shortage = flt(req.shortage_quantity)
        buffer_qty = shortage * buffer_percent / 100
        receipt_qty = shortage + buffer_qty
        # Preserve fractional recipe quantities while ensuring a useful minimum buffer.
        if buffer_percent and buffer_qty < 0.1:
            receipt_qty = shortage + 0.1

        grouped.setdefault(warehouse, []).append({
            "ingredient": req.ingredient,
            "quantity": receipt_qty,
            "uom": req.uom or ingredient.get("uom"),
            "unit_cost": flt(req.unit_cost),
        })

    batch.save(ignore_permissions=True)
    created = []
    posted = []
    for warehouse, items in grouped.items():
        movement = frappe.get_doc({
            "doctype": "WAFD Stock Movement",
            "movement_type": "استلام / Receipt",
            "posting_date": now_datetime(),
            "project": batch.project,
            "production_batch": batch.name,
            "target_warehouse": warehouse,
            "reference_type": "WAFD Production Batch",
            "reference_name": batch.name,
            "status": "مسودة / Draft",
            "notes": f"UAT TEST STOCK ONLY — مخزون اختبار مؤقت للدفعة {batch.name}; buffer={buffer_percent}%",
        })
        for item in items:
            movement.append("items", item)
        movement.insert(ignore_permissions=True)
        created.append(movement.name)
        result = post_movement(movement.name)
        if result.get("posted") or frappe.db.get_value("WAFD Stock Movement", movement.name, "status") == "مرحلة / Posted":
            posted.append(movement.name)

    batch.reload()
    batch._calculate_material_requirements()
    batch.save(ignore_permissions=True)
    remaining = [row.ingredient for row in batch.material_requirements if flt(row.shortage_quantity) > 0]
    if remaining:
        frappe.throw("تم إنشاء مخزون الاختبار لكن بقي عجز في: " + ", ".join(remaining) + " / UAT stock was posted but shortages remain")

    return {
        "created": created,
        "posted": posted,
        "count": len(posted),
        "already_available": False,
        "materials_status": batch.materials_status,
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
