"""RC249: repair persisted legacy WAFD ONE launch links."""

import frappe


CANONICAL_HOME = "/app/wafd-role-home"
LEGACY_HOME_LINKS = (
    "/desk/wafd-role-home",
    "/desk/wafd-role-home/",
)


def execute():
    """Move old Desktop Icon records to the canonical Frappe v16 Page route.

    The hook is authoritative for new sessions.  This migration repairs icons
    already materialized by older releases, without touching any other app.
    """
    try:
        if (
            frappe.db.exists("DocType", "Desktop Icon")
            and frappe.db.has_column("Desktop Icon", "link")
        ):
            names = frappe.get_all(
                "Desktop Icon",
                filters={"link": ["in", LEGACY_HOME_LINKS]},
                pluck="name",
            )
            for name in names:
                frappe.db.set_value(
                    "Desktop Icon",
                    name,
                    "link",
                    CANONICAL_HOME,
                    update_modified=False,
                )
    except Exception:
        # Desktop Icon is optional and its schema changed during Frappe v16.
        # A stale cosmetic record must never block the application migration.
        frappe.log_error(frappe.get_traceback(), "WAFD ONE RC249 desktop route repair")

    frappe.clear_cache()
