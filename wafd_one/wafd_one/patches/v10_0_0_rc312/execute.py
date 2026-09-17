"""Remove only legacy Iftar employee shortcut cards from role homes."""

import frappe


def execute():
    # UI metadata only. Do not reload or mutate delivery, driver, inventory,
    # undertaking, quotation, finance, or Iftar operational DocTypes.
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache()
