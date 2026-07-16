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
