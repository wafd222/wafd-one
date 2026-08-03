"""Rebuild the WAFD ONE workspace from the packaged source definition.

Earlier releases used ``frappe.reload_doc``. On sites where a Workspace record
already existed, that did not reliably replace its child Shortcut/Link rows.
This patch deliberately recreates the standard public workspace and validates
that all Phase 1 shortcuts were persisted.
"""

import frappe

from wafd_one.setup import rebuild_workspace_from_source


def execute():
    rebuild_workspace_from_source()
    frappe.clear_cache()
