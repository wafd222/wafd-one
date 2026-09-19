from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


class WAFDIftarSupervisorDailyReport(Document):
    def validate(self):
        if not self.daily_operation or not self.supervisor_plan:
            return
        duplicate = frappe.db.exists("WAFD Iftar Supervisor Daily Report", {
            "daily_operation": self.daily_operation, "supervisor_plan": self.supervisor_plan,
            "name": ["!=", self.name or ""],
        })
        if duplicate:
            frappe.throw("يوجد تقرير يومي لهذا المشرف في نفس التشغيل / A daily report already exists for this supervisor")
        operation = frappe.get_doc("WAFD Iftar Daily Operation", self.daily_operation)
        plan = frappe.get_doc("WAFD Iftar Supervisor Plan", self.supervisor_plan)
        if operation.project != self.project or plan.project != self.project:
            frappe.throw("التشغيل وخطة المشرف يجب أن يتبعا المشروع نفسه / Operation and supervisor plan must belong to the same project")
        self.operation_date = operation.operation_date
        self.supervisor_user = plan.supervisor_user
        self.supervisor_name = plan.supervisor_name
        self.supervisor_mobile = plan.supervisor_mobile
        self.planned_meals = cint(plan.assigned_meals)
        self.cartons = (self.planned_meals + 24) // 25 if self.planned_meals else 0
        planned_by_owner = sum(cint(row.planned_meals) for row in (self.table_owners or []))
        if planned_by_owner != self.planned_meals:
            frappe.throw("إجمالي خطة أصحاب السفر يجب أن يساوي الكمية المسندة / Table-owner plan must equal assigned meals")
        for photo in self.daily_photos or []:
            photo.uploaded_by = photo.uploaded_by or frappe.session.user
            photo.uploaded_at = photo.uploaded_at or now_datetime()
        values = [self.received_meals, self.distributed_meals, self.surplus_meals, self.preservation_meals, self.waste_meals]
        if any(cint(value) < 0 for value in values):
            frappe.throw("لا يمكن إدخال كميات سالبة / Negative quantities are not allowed")
        if any(cint(self.get(field)) < 0 for field in ("tablecloths", "bread_bags", "waste_bags", "gloves", "shoe_covers")):
            frappe.throw("لا يمكن إدخال عهدة سالبة / Operating supplies cannot be negative")
        if cint(self.received_meals) > self.planned_meals:
            frappe.throw("الكمية المستلمة تتجاوز الكمية المسندة / Received quantity exceeds assigned meals")
        closed = cint(self.distributed_meals) + cint(self.surplus_meals) + cint(self.preservation_meals) + cint(self.waste_meals)
        if closed > cint(self.received_meals):
            frappe.throw("إجمالي التوزيع والفائض وحفظ النعمة والتالف يتجاوز المستلم / Closeout quantities exceed received meals")
        if cint(self.report_submitted):
            if cint(self.received_meals) <= 0:
                frappe.throw("يجب اعتماد استلام المشرف للوجبات أولاً / Supervisor receipt must be approved first")
            unmarked = [row.assistant_name for row in (self.assistants_attendance or []) if row.attendance_status == "لم يسجل / Not Marked"]
            if unmarked:
                frappe.throw("سجل حضور أو غياب جميع المساعدين قبل إرسال التقرير / Mark every assistant present or absent")
            absent_without_reason = [row.assistant_name for row in (self.assistants_attendance or []) if row.attendance_status == "غائب / Absent" and not (row.absence_reason or "").strip()]
            if absent_without_reason:
                frappe.throw("أدخل سبب غياب كل مساعد / Enter the absence reason for every absent assistant")
            if not all(cint(value) for value in (self.tables_spread_completed, self.distribution_completed, self.cleanup_completed)):
                frappe.throw("أكمل فرش السفر والتوزيع ورفع السفر قبل إرسال التقرير / Complete field work before submitting the report")
            if closed != cint(self.received_meals):
                frappe.throw("يجب تسوية كامل الكمية المستلمة قبل إرسال التقرير / Reconcile all received meals before submitting")
            owner_delivered = sum(cint(row.delivered_meals) for row in (self.table_owners or []))
            if owner_delivered != cint(self.distributed_meals):
                frappe.throw("إجمالي تسليم أصحاب السفر يجب أن يساوي الكمية الموزعة / Table-owner deliveries must equal distributed meals")
            incomplete_owner_evidence = [row.table_owner_name for row in (self.table_owners or []) if not row.owner_confirmed or not row.delivery_photo or not row.recipient_signature]
            if incomplete_owner_evidence:
                frappe.throw("أكمل صورة وتوقيع تسليم أصحاب السفر / Complete every table-owner photo and signature")
            if cint(self.preservation_meals) and (not self.preservation_receipt_photo or not self.preservation_receiver_signature):
                frappe.throw("أرفق صورة وتوقيع استلام جمعية حفظ النعمة / Attach preservation receipt photo and signature")
            if not self.distribution_photo or not self.closeout_photo:
                frappe.throw("صورتا التوزيع ورفع السفر مطلوبتان / Distribution and closeout photos are required")
            if not any(row.photo for row in (self.daily_photos or [])) and not self.distribution_photo and not (self.media_links or "").strip():
                frappe.throw("أرفق صورة واحدة على الأقل أو رابط توثيق / Attach at least one photo or evidence link")
            if not self.submitted_at:
                self.submitted_at = now_datetime()
        roles = set(frappe.get_roles(frappe.session.user))
        if "WAFD Iftar Supervisor" in roles and not roles.intersection({"System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager"}):
            old = self.get_doc_before_save() if not self.is_new() else None
            for field in (
                "received_meals", "received_at", "tablecloths", "bread_bags",
                "waste_bags", "gloves", "shoe_covers", "site_manager_user",
                "handover_photo",
            ):
                self.set(field, old.get(field) if old else self.get(field))
            self.manager_approved = cint(old.manager_approved) if old else 0
            self.approved_by = old.approved_by if old else None
            self.approved_at = old.approved_at if old else None
            self.manager_notes = old.manager_notes if old else None

    def before_save(self):
        if not self.is_new() and frappe.session.user not in ("Administrator",):
            old = self.get_doc_before_save()
            if old and cint(old.manager_approved) and "System Manager" not in frappe.get_roles():
                frappe.throw("التقرير معتمد ولا يمكن للمشرف تعديله / Approved report cannot be edited")
            roles = set(frappe.get_roles(frappe.session.user))
            if old and "WAFD Iftar Site Manager" in roles and not roles.intersection(
                {"System Manager", "WAFD Operations Manager", "WAFD Project Manager"}
            ):
                protected = (
                    "distributed_meals", "surplus_meals", "preservation_meals", "waste_meals",
                    "tables_spread_completed", "distribution_completed", "cleanup_completed",
                    "report_submitted", "submitted_at", "media_links",
                    "submitted_by", "distribution_photo", "closeout_photo",
                    "closeout_at", "preservation_receipt_photo", "preservation_receiver_signature", "supervisor_notes",
                )
                if any(self.get(field) != old.get(field) for field in protected):
                    frappe.throw("مدير الموقع يعتمد التقرير ولا يغير بيانات المشرف / Site manager cannot alter supervisor report data")
                for childfield in ("table_owners", "assistants_attendance", "daily_photos"):
                    before = [row.as_dict(no_nulls=True) for row in (old.get(childfield) or [])]
                    after = [row.as_dict(no_nulls=True) for row in (self.get(childfield) or [])]
                    if before != after:
                        frappe.throw("مدير الموقع لا يغير تفاصيل أو صور تقرير المشرف / Site manager cannot alter supervisor details or photos")
