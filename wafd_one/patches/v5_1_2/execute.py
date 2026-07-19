import frappe


def execute():
    # Reload the standard undertaking print format so the refined header/footer
    # is applied on existing sites without touching user-entered undertaking data.
    frappe.reload_doc("wafd_one", "print_format", "wafd_hotel_undertaking", force=True)
