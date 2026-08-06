from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, nowdate


@frappe.whitelist()
def create_project(data):
    if isinstance(data, str):
        data = frappe.parse_json(data)
    required = [
        "project_title", "contracting_entity", "distribution_site",
        "start_date", "end_date", "daily_meals", "sale_price_per_meal",
    ]
    missing = [field for field in required if not data.get(field)]
    if missing:
        frappe.throw(_("الحقول المطلوبة غير مكتملة: {0}").format(", ".join(missing)))
    allowed = required + [
        "contracting_entity_type", "site_details", "meal_template", "include_zamzam"
    ]
    doc = frappe.get_doc({
        "doctype": "WAFD Iftar Project",
        **{key: value for key, value in data.items() if key in allowed},
    })
    doc.insert()
    generate_daily_operations(doc.name, ignore_permissions=True)
    return {"name": doc.name, "route": f"/app/wafd-iftar-project/{doc.name}"}


@frappe.whitelist()
def generate_daily_operations(project_name, ignore_permissions=False):
    project = frappe.get_doc("WAFD Iftar Project", project_name)
    if not ignore_permissions:
        project.check_permission("write")

    if not project.start_date or not project.end_date or cint(project.daily_meals) <= 0:
        return {"created": 0, "updated": 0, "removed": 0}

    start = getdate(project.start_date)
    end = getdate(project.end_date)
    expected_dates = set()
    day = start
    while day <= end:
        expected_dates.add(day)
        day = add_days(day, 1)

    existing = frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": project.name},
        fields=[
            "name", "operation_date", "status", "produced_meals", "packaged_meals",
            "loaded_meals", "delivered_meals", "received_meals", "docstatus",
        ],
    )
    by_date = {getdate(row.operation_date): row for row in existing}
    created = updated = removed = 0

    for operation_date in sorted(expected_dates):
        row = by_date.get(operation_date)
        if not row:
            frappe.get_doc({
                "doctype": "WAFD Iftar Daily Operation",
                "project": project.name,
                "operation_date": operation_date,
                "planned_meals": cint(project.daily_meals),
                "status": "مخطط / Planned",
                "produced_meals": 0,
                "packaged_meals": 0,
                "loaded_meals": 0,
                "delivered_meals": 0,
                "received_meals": 0,
                "surplus_meals": 0,
                "waste_meals": 0,
                "preservation_society_quantity": 0,
            }).insert(ignore_permissions=True)
            created += 1
        elif cint(frappe.db.get_value("WAFD Iftar Daily Operation", row.name, "planned_meals")) != cint(project.daily_meals):
            frappe.db.set_value(
                "WAFD Iftar Daily Operation", row.name, "planned_meals", cint(project.daily_meals),
                update_modified=False,
            )
            updated += 1

    # Remove only untouched draft rows outside the new project range. Never
    # delete operational history containing entered quantities.
    for operation_date, row in by_date.items():
        if operation_date in expected_dates:
            continue
        has_activity = any(cint(row.get(field)) for field in [
            "produced_meals", "packaged_meals", "loaded_meals", "delivered_meals", "received_meals"
        ])
        if not has_activity and cint(row.docstatus) == 0:
            frappe.delete_doc("WAFD Iftar Daily Operation", row.name, ignore_permissions=True)
            removed += 1

    return {"created": created, "updated": updated, "removed": removed}


@frappe.whitelist()
def get_project_operations(project_name):
    frappe.has_permission("WAFD Iftar Project", "read", project_name, throw=True)
    return frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": project_name},
        fields=[
            "name", "operation_date", "status", "planned_meals", "produced_meals",
            "packaged_meals", "loaded_meals", "delivered_meals", "received_meals",
            "surplus_meals", "waste_meals", "completion_percent",
        ],
        order_by="operation_date asc",
    )


@frappe.whitelist()
def get_dashboard(date=None):
    operation_date = getdate(date or nowdate())

    def fetch_rows(target_date):
        data = frappe.get_all(
            "WAFD Iftar Daily Operation",
            filters={"operation_date": target_date},
            fields=[
                "name", "project", "status", "planned_meals", "produced_meals",
                "packaged_meals", "loaded_meals", "delivered_meals", "received_meals",
                "completion_percent",
            ],
            order_by="modified desc",
        )
        if data:
            project_names = list({row.project for row in data if row.project})
            project_meta = {
                row.name: row for row in frappe.get_all(
                    "WAFD Iftar Project",
                    filters={"name": ["in", project_names]},
                    fields=["name", "project_title", "distribution_site", "contracting_entity"],
                )
            }
            for row in data:
                meta = project_meta.get(row.project)
                row.project_title = meta.project_title if meta else row.project
                row.distribution_site = meta.distribution_site if meta else ""
                row.contracting_entity = meta.contracting_entity if meta else ""
        return data

    rows = fetch_rows(operation_date)

    # Self-healing: generate missing daily rows for projects covering selected date.
    if not rows:
        projects = frappe.get_all(
            "WAFD Iftar Project",
            filters={
                "start_date": ["<=", operation_date],
                "end_date": [">=", operation_date],
                "docstatus": ["<", 2],
            },
            pluck="name",
        )
        for project_name in projects:
            generate_daily_operations(project_name, ignore_permissions=True)
        if projects:
            rows = fetch_rows(operation_date)

    # When today has no work, suggest the nearest available operation date so
    # the operations page does not appear empty while a project is upcoming.
    suggested_date = None
    if not rows:
        nearest = frappe.db.sql(
            """
            select operation_date
            from `tabWAFD Iftar Daily Operation`
            where docstatus < 2
            order by abs(datediff(operation_date, %s)), operation_date asc
            limit 1
            """,
            operation_date,
            as_dict=True,
        )
        if nearest:
            suggested_date = nearest[0].operation_date

    keys = [
        "planned_meals", "produced_meals", "packaged_meals", "loaded_meals",
        "delivered_meals", "received_meals",
    ]
    sums = {key: sum(cint(row.get(key)) for row in rows) for key in keys}
    sums["remaining_meals"] = max(0, sums["planned_meals"] - sums["received_meals"])
    sums["project_count"] = len({row.project for row in rows})
    sums["completion_percent"] = round(
        sums["received_meals"] / sums["planned_meals"] * 100, 1
    ) if sums["planned_meals"] else 0
    return {
        "summary": sums,
        "rows": rows,
        "selected_date": operation_date,
        "suggested_date": suggested_date,
    }

