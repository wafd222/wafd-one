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

    def _calculate_material_requirements(self):
        self.set("material_requirements", [])
        self.total_material_cost = 0
        self.materials_status = "لم تحسب / Not Calculated"
        if not self.recipe or not self.planned_quantity:
            return
        _, requirements = _recipe_requirements(self)
        has_shortage = False
        for row in requirements:
            available = 0
            if self.source_warehouse:
                available = flt(frappe.db.get_value(
                    "WAFD Stock Balance",
                    {"warehouse": self.source_warehouse, "ingredient": row["ingredient"]},
                    "available_quantity",
                ) or 0)
            shortage = max(flt(row["quantity"]) - available, 0) if self.source_warehouse else flt(row["quantity"])
            has_shortage = has_shortage or shortage > 0
            amount = flt(row["quantity"]) * flt(row["unit_cost"])
            self.total_material_cost += amount
            self.append("material_requirements", {
                "ingredient": row["ingredient"],
                "required_quantity": row["quantity"],
                "uom": row["uom"],
                "available_quantity": available,
                "shortage_quantity": shortage,
                "unit_cost": row["unit_cost"],
                "amount": amount,
                "availability_status": "ناقص / Shortage" if shortage else "متوفر / Available",
            })
        if self.material_issue and frappe.db.get_value("WAFD Stock Movement", self.material_issue, "status") == "مرحلة / Posted":
            self.materials_status = "مصروفة / Issued"
        elif not self.source_warehouse:
            self.materials_status = "لم تحسب / Not Calculated"
        else:
            self.materials_status = "عجز / Shortage" if has_shortage else "متوفرة / Available"

    def _validate_workflow(self):
        active = ("تحضير / Preparing", "طبخ / Cooking", "تغليف / Packaging", "جاهز / Ready", "مكتمل / Completed")
        if self.status in active:
            if not self.material_issue:
                frappe.throw("يجب إنشاء وترحيل صرف المواد قبل بدء الإنتاج / Material issue must be created and posted before production")
            status = frappe.db.get_value("WAFD Stock Movement", self.material_issue, "status")
            if status != "مرحلة / Posted":
                frappe.throw("يجب ترحيل حركة صرف المواد أولاً / Post the material issue first")
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
    if not batch.recipe or not batch.source_warehouse:
        frappe.throw("حدد الوصفة ومستودع الصرف / Select recipe and source warehouse")
    _, requirements = _recipe_requirements(batch)
    shortages = []
    for row in requirements:
        available = flt(frappe.db.get_value("WAFD Stock Balance", {"warehouse": batch.source_warehouse, "ingredient": row["ingredient"]}, "available_quantity") or 0)
        row["available_quantity"] = available
        row["shortage_quantity"] = max(flt(row["quantity"]) - available, 0)
        if row["shortage_quantity"] > 0:
            shortages.append(row)
    return {"requirements": requirements, "shortages": shortages, "available": not shortages}


@frappe.whitelist()
def create_material_issue(batch_name):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    if batch.material_issue and frappe.db.exists("WAFD Stock Movement", batch.material_issue):
        return {"name": batch.material_issue, "created": False}
    if not batch.source_warehouse:
        frappe.throw("حدد مستودع الصرف أولاً / Select the source warehouse first")
    availability = check_material_availability(batch.name)
    if not availability["available"]:
        lines = [f'{r["ingredient"]}: مطلوب {r["quantity"]}, متاح {r["available_quantity"]}' for r in availability["shortages"]]
        frappe.throw("المخزون غير كافٍ / Insufficient stock:<br>" + "<br>".join(lines))
    _, requirements = _recipe_requirements(batch)
    movement = frappe.get_doc({
        "doctype": "WAFD Stock Movement", "movement_type": "صرف / Issue", "posting_date": now_datetime(),
        "project": batch.project, "production_batch": batch.name, "source_warehouse": batch.source_warehouse,
        "reference_type": "WAFD Production Batch", "reference_name": batch.name, "status": "مسودة / Draft",
        "notes": f"صرف مواد تلقائي لدفعة الإنتاج {batch.name}",
    })
    for row in requirements:
        movement.append("items", row)
    movement.insert()
    batch.db_set("material_issue", movement.name, update_modified=False)
    return {"name": movement.name, "created": True}


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
    unresolved = [row.name for row in checks if row.compliance_status == "غير مطابق / Noncompliant"]
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
