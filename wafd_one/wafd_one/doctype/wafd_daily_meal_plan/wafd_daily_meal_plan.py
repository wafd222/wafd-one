import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate


class WAFDDailyMealPlan(Document):
    def validate(self):
        self._validate_project_context()
        self._validate_unique_day()
        self._validate_source_warehouses()
        self._calculate_rows_and_totals()
        self._set_readiness_status()

    def _validate_project_context(self):
        if not self.project:
            return
        project = frappe.get_doc("WAFD Catering Project", self.project)
        if project.start_date and self.service_date and getdate(self.service_date) < getdate(project.start_date):
            frappe.throw("تاريخ الخطة يسبق بداية المشروع / Daily plan date is before project start")
        if project.end_date and self.service_date and getdate(self.service_date) > getdate(project.end_date):
            frappe.throw("تاريخ الخطة بعد نهاية المشروع / Daily plan date is after project end")
        allowed = {row.hotel for row in (project.hotels or []) if row.hotel}
        if project.primary_hotel:
            allowed.add(project.primary_hotel)
        if self.hotel and allowed and self.hotel not in allowed:
            frappe.throw("الفندق غير مرتبط بالمشروع / Hotel is not linked to the project")
        self.kitchen = self.kitchen or project.default_kitchen
        if not self.source_warehouses:
            project_sources = list(getattr(project, "source_warehouses", []) or [])
            if not project_sources and self.kitchen:
                kitchen = frappe.get_doc("WAFD Kitchen", self.kitchen)
                project_sources = list(getattr(kitchen, "source_warehouses", []) or [])
                if not project_sources and getattr(kitchen, "default_warehouse", None):
                    project_sources = [{"warehouse": kitchen.default_warehouse, "priority": 1, "is_default": 1}]
            if not project_sources and getattr(project, "default_source_warehouse", None):
                project_sources = [{"warehouse": project.default_source_warehouse, "priority": 1, "is_default": 1}]
            for source in project_sources:
                getter = source.get if isinstance(source, dict) else lambda key, default=None: getattr(source, key, default)
                self.append("source_warehouses", {
                    "warehouse": getter("warehouse"), "priority": getter("priority", 1),
                    "material_category": getter("material_category"), "is_default": getter("is_default", 0),
                    "allocation_percent": getter("allocation_percent"), "notes": getter("notes"),
                })
        self.source_warehouse = self.source_warehouse or getattr(project, "default_source_warehouse", None)
        if not self.plan_title and self.service_date and self.hotel:
            self.plan_title = f"{project.project_name} - {self.hotel} - {self.service_date}"

    def _validate_unique_day(self):
        if not (self.project and self.hotel and self.service_date):
            return
        duplicate = frappe.db.get_value(
            "WAFD Daily Meal Plan",
            {"project": self.project, "hotel": self.hotel, "service_date": self.service_date,
             "name": ["!=", self.name or ""]},
            "name",
        )
        if duplicate:
            frappe.throw(f"توجد خطة يومية لنفس المشروع والفندق والتاريخ: {duplicate} / Duplicate daily plan exists")


    def _validate_source_warehouses(self):
        # Preserve backward compatibility while making the table authoritative.
        if self.source_warehouse and not self.source_warehouses:
            self.append("source_warehouses", {"warehouse": self.source_warehouse, "priority": 1, "is_default": 1})
        if not self.source_warehouses:
            frappe.throw("اختر مستودعاً أو ثلاجة واحدة على الأقل / Select at least one warehouse or cold room")
        seen = set()
        defaults = 0
        for index, row in enumerate(sorted(self.source_warehouses, key=lambda x: (cint(x.priority) or 9999, x.idx)), start=1):
            if not row.warehouse:
                frappe.throw("حدد المستودع في جميع صفوف مصادر الصرف / Select a warehouse in every source row")
            if row.warehouse in seen:
                frappe.throw(f"المستودع مكرر: {row.warehouse} / Duplicate source warehouse")
            seen.add(row.warehouse)
            row.priority = cint(row.priority) or index
            defaults += cint(row.is_default)
        if defaults > 1:
            frappe.throw("يمكن تحديد مصدر افتراضي واحد فقط / Only one default source is allowed")
        ordered = sorted(self.source_warehouses, key=lambda x: (0 if cint(x.is_default) else 1, cint(x.priority), x.idx))
        self.source_warehouse = ordered[0].warehouse

    def _calculate_rows_and_totals(self):
        if not self.meals:
            frappe.throw("أضف وجبة واحدة على الأقل / Add at least one meal")
        seen = set()
        total_quantity = total_value = estimated_cost = 0
        missing_recipe_count = production_batch_count = 0
        for row in self.meals:
            if row.meal_type in seen:
                frappe.throw(f"نوع الوجبة مكرر: {row.meal_type} / Duplicate meal type")
            seen.add(row.meal_type)
            if cint(row.quantity) <= 0:
                frappe.throw(f"الكمية يجب أن تكون أكبر من صفر في صف {row.idx} / Quantity must be positive")
            if row.recipe:
                recipe = frappe.db.get_value("WAFD Recipe", row.recipe, ["cost_per_portion", "recipe_name"], as_dict=True)
                if recipe:
                    row.estimated_unit_cost = flt(recipe.cost_per_portion)
                    row.menu_name = row.menu_name or recipe.recipe_name
            else:
                missing_recipe_count += 1
            row.total_value = cint(row.quantity) * flt(row.unit_price)
            row.estimated_cost = cint(row.quantity) * flt(row.estimated_unit_cost)
            row.estimated_profit = flt(row.total_value) - flt(row.estimated_cost)
            row.estimated_margin_percent = (flt(row.estimated_profit) / flt(row.total_value) * 100) if row.total_value else 0
            total_quantity += cint(row.quantity)
            total_value += flt(row.total_value)
            estimated_cost += flt(row.estimated_cost)
            if row.production_batch:
                production_batch_count += 1
        self.total_quantity = total_quantity
        self.total_value = total_value
        self.estimated_cost = estimated_cost
        self.estimated_profit = total_value - estimated_cost
        self.estimated_margin_percent = (self.estimated_profit / total_value * 100) if total_value else 0
        self.missing_recipe_count = missing_recipe_count
        self.production_batch_count = production_batch_count

    def _set_readiness_status(self):
        if self.status in ("ملغاة / Cancelled", "تم التسليم / Delivered", "جاهزة / Ready", "قيد الإنتاج / In Production"):
            return
        self.status = "جاهزة للاعتماد / Ready for Approval" if not self.missing_recipe_count else "مسودة / Draft"


