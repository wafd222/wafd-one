"""RC148 — repair legacy empty recipes and install the Hajj cuisine reference."""
import frappe


def execute():
    if not frappe.db.exists("DocType", "WAFD Recipe"):
        return

    from wafd_one.master_data import load_reference_master_data
    from wafd_one.rc148_recipe_catalog import SOURCE_METADATA
    load_reference_master_data()

    # Enrich trusted dish-name provenance without changing user recipes or quantities.
    for recipe_name, metadata in SOURCE_METADATA.items():
        if not frappe.db.exists("WAFD Recipe", recipe_name):
            continue
        current = frappe.db.get_value(
            "WAFD Recipe", recipe_name,
            ["source_authority", "source_url", "verification_status", "last_verified_on", "source_notes"],
            as_dict=True,
        ) or {}
        updates = {k: v for k, v in metadata.items() if v and not current.get(k)}
        if updates:
            frappe.db.set_value("WAFD Recipe", recipe_name, updates, update_modified=False)

    # Legacy/custom recipes that are still empty are retained for audit/history,
    # but cannot remain Active because production would fail later.
    active = "نشطة / Active"
    inactive = "غير نشطة / Inactive"
    empty_recipes = frappe.db.sql(
        """
        SELECT r.name
        FROM `tabWAFD Recipe` r
        LEFT JOIN `tabWAFD Recipe Item` i
          ON i.parent = r.name
         AND i.parenttype = 'WAFD Recipe'
         AND i.parentfield = 'items'
         AND COALESCE(i.ingredient, '') != ''
         AND COALESCE(i.quantity, 0) > 0
        WHERE r.status = %s
        GROUP BY r.name
        HAVING COUNT(i.name) = 0
        """,
        (active,),
        as_dict=True,
    )
    for row in empty_recipes:
        frappe.db.set_value(
            "WAFD Recipe",
            row.name,
            {
                "status": inactive,
                "source_notes": "RC148: تم تعطيل الوصفة تلقائياً لأنها لا تحتوي على مكونات تشغيلية. أكمل المكونات ثم أعد تنشيطها / Automatically disabled because it has no operational ingredients.",
            },
            update_modified=False,
        )

    frappe.clear_cache(doctype="WAFD Recipe")
    frappe.clear_cache(doctype="WAFD Contract")
    frappe.clear_cache(doctype="WAFD Catering Project")
