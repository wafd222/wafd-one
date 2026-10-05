"""Refresh Iftar daily-operation UI after participant-name entry fix."""

import frappe


def execute():
    # Iftar-only cache refresh. No delivery, driver, undertaking, inventory,
    # finance, quotation, cleaning or other operational DocTypes are reloaded.
    frappe.clear_cache()
