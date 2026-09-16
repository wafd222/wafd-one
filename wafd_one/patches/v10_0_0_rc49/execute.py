import frappe


def execute():
    """Remove stale overrides for the standard advance_percent field."""
    if frappe.db.exists("DocType", "Custom Field"):
        for name in frappe.get_all(
            "Custom Field",
            filters={"dt": "WAFD Contract", "fieldname": "advance_percent"},
            pluck="name",
        ):
            frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)

    if frappe.db.exists("DocType", "Property Setter"):
        for name in frappe.get_all(
            "Property Setter",
            filters={"doc_type": "WAFD Contract", "field_name": "advance_percent"},
            pluck="name",
        ):
            frappe.delete_doc("Property Setter", name, ignore_permissions=True, force=True)

    frappe.clear_cache(doctype="WAFD Contract")
