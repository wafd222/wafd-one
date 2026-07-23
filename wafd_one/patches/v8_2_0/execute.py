import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_catering_project", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_meal_plan", force=True)

    # Keep operation counters accurate for projects created before v8.2.
    for project_name in frappe.get_all("WAFD Catering Project", pluck="name"):
        count = frappe.db.count("WAFD Meal Plan", {"project": project_name})
        frappe.db.set_value(
            "WAFD Catering Project",
            project_name,
            "meal_plans_created",
            count,
            update_modified=False,
        )
