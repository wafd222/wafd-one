"""Rebuild WAFD ONE Workspace with Frappe v16 block identifiers.

Frappe v16's Workspace block renderer expects every content block to have a
stable ``id``. Older WAFD ONE releases omitted those IDs, so headers and text
rendered while shortcut blocks were silently ignored.
"""

import json

import frappe

from wafd_one.setup import rebuild_workspace_from_source


def execute():
    rebuild_workspace_from_source()

    workspace = frappe.get_doc("Workspace", "WAFD ONE")
    blocks = json.loads(workspace.content or "[]")
    missing_ids = [index for index, block in enumerate(blocks) if not block.get("id")]
    if missing_ids:
        frappe.throw(
            "WAFD ONE Workspace contains blocks without Frappe v16 IDs: "
            + ", ".join(map(str, missing_ids))
        )

    expected_shortcuts = {
        "المشاريع",
        "البعثات والعملاء",
        "الفنادق",
        "العقود",
        "خطط الوجبات",
        "الوصفات",
        "مكونات الأغذية",
    }
    rendered_shortcuts = {
        block.get("data", {}).get("shortcut_name")
        for block in blocks
        if block.get("type") == "shortcut"
    }
    missing = expected_shortcuts - rendered_shortcuts
    if missing:
        frappe.throw(
            "WAFD ONE Workspace is missing shortcut blocks: " + ", ".join(sorted(missing))
        )

    frappe.clear_cache()
