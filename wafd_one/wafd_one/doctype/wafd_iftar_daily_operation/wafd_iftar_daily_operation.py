from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, now_datetime


class WAFDIftarDailyOperation(Document):
    def validate(self):
        if not self.project or not self.operation_date:
            return

        duplicate = frappe.db.exists(
            "WAFD Iftar Daily Operation",
            {
                "project": self.project,
                "operation_date": self.operation_date,
                "name": ["!=", self.name or ""],
            },
        )
        if duplicate:
            frappe.throw(
                "يوجد سجل تشغيل لهذا المشروع في نفس التاريخ / "
                "A daily operation already exists for this project and date"
            )

        project = frappe.get_doc("WAFD Iftar Project", self.project)
        operation_date = getdate(self.operation_date)
        start_date = getdate(project.start_date) if project.start_date else None
        end_date = getdate(project.end_date) if project.end_date else None
        if start_date and operation_date < start_date or end_date and operation_date > end_date:
            frappe.throw("تاريخ التشغيل خارج مدة المشروع / Operation date is outside the project period")

        self.planned_meals = cint(project.daily_meals)
        self.project_title = project.project_title
        self.distribution_site = project.distribution_site
        self.contracting_entity = project.contracting_entity

        produced = cint(self.produced_meals)
        packaged = cint(self.packaged_meals)
        loaded = cint(self.loaded_meals)
        delivered = cint(self.delivered_meals)
        received = cint(self.received_meals)
        surplus = cint(self.surplus_meals)
        waste = cint(self.waste_meals)
        preservation = cint(self.preservation_society_quantity)

        # Normalize empty numeric fields before any comparison. This prevents
        # NoneType comparison errors when a newly generated day has blank values.
        self.produced_meals = produced
        self.packaged_meals = packaged
        self.loaded_meals = loaded
        self.delivered_meals = delivered
        self.received_meals = received
        self.surplus_meals = surplus
        self.waste_meals = waste
        self.preservation_society_quantity = preservation

        if any(value < 0 for value in [produced, packaged, loaded, delivered, received, surplus, waste, preservation]):
            frappe.throw("لا يمكن إدخال كميات سالبة / Negative quantities are not allowed")
        if produced > self.planned_meals:
            frappe.throw("الإنتاج لا يتجاوز الكمية المخططة / Produced cannot exceed planned meals")
        if packaged > produced:
            frappe.throw("التغليف لا يتجاوز الإنتاج / Packaged cannot exceed produced")
        if loaded > packaged:
            frappe.throw("التحميل لا يتجاوز التغليف / Loaded cannot exceed packaged")
        if delivered > loaded:
            frappe.throw("التسليم لا يتجاوز التحميل / Delivered cannot exceed loaded")
        if received > delivered:
            frappe.throw("الاستلام لا يتجاوز التسليم / Received cannot exceed delivered")
        if surplus + waste + preservation > produced:
            frappe.throw(
                "الفائض والتالف وحفظ النعمة لا تتجاوز الإنتاج / "
                "Closing quantities cannot exceed production"
            )
        # The authority food supervisor samples yogurt, bread and dates on site.
        # Once approved, preserve the timestamp and require all four checks.
        if cint(self.authority_inspection_approved):
            if not self.authority_supervisor_name:
                frappe.throw("اسم مشرف التغذية مطلوب لاعتماد الفحص / Food supervisor name is required")
            if not all(cint(v) for v in [self.yogurt_checked, self.bread_checked, self.dates_checked, self.expiry_checked]):
                frappe.throw("أكمل فحص الزبادي والخبز والتمر وتواريخ الصلاحية / Complete all authority food inspection checks")
            if not self.authority_inspection_time:
                self.authority_inspection_time = now_datetime()
        if delivered and not cint(self.authority_inspection_approved):
            frappe.throw("يجب اعتماد فحص مشرف التغذية قبل التسليم والتوزيع / Authority food inspection must be approved before distribution")

        self.completion_percent = min(100, flt(received) / flt(self.planned_meals) * 100) if self.planned_meals else 0
        if received >= self.planned_meals and self.planned_meals:
            # Keep the day visibly pending until cleanup and the daily authority
            # report are complete; then mark the field operation as closed.
            if cint(self.cleanup_completed) and cint(self.daily_report_sent):
                self.status = "مغلق / Closed"
            else:
                self.status = "مستلم / Received"
            if not self.receipt_time:
                self.receipt_time = now_datetime()
        elif delivered:
            self.status = "في التوزيع / Distributing"
        elif loaded:
            self.status = "جاهز للتحميل / Ready to Load"
        elif produced:
            self.status = "قيد الإنتاج / In Production"
        else:
            self.status = "مخطط / Planned"
