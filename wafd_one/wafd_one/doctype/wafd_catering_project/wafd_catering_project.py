import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, cint


class WafdCateringProject(Document):
    def autoname(self):
        # Naming series generates the canonical project code and document name.
        pass

    def validate(self):
        self._validate_dates()
        self._calculate_services()
        self._calculate_summary()
        self._validate_approvals()

    def before_save(self):
        if self.name and not self.project_code:
            self.project_code = self.name

    def after_insert(self):
        if not self.project_code:
            frappe.db.set_value(self.doctype, self.name, "project_code", self.name, update_modified=False)

    def _validate_dates(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                frappe.throw("تاريخ النهاية يجب أن يكون بعد تاريخ البداية / End date must be after start date")
            self.duration_days = date_diff(self.end_date, self.start_date) + 1
        else:
            self.duration_days = 0

    def _calculate_services(self):
        total_meals = 0
        estimated_revenue = 0
        default_days = cint(self.duration_days) or 1
        default_beneficiaries = cint(self.beneficiary_count)
        for row in self.get("services") or []:
            days = cint(row.service_days) or default_days
            beneficiaries = cint(row.beneficiaries) or default_beneficiaries
            multiplier = flt(row.meals_per_person_per_day) or 1
            row.total_meals = cint(days * beneficiaries * multiplier)
            row.estimated_revenue = flt(row.total_meals) * flt(row.unit_price)
            total_meals += cint(row.total_meals)
            estimated_revenue += flt(row.estimated_revenue)
        self.total_meals = total_meals
        self.estimated_revenue = estimated_revenue or flt(self.contract_value)

    def _calculate_summary(self):
        self.remaining_meals = max(cint(self.total_meals) - cint(self.delivered_meals), 0)
        self.progress_percent = (flt(self.delivered_meals) / flt(self.total_meals) * 100) if self.total_meals else 0
        self.profit = flt(self.revenue) - flt(self.actual_cost)
        self.profit_margin_percent = (self.profit / flt(self.revenue) * 100) if self.revenue else 0

    def _validate_approvals(self):
        if self.is_new():
            return
        previous = self.get_doc_before_save()
        if not previous:
            return
        checks = {
            "project_manager_approved": {"System Manager", "WAFD Project Manager"},
            "operations_approved": {"System Manager", "WAFD Operations Manager"},
            "finance_approved": {"System Manager", "WAFD Finance User"},
            "general_manager_approved": {"System Manager"},
        }
        user_roles = set(frappe.get_roles())
        for fieldname, allowed_roles in checks.items():
            if cint(self.get(fieldname)) != cint(previous.get(fieldname)) and not user_roles.intersection(allowed_roles):
                frappe.throw(f"ليس لديك صلاحية تغيير الاعتماد: {self.meta.get_label(fieldname)}")


@frappe.whitelist()
def generate_meal_plans(project_name, replace_existing=0):
    """Generate daily meal plans from project services and assigned hotels."""
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("write")
    if not project.services:
        frappe.throw("أضف خدمات المشروع أولاً / Add project services first")
    if not project.hotels:
        frappe.throw("أضف فندقاً واحداً على الأقل / Add at least one hotel")

    replace_existing = cint(replace_existing)
    if replace_existing:
        existing = frappe.get_all("WAFD Meal Plan", filters={"project": project.name}, pluck="name")
        for name in existing:
            frappe.delete_doc("WAFD Meal Plan", name, ignore_permissions=True)

    created = 0
    skipped = 0
    from frappe.utils import add_days

    for service in project.services:
        days = min(cint(service.service_days) or cint(project.duration_days) or 1, cint(project.duration_days) or 1)
        total_beneficiaries = cint(service.beneficiaries) or cint(project.beneficiary_count)
        hotel_rows = project.hotels or []
        allocated = sum(cint(h.guest_count) for h in hotel_rows)

        for day_index in range(days):
            service_date = add_days(project.start_date, day_index)
            for hotel_row in hotel_rows:
                quantity = cint(hotel_row.guest_count)
                if not quantity:
                    quantity = total_beneficiaries if len(hotel_rows) == 1 else 0
                if not quantity and allocated == 0:
                    quantity = total_beneficiaries // len(hotel_rows)
                quantity = max(cint(quantity * (flt(service.meals_per_person_per_day) or 1)), 1)
                filters = {
                    "project": project.name,
                    "hotel": hotel_row.hotel,
                    "service_date": service_date,
                    "meal_type": service.service_type,
                    "source_service_row": service.name,
                }
                if frappe.db.exists("WAFD Meal Plan", filters):
                    skipped += 1
                    continue
                doc = frappe.get_doc({
                    "doctype": "WAFD Meal Plan",
                    **filters,
                    "quantity": quantity,
                    "service_time": service.service_time,
                    "menu_name": service.meal_name or service.service_type,
                    "recipe": service.recipe,
                    "unit_price": flt(service.unit_price),
                    "status": "مسودة / Draft",
                })
                doc.insert()
                created += 1
    return {"created": created, "skipped": skipped}
