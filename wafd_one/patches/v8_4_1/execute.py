import frappe


def execute():
    """Refresh corrected daily-planning metadata and the standard workspace."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_daily_meal_plan_item", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_daily_meal_plan", force=True)
    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=True)
    frappe.clear_cache(doctype="WAFD Daily Meal Plan")
    frappe.clear_cache(doctype="WAFD Daily Meal Plan Item")
