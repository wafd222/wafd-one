"""RC144 deployment cache refresh after report/attendance QA hardening."""

import frappe


def execute():
    # RC143/RC144 change Page JS and Print Format metadata. Clearing caches here
    # ensures Desk and print metadata are re-read immediately after migrate.
    frappe.clear_cache()
