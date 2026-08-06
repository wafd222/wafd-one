from __future__ import annotations

import frappe
from frappe.model.naming import make_autoname


def execute():
    # Force the clean naming series for all future projects.
    frappe.db.set_value(
        "Property Setter",
        {"doc_type": "WAFD Iftar Project", "field_name": "naming_series", "property": "options"},
        "value",
        "WAFD-IFTAR-.#####",
        update_modified=False,
    ) if frappe.db.exists("Property Setter", {"doc_type": "WAFD Iftar Project", "field_name": "naming_series", "property": "options"}) else None

    # Repair malformed historic identifiers while preserving linked documents.
    bad_names = frappe.get_all("WAFD Iftar Project", filters={"name": ["like", "%#%"]}, pluck="name")
    for old_name in bad_names:
        new_name = make_autoname("WAFD-IFTAR-.#####")
        while frappe.db.exists("WAFD Iftar Project", new_name):
            new_name = make_autoname("WAFD-IFTAR-.#####")
        frappe.rename_doc("WAFD Iftar Project", old_name, new_name, force=True)

    # Existing daily rows from older releases may be submitted. Keep them usable;
    # stage updates are now handled by the controlled server API.
    frappe.clear_cache(doctype="WAFD Iftar Project")
    frappe.clear_cache(doctype="WAFD Iftar Daily Operation")
