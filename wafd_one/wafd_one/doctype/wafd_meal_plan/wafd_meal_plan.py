import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WAFDMealPlan(Document):
    def validate(self):
        if flt(self.quantity) <= 0:
            frappe.throw("الكمية يجب أن تكون أكبر من صفر / Quantity must be greater than zero")
        self._validate_project_hotel()
        self._load_recipe_cost()
        self.total_value = flt(self.quantity) * flt(self.unit_price)
        self.estimated_cost = flt(self.quantity) * flt(self.estimated_unit_cost)
        self.estimated_profit = flt(self.total_value) - flt(self.estimated_cost)
        self.estimated_margin_percent = (
            flt(self.estimated_profit) / flt(self.total_value) * 100 if self.total_value else 0
        )

    def _validate_project_hotel(self):
        if not self.project or not self.hotel:
            return

        project = frappe.get_doc("WAFD Catering Project", self.project)
        allowed_hotels = {row.hotel for row in (project.hotels or []) if row.hotel}
        if project.primary_hotel:
            allowed_hotels.add(project.primary_hotel)

        # Projects created before v4.2.3 may not yet contain hotel rows.
        # Attach the first selected hotel safely so old records remain usable.
        if not allowed_hotels:
            project.primary_hotel = self.hotel
            project.append("hotels", {
                "hotel": self.hotel,
                "guest_count": project.beneficiary_count or 0,
            })
            project.flags.from_meal_plan_sync = True
            project.save(ignore_permissions=True)
            return

        if self.hotel not in allowed_hotels:
            frappe.throw(
                "الفندق المحدد غير مرتبط بالمشروع / Selected hotel is not linked to the project"
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
