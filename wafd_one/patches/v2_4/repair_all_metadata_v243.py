"""Repair all WAFD ONE metadata and rebuild its workspace after model sync."""

import frappe

from wafd_one.setup import apply_setup


def execute():
    apply_setup(force_rebuild=True, assign_manager_access=True)
    frappe.db.commit()
