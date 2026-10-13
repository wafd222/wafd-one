import frappe


def execute():
    """Repair stale daily-plan/batch statuses from persisted downstream documents."""
    for batch in frappe.get_all("WAFD Production Batch", fields=["name", "daily_plan"]):
        packaging = frappe.db.get_value("WAFD Packaging Record", {"production_batch": batch.name}, "name")
        loading = frappe.db.get_value("WAFD Loading Record", {"production_batch": batch.name}, "name")
        trip = frappe.db.get_value("WAFD Delivery Trip", {"loading_record": loading, "status": ["!=", "ملغية / Cancelled"]}, ["name", "status"], as_dict=True) if loading else None
        if trip and trip.status == "تم التسليم / Delivered":
            frappe.db.set_value("WAFD Production Batch", batch.name, "status", "مكتمل / Completed", update_modified=False)
        elif loading:
            frappe.db.set_value("WAFD Production Batch", batch.name, "status", "جاهز / Ready", update_modified=False)
        elif packaging:
            frappe.db.set_value("WAFD Production Batch", batch.name, "status", "تغليف / Packaging", update_modified=False)

    for daily in frappe.get_all("WAFD Daily Meal Plan", pluck="name"):
        meal_plans = frappe.get_all("WAFD Production Batch", filters={"daily_plan": daily}, pluck="meal_plan")
        meal_plans = list(dict.fromkeys([x for x in meal_plans if x]))
        if not meal_plans:
            continue
        delivered = frappe.db.count("WAFD Meal Plan", {"name": ["in", meal_plans], "status": "تم التسليم / Delivered"})
        if delivered == len(meal_plans):
            frappe.db.set_value("WAFD Daily Meal Plan", daily, "status", "تم التسليم / Delivered", update_modified=False)