@frappe.whitelist()
def create_production_batches(daily_plan_name):
    daily = frappe.get_doc("WAFD Daily Meal Plan", daily_plan_name)
    daily.check_permission("write")
    if daily.missing_recipe_count:
        frappe.throw("حدد وصفة لكل وجبة قبل إنشاء الإنتاج / Select a recipe for every meal")
    created = skipped = 0
    for row in daily.meals:
        plan_name = row.meal_plan
        if not plan_name:
            plan_name = frappe.db.get_value("WAFD Meal Plan", {
                "project": daily.project, "hotel": daily.hotel, "service_date": daily.service_date,
                "meal_type": row.meal_type,
            }, "name")
        if not plan_name:
            plan = frappe.get_doc({
                "doctype": "WAFD Meal Plan", "project": daily.project, "hotel": daily.hotel,
                "service_date": daily.service_date, "meal_type": row.meal_type,
                "quantity": row.quantity, "service_time": row.service_time, "menu_name": row.menu_name,
                "recipe": row.recipe, "unit_price": row.unit_price,
                "estimated_unit_cost": row.estimated_unit_cost, "status": "معتمد / Approved",
            })
            plan.insert(ignore_permissions=True)
            plan_name = plan.name
        existing = frappe.db.get_value("WAFD Production Batch", {"meal_plan": plan_name}, "name")
        if existing:
            batch_name = existing
            skipped += 1
        else:
            batch = frappe.get_doc({
                "doctype": "WAFD Production Batch", "project": daily.project,
                "meal_plan": plan_name, "daily_plan": daily.name, "recipe": row.recipe, "batch_date": daily.service_date,
                "planned_quantity": row.quantity, "kitchen": daily.kitchen,
                "source_warehouse": daily.source_warehouse, "status": "مخطط / Planned",
            })
            for source in daily.source_warehouses:
                batch.append("source_warehouses", {
                    "warehouse": source.warehouse, "priority": source.priority,
                    "material_category": source.material_category, "is_default": source.is_default,
                    "allocation_percent": source.allocation_percent, "notes": source.notes,
                })
            batch.insert(ignore_permissions=True)
            batch_name = batch.name
            created += 1
        frappe.db.set_value(row.doctype, row.name, {"meal_plan": plan_name, "production_batch": batch_name}, update_modified=False)
    daily.reload()
    daily.status = "قيد الإنتاج / In Production"
    daily.save(ignore_permissions=True)
    return {"created": created, "skipped": skipped, "total": len(daily.meals), "name": daily.name}
