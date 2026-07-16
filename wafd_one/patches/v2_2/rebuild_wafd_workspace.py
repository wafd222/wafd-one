"""Force-sync the standard WAFD ONE workspace on existing sites."""

import frappe

from wafd_one.setup import ensure_workspace


def execute():
    ensure_workspace(force_reload=True)
    frappe.clear_cache()
