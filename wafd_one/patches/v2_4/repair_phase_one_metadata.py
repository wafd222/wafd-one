"""Repair Phase 1 metadata after Frappe has completed model synchronization."""

import frappe

from wafd_one.setup import PHASE_ONE_DOCTYPE_FILES, ensure_roles, ensure_system_manager_access, reload_workspace


def execute():
    ensure_roles()

    # Explicit reload repairs sites that previously deployed the files but did not
    # persist the DocType metadata. Child tables are loaded before their parents.
    for doctype_file in PHASE_ONE_DOCTYPE_FILES:
        frappe.reload_doc(
            "wafd_one",
            "doctype",
            doctype_file,
            force=True,
            reset_permissions=True,
        )

    reload_workspace()
    ensure_system_manager_access()
    frappe.clear_cache()
