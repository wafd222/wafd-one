import frappe


def _first_active_warehouse():
    return frappe.db.get_value(
        "WAFD Warehouse",
        {"status": "نشط / Active"},
        "name",
        order_by="creation asc",
    )


def execute():
    """Remove blank source rows and establish safe operational defaults."""
    fallback = _first_active_warehouse()

    for doctype in ("WAFD Catering Project", "WAFD Kitchen"):
        for name in frappe.get_all(doctype, pluck="name"):
            doc = frappe.get_doc(doctype, name)
            rows = [row for row in (getattr(doc, "source_warehouses", []) or []) if row.warehouse]
            changed = len(rows) != len(getattr(doc, "source_warehouses", []) or [])
            if changed:
                doc.set("source_warehouses", rows)

            default_field = "default_source_warehouse" if doctype == "WAFD Catering Project" else "default_warehouse"
            default_warehouse = getattr(doc, default_field, None)
            if not default_warehouse and rows:
                setattr(doc, default_field, rows[0].warehouse)
                default_warehouse = rows[0].warehouse
                changed = True
            if not default_warehouse and fallback:
                setattr(doc, default_field, fallback)
                doc.append("source_warehouses", {
                    "warehouse": fallback,
                    "priority": 1,
                    "is_default": 1,
                })
                changed = True

            if changed:
                doc.flags.ignore_validate_update_after_submit = True
                doc.save(ignore_permissions=True)

    # Existing draft plans may contain a UI-created blank child row. Remove it;
    # a valid source is restored from project/kitchen/fallback during validation.
    for name in frappe.get_all("WAFD Daily Meal Plan", filters={"docstatus": 0}, pluck="name"):
        doc = frappe.get_doc("WAFD Daily Meal Plan", name)
        rows = [row for row in (doc.source_warehouses or []) if row.warehouse]
        if len(rows) != len(doc.source_warehouses or []):
            doc.set("source_warehouses", rows)
            doc.save(ignore_permissions=True)

    frappe.clear_cache(doctype="WAFD Catering Project")
    frappe.clear_cache(doctype="WAFD Kitchen")
    frappe.clear_cache(doctype="WAFD Daily Meal Plan")
