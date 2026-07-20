import frappe

from wafd_one.setup import ensure_roles


def execute():
    """Initialize governance data after schema synchronization.

    DocTypes are synchronized by ``bench migrate`` before post-model-sync
    patches run, so reloading them here is both unnecessary and unsafe on
    databases that contain legacy metadata rows with a missing modified value.
    """
    ensure_roles()

    if not frappe.db.exists("DocType", "WAFD Governance Settings"):
        return

    settings = frappe.get_single("WAFD Governance Settings")
    changed = False

    if not settings.approver_role:
        settings.approver_role = "WAFD Approver"
        changed = True
    if not settings.audit_retention_days:
        settings.audit_retention_days = 2555
        changed = True

    if changed:
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)

    frappe.clear_cache()
