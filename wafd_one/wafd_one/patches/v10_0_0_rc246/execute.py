"""RC246: repair missing or obsolete explicit driver assignments."""

import frappe


def execute():
    from wafd_one.driver_security import repair_trip_assignments

    repair_trip_assignments()
    frappe.clear_cache()
