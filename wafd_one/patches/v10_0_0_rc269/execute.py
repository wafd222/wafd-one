import frappe


def execute():
    """Refresh employee pages after unifying the account language."""
    for page in (
        "wafd_role_home",
        "wafd_storekeeper_home",
        "wafd_cleaning_home",
        "wafd_driver_trips",
        "wafd_employee_team",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="Page")
