import frappe


def execute():
    """Reload the corrected hotel undertaking print format only."""
    frappe.reload_doc("wafd_one", "print_format", "wafd_hotel_undertaking", force=True)
    if frappe.db.exists("DocType", "WAFD Print Settings"):
        settings = frappe.get_single("WAFD Print Settings")
        if settings.get("show_company_details"):
            settings.show_company_details = 0
            settings.save(ignore_permissions=True)
