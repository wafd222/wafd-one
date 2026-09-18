from collections import defaultdict

import frappe
from frappe.utils import cint, flt


def execute():
    """Safely consolidate existing operational meal rows into daily plans.

    WAFD Meal Plan is retained as the internal compatibility layer. No records
    are deleted, renamed or detached from downstream production documents.
    """
    projects = frappe.get_all("WAFD Catering Project", pluck="name")
    for project_name in projects:
        try:
            _consolidate_project(project_name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"WAFD v8.4 daily plan migration: {project_name}")


def _consolidate_project(project_name):
    project = frappe.get_doc("WAFD Catering Project", project_name)
    rows = frappe.get_all(
        "WAFD Meal Plan",
        filters={"project": project_name, "status": ["!=", "ملغي / Cancelled"]},
        fields=["name", "hotel", "service_date", "meal_type", "quantity", "service_time",
                "menu_name", "recipe", "unit_price", "estimated_unit_cost"],
        order_by="service_date asc, hotel asc, service_time asc",
    )
    groups = defaultdict(list)
    for row in rows:
        if row.hotel and row.service_date:
            groups[(row.hotel, str(row.service_date))].append(row)

    for (hotel, service_date), meal_rows in groups.items():
        name = frappe.db.get_value("WAFD Daily Meal Plan", {
            "project": project_name, "hotel": hotel, "service_date": service_date
        }, "name")
        if name:
            daily = frappe.get_doc("WAFD Daily Meal Plan", name)
            if daily.status in ("قيد الإنتاج / In Production", "جاهزة / Ready", "تم التسليم / Delivered"):
                continue
            existing_links = {x.meal_plan for x in daily.meals if x.meal_plan}
        else:
            daily = frappe.new_doc("WAFD Daily Meal Plan")
            daily.project = project_name
            daily.hotel = hotel
            daily.service_date = service_date
            daily.kitchen = project.default_kitchen
            daily.source_warehouse = project.default_source_warehouse
            daily.plan_title = f"{project.project_name} - {hotel} - {service_date}"
            existing_links = set()

        for row in meal_rows:
            if row.name in existing_links:
                continue
            # Avoid duplicate meal types while preserving the existing daily row.
            if any(x.meal_type == row.meal_type for x in daily.meals):
                continue
            daily.append("meals", {
                "meal_type": row.meal_type,
                "quantity": cint(row.quantity),
                "service_time": row.service_time,
                "menu_name": row.menu_name,
                "recipe": row.recipe,
                "unit_price": flt(row.unit_price),
                "estimated_unit_cost": flt(row.estimated_unit_cost),
                "meal_plan": row.name,
            })
        if daily.meals:
            daily.save(ignore_permissions=True)
