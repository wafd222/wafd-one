from __future__ import annotations

import frappe


def execute():
    """Non-destructive RC103 setup.

    Keep existing operational records and prices. Only correct the default
    Iftar naming series for future documents and clear metadata caches.
    """
    if frappe.db.exists("DocType", "WAFD Iftar Project"):
        # Existing document names are intentionally preserved.
        frappe.db.set_value(
            "DocField",
            {"parent": "WAFD Iftar Project", "fieldname": "naming_series"},
            {"options": "WAFD-IFTAR-#####", "default": "WAFD-IFTAR-#####"},
            update_modified=False,
        )
    frappe.clear_cache(doctype="WAFD Iftar Project")
