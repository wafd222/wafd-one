import frappe


def execute():
    for doctype in (
        "WAFD Source Warehouse Row",
        "WAFD Material Allocation",
        "WAFD Daily Meal Plan",
        "WAFD Production Batch",
        "WAFD Catering Project",
        "WAFD Kitchen",
    ):
        frappe.reload_doc("wafd_one", "doctype", frappe.scrub(doctype), force=True)

    # Safely copy each legacy single source into the new multi-source table.
    legacy_fields = {
        "WAFD Daily Meal Plan": "source_warehouse",
        "WAFD Production Batch": "source_warehouse",
        "WAFD Catering Project": "default_source_warehouse",
        "WAFD Kitchen": "default_warehouse",
    }
    for dt, legacy_field in legacy_fields.items():
        if not frappe.db.table_exists(dt):
            continue
        for name, warehouse in frappe.get_all(dt, filters={legacy_field: ["is", "set"]}, fields=["name", legacy_field], as_list=True):
            exists = frappe.db.exists("WAFD Source Warehouse Row", {
                "parenttype": dt, "parent": name, "parentfield": "source_warehouses", "warehouse": warehouse,
            })
            if warehouse and not exists:
                frappe.get_doc({
                    "doctype": "WAFD Source Warehouse Row", "parenttype": dt, "parent": name,
                    "parentfield": "source_warehouses", "warehouse": warehouse,
                    "priority": 1, "is_default": 1,
                }).insert(ignore_permissions=True)
