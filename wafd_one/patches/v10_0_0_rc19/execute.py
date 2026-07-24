import frappe


def execute():
    """Refresh derived production quantities after the RC19 schema update.

    The patch is deliberately idempotent: it only recalculates derived fields
    on existing production batches and can be run safely more than once.
    """
    if not frappe.db.exists("DocType", "WAFD Production Batch"):
        return

    meta = frappe.get_meta("WAFD Production Batch")
    fieldnames = {field.fieldname for field in meta.fields}
    required = {
        "planned_quantity",
        "produced_quantity",
        "rejected_quantity",
        "remaining_quantity",
        "completion_percent",
    }
    if not required.issubset(fieldnames):
        return

    for name in frappe.get_all("WAFD Production Batch", pluck="name"):
        try:
            values = frappe.db.get_value(
                "WAFD Production Batch",
                name,
                ["planned_quantity", "produced_quantity", "rejected_quantity"],
                as_dict=True,
            ) or {}
            planned = frappe.utils.flt(values.get("planned_quantity"))
            produced = frappe.utils.flt(values.get("produced_quantity"))
            rejected = frappe.utils.flt(values.get("rejected_quantity"))

            frappe.db.set_value(
                "WAFD Production Batch",
                name,
                {
                    "remaining_quantity": max(planned - produced - rejected, 0),
                    "completion_percent": (produced / planned * 100) if planned else 0,
                },
                update_modified=False,
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"RC19 production refresh failed: {name}",
            )
