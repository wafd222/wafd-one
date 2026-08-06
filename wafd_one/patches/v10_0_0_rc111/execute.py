import frappe
from frappe.model.naming import make_autoname


def execute():
    # Correct the naming-series syntax for all future Iftar projects.
    if frappe.db.exists("DocType", "WAFD Iftar Project"):
        frappe.db.set_value(
            "DocField",
            {"parent": "WAFD Iftar Project", "fieldname": "naming_series"},
            {"options": "WAFD-IFTAR-.#####", "default": "WAFD-IFTAR-.#####"},
            update_modified=False,
        )

    # Earlier releases created names containing literal # characters. Rename
    # them through Frappe so every Link field is updated safely.
    malformed = frappe.get_all(
        "WAFD Iftar Project",
        filters={"name": ["like", "%#%"]},
        pluck="name",
        order_by="creation asc",
    )
    for old_name in malformed:
        new_name = make_autoname("WAFD-IFTAR-.#####")
        while frappe.db.exists("WAFD Iftar Project", new_name):
            new_name = make_autoname("WAFD-IFTAR-.#####")
        frappe.rename_doc("WAFD Iftar Project", old_name, new_name, force=True, ignore_permissions=True)

    frappe.clear_cache(doctype="WAFD Iftar Project")
