"""Synchronize all WAFD ONE metadata after Frappe model sync.

This patch repairs sites created from earlier releases where the app code was
present but some DocType metadata was not persisted in the database. It is
idempotent and safe to run once through the Patch Log.
"""

import frappe

from wafd_one.setup import apply_setup


def execute():
    apply_setup(force_rebuild=True, assign_manager_access=True, sync_doctypes=True)
    frappe.clear_cache()
