import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class WAFDMealPlan(Document):
    def validate(self):
        if flt(self.quantity) <= 0:
            frappe.throw("الكمية يجب أن تكون أكبر من صفر / Quantity must be greater than zero")
        self._validate_project_dates_and_locking()
        self._validate_project_hotel()
        self._load_recipe_cost()
        from wafd_one.planning import validate_meal_plan_capacity
        validate_meal_plan_capacity(self)
        self.total_value = flt(self.quantity) * flt(self.unit_price)
        self.estimated_cost = flt(self.quantity) * flt(self.estimated_unit_cost)
        self.estimated_profit = flt(self.total_value) - flt(self.estimated_cost)
        self.estimated_margin_percent = (
            flt(self.estimated_profit) / flt(self.total_value) * 100 if self.total_value else 0
        )

    def _validate_project_dates_and_locking(self):
        if not self.project or not self.service_date:
            return
        values = frappe.db.get_value(
            "WAFD Catering Project", self.project,
            ["start_date", "end_date", "status"], as_dict=True,
        )
        if not values:
            frappe.throw("المشروع غير موجود / Project not found")
        service_date = getdate(self.service_date)
        if values.start_date and service_date < getdate(values.start_date):
            frappe.throw("تاريخ الخدمة يسبق بداية المشروع / Service date is before project start")
        if values.end_date and service_date > getdate(values.end_date):
            frappe.throw("تاريخ الخدمة بعد نهاية المشروع / Service date is after project end")
        if values.status in ("مكتمل / Completed", "ملغي / Cancelled"):
            frappe.throw("لا يمكن تعديل خطة وجبات لمشروع مكتمل أو ملغي / Cannot edit meal plan for a completed or cancelled project")

        duplicate = frappe.db.get_value(
            "WAFD Meal Plan",
            {"project": self.project, "hotel": self.hotel, "service_date": self.service_date,
             "meal_type": self.meal_type, "name": ["!=", self.name or ""]},
            "name",
        )
        if duplicate:
            frappe.throw(f"توجد خطة مماثلة لنفس الفندق والتاريخ ونوع الوجبة: {duplicate} / Duplicate meal plan exists")

        if self.is_new():
            return
        old = self.get_doc_before_save()
        if not old:
            return
        batch = frappe.db.get_value("WAFD Production Batch", {"meal_plan": self.name}, ["name", "status"], as_dict=True)
        if batch and batch.status != "مخطط / Planned":
            protected = ("project", "hotel", "service_date", "meal_type", "quantity", "recipe")
            changed = [field for field in protected if self.get(field) != old.get(field)]
            if changed:
                frappe.throw("لا يمكن تغيير بيانات التخطيط الأساسية بعد بدء الإنتاج / Core planning data cannot change after production starts")

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
