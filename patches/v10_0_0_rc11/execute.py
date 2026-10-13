import frappe
from frappe.utils import flt


def execute():
    # Normalize all legacy stock balances so production availability reflects
    # actual minus reserved quantities immediately after migration.
    rows = frappe.get_all(
        "WAFD Stock Balance",
        fields=["name", "actual_quantity", "reserved_quantity", "available_quantity"],
    )
    for row in rows:
        available = max(flt(row.actual_quantity) - flt(row.reserved_quantity), 0)
        if abs(flt(row.available_quantity) - available) > 0.000001:
            frappe.db.set_value("WAFD Stock Balance", row.name, "available_quantity", available, update_modified=False)

    # Repair production batches that have a primary warehouse but no child source row.
    batches = frappe.get_all(
        "WAFD Production Batch",
        filters={"source_warehouse": ["is", "set"]},
        fields=["name", "source_warehouse"],
    )
    for row in batches:
        exists = frappe.db.exists(
            "WAFD Source Warehouse Row",
            {"parent": row.name, "parenttype": "WAFD Production Batch", "warehouse": row.source_warehouse},
        )
        if not exists:
            doc = frappe.get_doc("WAFD Production Batch", row.name)
            doc.append("source_warehouses", {"warehouse": row.source_warehouse, "priority": 1, "is_default": 1})
            doc.save(ignore_permissions=True)

    frappe.clear_cache()
