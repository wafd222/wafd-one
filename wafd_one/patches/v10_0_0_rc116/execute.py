import frappe


def execute():
    # Ensure updated print formats and operations page are reloaded on migration.
    for doctype, name in (
        ("Print Format", "إفطار صائم — تسليم واستلام يومي"),
        ("Print Format", "WAFD Iftar Project Summary"),
    ):
        if frappe.db.exists(doctype, name):
            frappe.clear_cache(doctype=doctype)
