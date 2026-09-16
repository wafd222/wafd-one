"""Normalize legacy Iftar stages and refresh the mobile role dashboard."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_daily_operation", force=True, reset_permissions=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)
    from wafd_one.wafd_one.iftar_team import normalize_legacy_iftar_sequence
    normalize_legacy_iftar_sequence()
    frappe.clear_cache()
