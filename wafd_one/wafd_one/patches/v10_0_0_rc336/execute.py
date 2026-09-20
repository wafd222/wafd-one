from __future__ import annotations

import frappe


def execute():
    """Refresh the concise official report and reliable native-share preview."""
    frappe.reload_doc("wafd_one", "print_format", "wafd_iftar_official_daily_report", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_team", force=True)
    frappe.clear_cache()
