import frappe


def execute():
    """Keep audit history without making it a database deletion dependency."""
    if not frappe.db.exists("DocType", "WAFD Audit Event"):
        return
    # The source JSON changes reference_name from Dynamic Link to Data. Updating
    # metadata explicitly makes the migration deterministic on existing sites.
    frappe.db.set_value(
        "DocField",
        {"parent": "WAFD Audit Event", "fieldname": "reference_name"},
        {"fieldtype": "Data", "options": None},
        update_modified=False,
    )
    frappe.clear_cache(doctype="WAFD Audit Event")
