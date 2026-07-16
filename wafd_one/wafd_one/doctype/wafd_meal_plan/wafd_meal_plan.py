import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WafdMealPlan(Document):
    def validate(self):
        if flt(self.quantity) <= 0:
            frappe.throw("الكمية يجب أن تكون أكبر من صفر / Quantity must be greater than zero")
        self._load_recipe_cost()
        self.total_value = flt(self.quantity) * flt(self.unit_price)
        self.estimated_cost = flt(self.quantity) * flt(self.estimated_unit_cost)
        self.estimated_profit = flt(self.total_value) - flt(self.estimated_cost)
        self.estimated_margin_percent = (
            flt(self.estimated_profit) / flt(self.total_value) * 100 if self.total_value else 0
        )

    def _load_recipe_cost(self):
        if not self.recipe:
            return
        cost = frappe.db.get_value("WAFD Recipe", self.recipe, "cost_per_portion")
        self.estimated_unit_cost = flt(cost)


@frappe.whitelist()
def create_production_batch(meal_plan_name):
    meal_plan = frappe.get_doc("WAFD Meal Plan", meal_plan_name)
    meal_plan.check_permission("write")
    existing = frappe.db.get_value("WAFD Production Batch", {"meal_plan": meal_plan.name}, "name")
    if existing:
        return {"name": existing, "created": False}
    if not meal_plan.recipe:
        frappe.throw("حدد وصفة في خطة الوجبة أولاً / Select a recipe in the meal plan first")
    batch = frappe.get_doc({
        "doctype": "WAFD Production Batch",
        "project": meal_plan.project,
        "meal_plan": meal_plan.name,
        "recipe": meal_plan.recipe,
        "batch_date": meal_plan.service_date,
        "planned_quantity": meal_plan.quantity,
        "status": "مخطط / Planned",
    })
    batch.insert()
    meal_plan.db_set("status", "معتمد / Approved", update_modified=False)
    return {"name": batch.name, "created": True}
