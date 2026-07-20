import frappe


def execute():
    """Compatibility patch retained for already published patch history.

    The previous implementation reloaded governance DocTypes a second time.
    Schema synchronization already handles that, so this patch now only clears
    caches and remains safely idempotent.
    """
    frappe.clear_cache()
