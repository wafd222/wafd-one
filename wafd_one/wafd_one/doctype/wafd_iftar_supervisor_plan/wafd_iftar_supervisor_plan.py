from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cint


class WAFDIftarSupervisorPlan(Document):
    def validate(self):
        project = frappe.get_doc("WAFD Iftar Project", self.project)
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
                filters={"project": self.project, "active": 1, "name": ["!=", self.name or ""]},
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

    def on_trash(self):
        self._sync_project_counters(exclude_self=True)
        self._sync_project_distribution(exclude_self=True)

    def _sync_project_counters(self, exclude_self=False):
        filters = {"project": self.project, "active": 1}
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
        """Keep the legacy project distribution table synchronized without saving the parent.

        `WAFD Iftar Distribution Recipient` is an ``istable`` child DocType.  Frappe v16 can
        still run a standalone permission check for nested child writes while a non-System
        Manager saves the supervisor plan, even when the parent ``project.save`` receives
        ``ignore_permissions=True``.  That produced the misleading "choose the correct parent
        DocType / no permission" message seen on mobile.

        The supervisor plan is already permission-validated before this hook executes, so we
        rebuild only the project's child rows directly at DB level.  This keeps the existing
        carton/distribution workflows fed while never treating the child table as a standalone
        user-editable document.
        """
        filters = {"project": self.project, "active": 1}
        if exclude_self and self.name:
            filters["name"] = ["!=", self.name]
        plan_names = frappe.get_all(
            "WAFD Iftar Supervisor Plan",
            filters=filters,
            pluck="name",
            order_by="creation asc",
        )

        child_filters = {
            "parent": self.project,
            "parenttype": "WAFD Iftar Project",
            "parentfield": "distribution_recipients",
        }
        frappe.db.delete("WAFD Iftar Distribution Recipient", child_filters)

        idx = 0
        for plan_name in plan_names:
            plan = frappe.get_doc("WAFD Iftar Supervisor Plan", plan_name)
            for owner in plan.table_owners or []:
                idx += 1
                row = frappe.get_doc({
                    "doctype": "WAFD Iftar Distribution Recipient",
                    "parent": self.project,
                    "parenttype": "WAFD Iftar Project",
                    "parentfield": "distribution_recipients",
                    "idx": idx,
                    "supervisor_name": plan.supervisor_name,
                    "supervisor_mobile": plan.supervisor_mobile,
                    "table_owner_name": owner.table_owner_name,
                    "mobile_no": owner.mobile_no,
                    "distribution_point": owner.distribution_point,
                    "delivery_location": owner.delivery_location,
                    "meal_quantity": owner.meal_quantity,
                    "notes": owner.notes,
                })
                row.db_insert()

        # Touch only the project timestamp so open forms refresh, without invoking project
        # validation/permission logic or re-saving unrelated project fields.
        frappe.db.set_value(
            "WAFD Iftar Project",
            self.project,
            "modified",
            frappe.utils.now(),
            update_modified=False,
        )
