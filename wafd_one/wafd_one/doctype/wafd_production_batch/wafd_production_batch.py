import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime


class WafdProductionBatch(Document):
    def validate(self):
        produced = cint(self.produced_quantity)
        rejected = cint(self.rejected_quantity)
        planned = cint(self.planned_quantity)
        packed = cint(self.packed_quantity)
        if planned <= 0:
            frappe.throw("الكمية المخططة يجب أن تكون أكبر من صفر / Planned quantity must be greater than zero")
        if min(produced, rejected, packed) < 0:
            frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
        if produced + rejected > planned:
            frappe.throw("مجموع المنتج والمرفوض لا يمكن أن يتجاوز الكمية المخططة")
        if packed > produced:
            frappe.throw("الكمية المغلفة لا يمكن أن تتجاوز الكمية المنتجة / Packed quantity cannot exceed produced quantity")
        if cint(self.box_count) and cint(self.units_per_box) and packed > cint(self.box_count) * cint(self.units_per_box):
            frappe.throw("الكمية المغلفة تتجاوز سعة الصناديق / Packed quantity exceeds box capacity")
        self.actual_yield_percent = (flt(produced) / flt(planned) * 100) if planned else 0
        self._sync_from_meal_plan()
        self._validate_workflow()

    def _sync_from_meal_plan(self):
        if not self.meal_plan:
            return
        values = frappe.db.get_value("WAFD Meal Plan", self.meal_plan, ["project", "recipe", "quantity"], as_dict=True)
        if not values:
            frappe.throw("خطة الوجبة غير موجودة / Meal plan was not found")
        if self.project and self.project != values.project:
            frappe.throw("المشروع لا يطابق خطة الوجبة / Project does not match the meal plan")
        self.project = values.project
        self.recipe = values.recipe
        if not self.planned_quantity:
            self.planned_quantity = cint(values.quantity)

    def _validate_workflow(self):
        if self.status in ("تحضير / Preparing", "طبخ / Cooking", "تغليف / Packaging", "جاهز / Ready", "مكتمل / Completed"):
            if not self.material_issue:
                frappe.throw("يجب إنشاء وترحيل صرف المواد قبل بدء الإنتاج / Material issue must be created and posted before production")
            status = frappe.db.get_value("WAFD Stock Movement", self.material_issue, "status")
            if status != "مرحلة / Posted":
                frappe.throw("يجب ترحيل حركة صرف المواد أولاً / Post the material issue first")
        if self.status in ("جاهز / Ready", "مكتمل / Completed") and self.quality_status != "ناجح / Passed":
            frappe.throw("لا يمكن اعتماد الدفعة كجاهزة قبل نجاح فحص الجودة / A passed quality inspection is required")

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
    recipe = frappe.get_doc("WAFD Recipe", batch.recipe)
    yield_quantity = flt(recipe.yield_quantity)
    if yield_quantity <= 0:
        frappe.throw("كمية إنتاج الوصفة يجب أن تكون أكبر من صفر / Recipe yield must be greater than zero")
    if not recipe.items:
        frappe.throw("الوصفة لا تحتوي على مكونات / Recipe has no ingredients")
    factor = flt(batch.planned_quantity) / yield_quantity
    return recipe, [{"ingredient": r.ingredient, "quantity": flt(r.quantity) * factor, "uom": r.uom, "unit_cost": flt(r.unit_cost)} for r in recipe.items]


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
    if not batch.recipe:
        frappe.throw("حدد الوصفة أولاً / Select a recipe first")
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
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    existing = frappe.db.get_value("WAFD Quality Inspection", {"production_batch": batch.name}, "name")
    if existing:
        return {"name": existing, "created": False}
    doc = frappe.get_doc({"doctype": "WAFD Quality Inspection", "production_batch": batch.name, "inspection_date": now_datetime(), "inspector": frappe.session.user, "result": "مشروط / Conditional"})
    doc.insert()
    return {"name": doc.name, "created": True}
