from __future__ import annotations

import frappe


def execute():
    """Install the RC333 Iftar reconciliation and mobile-action correction."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_supervisor_daily_report", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_daily_operation", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_supervisor", force=True)
    frappe.clear_cache()
