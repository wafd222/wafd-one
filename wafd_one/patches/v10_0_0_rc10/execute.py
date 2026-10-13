import frappe


def execute():
    """Repair stale workflow links without creating or approving transactions."""
    # Link packaging records back to batches where the relationship is clear.
    rows = frappe.db.sql(
        """select pr.name packaging, pr.production_batch batch
           from `tabWAFD Packaging Record` pr
           inner join `tabWAFD Production Batch` pb on pb.name=pr.production_batch
           where ifnull(pb.packaging_record, '')=''""",
        as_dict=True,
    )
    for row in rows:
        frappe.db.set_value("WAFD Production Batch", row.batch, "packaging_record", row.packaging, update_modified=False)

    # Normalize daily-plan production counts used by dashboards.
    plans = frappe.get_all("WAFD Daily Meal Plan", pluck="name")
    for name in plans:
        count = frappe.db.count("WAFD Production Batch", {"daily_plan": name})
        frappe.db.set_value("WAFD Daily Meal Plan", name, "production_batch_count", count, update_modified=False)
