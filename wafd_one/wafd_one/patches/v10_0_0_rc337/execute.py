from __future__ import annotations

import frappe

from wafd_one.driver_security import repair_trip_assignments


def execute():
    """Repair legacy driver links and refresh both isolated driver screens."""
    repair_trip_assignments()
    frappe.reload_doc("wafd_one", "page", "wafd_driver_trips", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_iftar_driver", force=True)
    frappe.clear_cache()
