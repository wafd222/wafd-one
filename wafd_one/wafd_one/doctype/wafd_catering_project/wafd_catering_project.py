import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, get_datetime, now_datetime


class WAFDCateringProject(Document):
    def before_insert(self):
        # The document name is generated from autoname before this hook runs.
        # Keep the visible project code synchronized with the immutable ID.
        self.project_code = self.name

    def validate(self):
        if not self.project_code and self.name:
            self.project_code = self.name
        self.validate_approval_permissions()
        self.validate_dates()
        self.calculate_duration()
        self.calculate_hotel_totals()
        self.calculate_service_totals()
        self.calculate_progress()
        self.calculate_profitability()
        self.manage_approval_status()

    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw(_("تاريخ النهاية يجب أن يكون بعد أو مساويًا لتاريخ البداية"))

        for row in self.hotels or []:
            if row.service_start_date and row.service_end_date and row.service_end_date < row.service_start_date:
                frappe.throw(_("تاريخ نهاية خدمة الفندق {0} غير صحيح").format(row.hotel or row.idx))

        for row in self.services or []:
            if row.start_date and row.end_date and row.end_date < row.start_date:
                frappe.throw(_("تاريخ نهاية الخدمة في الصف {0} غير صحيح").format(row.idx))

    def calculate_duration(self):
        self.duration_days = date_diff(self.end_date, self.start_date) + 1 if self.start_date and self.end_date else 0

    def calculate_hotel_totals(self):
        self.hotel_guest_total = sum(int(row.guest_count or 0) for row in self.hotels or [])
        if self.hotels and not self.beneficiary_count:
            self.beneficiary_count = self.hotel_guest_total

    def calculate_service_totals(self):
        total_meals = 0
        for row in self.services or []:
            if row.start_date and row.end_date:
                row.service_days = date_diff(row.end_date, row.start_date) + 1
            elif not row.service_days:
                row.service_days = self.duration_days or 0
            row.total_meals = int(row.meals_per_day or 0) * int(row.service_days or 0)
            row.total_value = flt(row.total_meals) * flt(row.unit_price)
            total_meals += int(row.total_meals or 0)
        self.total_meals = total_meals
        self.meals_per_beneficiary = flt(total_meals) / flt(self.beneficiary_count) if self.beneficiary_count else 0

    def calculate_progress(self):
        delivered = min(int(self.delivered_meals or 0), int(self.total_meals or 0)) if self.total_meals else int(self.delivered_meals or 0)
        self.delivered_meals = delivered
        self.remaining_meals = max(int(self.total_meals or 0) - delivered, 0)
        self.progress_percent = (flt(delivered) / flt(self.total_meals) * 100) if self.total_meals else 0

    def calculate_profitability(self):
        self.estimated_profit = flt(self.contract_value) - flt(self.estimated_cost)
        self.estimated_margin_percent = (flt(self.estimated_profit) / flt(self.contract_value) * 100) if self.contract_value else 0
        self.profit = flt(self.revenue) - flt(self.actual_cost)
        self.profit_margin_percent = (flt(self.profit) / flt(self.revenue) * 100) if self.revenue else 0
        self.cost_per_meal = flt(self.actual_cost) / flt(self.total_meals) if self.total_meals else 0

    def validate_approval_permissions(self):
        """Prevent users from approving stages outside their assigned role."""
        if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles():
            return

        previous = self.get_doc_before_save()
        role_map = {
            "project_manager_approval": "WAFD Project Manager",
            "operations_approval": "WAFD Operations Manager",
            "finance_approval": "WAFD Finance User",
            # General-manager approval is intentionally restricted to System Manager
            # until a dedicated WAFD General Manager role is introduced.
            "general_manager_approval": "System Manager",
        }
        user_roles = set(frappe.get_roles())
        for fieldname, required_role in role_map.items():
            old_value = int(getattr(previous, fieldname, 0) or 0) if previous else 0
            new_value = int(getattr(self, fieldname, 0) or 0)
            if old_value != new_value and required_role not in user_roles:
                frappe.throw(_("ليس لديك صلاحية لتغيير الاعتماد: {0}").format(self.meta.get_label(fieldname)))

    def manage_approval_status(self):
        approvals = [self.project_manager_approval, self.operations_approval, self.finance_approval, self.general_manager_approval]
        if all(approvals):
            if self.status in ("مسودة / Draft", "تخطيط / Planning", "بانتظار الاعتماد / Pending Approval"):
                self.status = "معتمد / Approved"
            if not self.approved_by:
                self.approved_by = frappe.session.user
                self.approved_on = now_datetime()
        elif any(approvals) and self.status == "مسودة / Draft":
            self.status = "بانتظار الاعتماد / Pending Approval"
        elif not any(approvals):
            self.approved_by = None
            self.approved_on = None
