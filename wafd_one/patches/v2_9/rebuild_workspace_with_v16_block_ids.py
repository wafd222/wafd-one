"""Rebuild WAFD ONE workspace using the Frappe v16 block schema.

Frappe v16 workspace blocks are identified by a stable ``id``.  The older
workspace source had no IDs. Text blocks were still displayed, while shortcut
widgets were silently skipped by the v16 client. This patch recreates the
workspace from the corrected source and verifies both shortcut and card blocks.
"""

import frappe

from wafd_one.setup import rebuild_workspace_from_source


def execute():
    rebuild_workspace_from_source()
    frappe.clear_cache()
