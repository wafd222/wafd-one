from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cint


class WAFDIftarSupervisorPlan(Document):
    def validate(self):
        project = frappe.get_doc("WAFD Iftar Project", self.project)
        if self.supervisor_user and frappe.db.exists("WAFD Iftar Supervisor Plan", {
            "project": self.project, "supervisor_user": self.supervisor_user,
            "name": ["!=", self.name or ""],
        }):
            frappe.throw("حساب المشرف مرتبط بخطة أخرى في المشروع نفسه / Supervisor user already has a plan in this project")
        self.distribution_site = project.distribution_site
        self.haram_zone = getattr(project, "haram_zone", None)
        self.table_owners_count = len([r for r in (self.table_owners or []) if r.table_owner_name])
        self.assistants_count = len([r for r in (self.assistants or []) if r.assistant_name and cint(r.active)])
        self.assigned_meals = sum(cint(r.meal_quantity) for r in (self.table_owners or []))
        if self.assigned_meals > cint(project.daily_meals):
            frappe.throw("إجمالي وجبات المشرف لا يمكن أن يتجاوز الوجبات اليومية للمشروع / Supervisor meals exceed project daily meals")

        sibling_meals = sum(
            cint(x.assigned_meals)
            for x in frappe.get_all(
                "WAFD Iftar Supervisor Plan",
                filters={"project": self.project, "name": ["!=", self.name or ""]},
                fields=["assigned_meals"],
            )
        )
        if sibling_meals + cint(self.assigned_meals) > cint(project.daily_meals):
            frappe.throw(
                "إجمالي الوجبات الموزعة على جميع المشرفين يتجاوز الوجبات اليومية للمشروع / "
                "Total meals assigned across supervisors exceed project daily meals"
            )

    def on_update(self):
        self._sync_project_counters()
        self._sync_project_distribution()
        self._seed_daily_assistants()

    def on_trash(self):
        self._sync_project_counters(exclude_self=True)
        self._sync_project_distribution(exclude_self=True)

    def _sync_project_counters(self, exclude_self=False):
        filters = {"project": self.project}
        if exclude_self and self.name:
            filters["name"] = ["!=", self.name]
        rows = frappe.get_all(
            "WAFD Iftar Supervisor Plan",
            filters=filters,
            fields=["assistants_count"],
        )
        frappe.db.set_value(
            "WAFD Iftar Project",
            self.project,
            {
                "supervisors": len(rows),
                "assistants": sum(cint(r.assistants_count) for r in rows),
            },
            update_modified=False,
        )

    def _sync_project_distribution(self, exclude_self=False):
        """Keep the existing distribution/carton workflow fed from the one-time supervisor plans."""
        filters = {"project": self.project}
        if exclude_self and self.name:
            filters["name"] = ["!=", self.name]
        plan_names = frappe.get_all("WAFD Iftar Supervisor Plan", filters=filters, pluck="name", order_by="creation asc")
        project = frappe.get_doc("WAFD Iftar Project", self.project)
        project.set("distribution_recipients", [])
        for plan_name in plan_names:
            plan = frappe.get_doc("WAFD Iftar Supervisor Plan", plan_name)
            for owner in plan.table_owners or []:
                project.append("distribution_recipients", {
                    "supervisor_name": plan.supervisor_name,
                    "supervisor_mobile": plan.supervisor_mobile,
                    "table_owner_name": owner.table_owner_name,
                    "mobile_no": owner.mobile_no,
                    "distribution_point": owner.distribution_point,
                    "delivery_location": owner.delivery_location,
                    "meal_quantity": owner.meal_quantity,
                    "notes": owner.notes,
                })
        project.save(ignore_permissions=True)

    def _seed_daily_assistants(self):
        """Add the registered monthly team to every day without erasing attendance history."""
        assistants = []
        for plan_name in frappe.get_all("WAFD Iftar Supervisor Plan", filters={"project": self.project}, pluck="name"):
            plan = frappe.get_doc("WAFD Iftar Supervisor Plan", plan_name)
            assistants.extend(
                (row.assistant_name, row.mobile_no) for row in (plan.assistants or [])
                if row.assistant_name and cint(row.active)
            )
        unique = dict(assistants)
        if not unique:
            return
        for operation in frappe.get_all("WAFD Iftar Daily Operation", filters={"project": self.project}, pluck="name"):
            existing = set(frappe.get_all(
                "WAFD Iftar Assistant Attendance",
                filters={"parent": operation, "parenttype": "WAFD Iftar Daily Operation", "parentfield": "assistants_attendance"},
                pluck="assistant_name",
            ))
            idx = frappe.db.count("WAFD Iftar Assistant Attendance", {
                "parent": operation, "parenttype": "WAFD Iftar Daily Operation", "parentfield": "assistants_attendance",
            })
            for name, mobile in unique.items():
                if name in existing:
                    continue
                idx += 1
                frappe.get_doc({
                    "doctype": "WAFD Iftar Assistant Attendance", "parent": operation,
                    "parenttype": "WAFD Iftar Daily Operation", "parentfield": "assistants_attendance", "idx": idx,
                    "assistant_name": name, "mobile_no": mobile, "attendance_status": "لم يسجل / Not Marked",
                }).db_insert()
