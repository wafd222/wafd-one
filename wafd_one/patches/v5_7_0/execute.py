import frappe


def execute():
    frappe.db.set_single_value("WAFD Operations Settings", "daily_production_capacity", frappe.db.get_single_value("WAFD Operations Settings", "daily_production_capacity") or 10000)
    frappe.db.set_single_value("WAFD Operations Settings", "capacity_warning_percent", frappe.db.get_single_value("WAFD Operations Settings", "capacity_warning_percent") or 85)
    frappe.db.set_single_value("WAFD Operations Settings", "default_production_lead_hours", frappe.db.get_single_value("WAFD Operations Settings", "default_production_lead_hours") or 8)
    frappe.db.set_single_value("WAFD Operations Settings", "shortage_warning_hours", frappe.db.get_single_value("WAFD Operations Settings", "shortage_warning_hours") or 24)
    frappe.db.set_single_value("WAFD Operations Settings", "auto_generate_alerts", 1)

    for name in frappe.get_all("WAFD Production Batch", pluck="name"):
        doc = frappe.get_doc("WAFD Production Batch", name)
        try:
            doc._validate_schedule()
            doc.db_set("service_deadline", doc.service_deadline, update_modified=False)
            doc.db_set("schedule_status", doc.schedule_status, update_modified=False)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"WAFD v5.7 schedule migration: {name}")
