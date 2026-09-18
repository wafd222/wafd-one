from __future__ import annotations

import frappe

PROPHETS_MOSQUE = "المسجد النبوي الشريف / Prophet’s Mosque"
HARAMAIN_ENTITY = "الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي"


def execute():
    # Normalize only editable (non-cancelled) Prophet's Mosque projects so the
    # wizard, operations dashboard and report center all use one location label.
    rows = frappe.get_all(
        "WAFD Iftar Project",
        filters={"project_title": PROPHETS_MOSQUE, "docstatus": ["<", 2]},
        pluck="name",
    )
    for name in rows:
        frappe.db.set_value(
            "WAFD Iftar Project",
            name,
            {
                "distribution_site": PROPHETS_MOSQUE,
                "contracting_entity": HARAMAIN_ENTITY,
                "distribution_type": "مسجد أو حرم / Mosque or Haram",
            },
            update_modified=False,
        )
    frappe.clear_cache(doctype="WAFD Iftar Project")
    frappe.clear_cache(doctype="WAFD Iftar Daily Operation")
    frappe.clear_cache()
