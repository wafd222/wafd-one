import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime


class WafdProductionBatch(Document):
    def validate(self):
        produced = cint(self.produced_quantity)
        rejected = cint(self.rejected_quantity)
        planned = cint(self.planned_quantity)
        if planned <= 0:
            frappe.throw("الكمية المخططة يجب أن تكون أكبر من صفر / Planned quantity must be greater than zero")
        if produced < 0 or rejected < 0:
            frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
        if produced + rejected > planned:
            frappe.throw("مجموع المنتج والمرفوض لا يمكن أن يتجاوز الكمية المخططة")
        self.actual_yield_percent = (flt(produced) / flt(planned) * 100) if planned else 0
        self._sync_from_meal_plan()

    def _sync_from_meal_plan(self):
        if not self.meal_plan:
            return
        values = frappe.db.get_value(
            "WAFD Meal Plan", self.meal_plan, ["project", "recipe", "quantity"], as_dict=True
        )
        if not values:
            frappe.throw("خطة الوجبة غير موجودة / Meal plan was not found")
        if self.project and self.project != values.project:
            frappe.throw("المشروع لا يطابق خطة الوجبة / Project does not match the meal plan")
        self.project = values.project
        self.recipe = values.recipe
        if not self.planned_quantity:
            self.planned_quantity = cint(values.quantity)

    def on_update(self):
        self._update_meal_plan_status()

    def _update_meal_plan_status(self):
        if not self.meal_plan:
            return
        mapped = {
            "مخطط / Planned": "معتمد / Approved",
            "قيد الإنتاج / In Production": "قيد الإنتاج / In Production",
            "مكتمل / Completed": "جاهز / Ready",
        }
        status = mapped.get(self.status)
        if status:
            frappe.db.set_value("WAFD Meal Plan", self.meal_plan, "status", status, update_modified=False)


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

    recipe = frappe.get_doc("WAFD Recipe", batch.recipe)
    yield_quantity = flt(recipe.yield_quantity)
    if yield_quantity <= 0:
        frappe.throw("كمية إنتاج الوصفة يجب أن تكون أكبر من صفر / Recipe yield must be greater than zero")
    factor = flt(batch.planned_quantity) / yield_quantity
    if not recipe.items:
        frappe.throw("الوصفة لا تحتوي على مكونات / Recipe has no ingredients")

    movement = frappe.get_doc({
        "doctype": "WAFD Stock Movement",
        "movement_type": "صرف / Issue",
        "posting_date": now_datetime(),
        "project": batch.project,
        "production_batch": batch.name,
        "source_warehouse": batch.source_warehouse,
        "reference_type": "WAFD Production Batch",
        "reference_name": batch.name,
        "status": "مسودة / Draft",
        "notes": f"صرف مواد تلقائي لدفعة الإنتاج {batch.name}",
    })
    for row in recipe.items:
        movement.append("items", {
            "ingredient": row.ingredient,
            "quantity": flt(row.quantity) * factor,
            "uom": row.uom,
            "unit_cost": flt(row.unit_cost),
        })
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
    doc = frappe.get_doc({
        "doctype": "WAFD Quality Inspection",
        "production_batch": batch.name,
        "inspection_date": now_datetime(),
        "inspector": frappe.session.user,
        "result": "مشروط / Conditional",
    })
    doc.insert()
    return {"name": doc.name, "created": True}
