import json

import frappe


LIVE_COMPACT_LAYOUT = {
    "intro": {"y": 168, "h": 105},
    "details": {"y": 285, "h": 265},
    "terms": {"y": 535, "h": 225},
    "signatory": {"y": 775, "h": 82},
    "signature": {"y": 770, "h": 90},
    "stamp": {"y": 755, "h": 120},
}

LIVE_APPROVED_LAYOUT = {
    "intro": {"y": 168, "h": 180},
    "details": {"y": 360, "h": 265},
    "terms": {"y": 610, "h": 225},
    "signatory": {"y": 850, "h": 82},
    "signature": {"y": 845, "h": 90},
    "stamp": {"y": 830, "h": 120},
}

BASE_COMPACT_LAYOUT = {
    "intro": {"y": 168, "h": 105},
    "details": {"y": 285, "h": 265},
    "terms": {"y": 535, "h": 170},
    "signatory": {"y": 715, "h": 82},
    "signature": {"y": 710, "h": 90},
    "stamp": {"y": 695, "h": 120},
}

BASE_APPROVED_LAYOUT = {
    "intro": {"y": 168, "h": 180},
    "details": {"y": 360, "h": 265},
    "terms": {"y": 610, "h": 170},
    "signatory": {"y": 790, "h": 82},
    "signature": {"y": 785, "h": 90},
    "stamp": {"y": 770, "h": 120},
}


def _restore_matching_layout(canvas, compact, approved):
    blocks = canvas.get("blocks") if isinstance(canvas, dict) else None
    if not isinstance(blocks, list):
        return False
    blocks_by_id = {
        block.get("id"): block
        for block in blocks
        if isinstance(block, dict) and block.get("id")
    }
    for block_id, compact_position in compact.items():
        block = blocks_by_id.get(block_id)
        if not block:
            return False
        current = {key: block.get(key) for key in ("y", "h")}
        if current not in (compact_position, approved[block_id]):
            return False

    changed = False
    for block_id, approved_position in approved.items():
        block = blocks_by_id[block_id]
        for key, value in approved_position.items():
            if block.get(key) != value:
                block[key] = value
                changed = True
    return changed


def _restore_approved_layout(canvas):
    if _restore_matching_layout(canvas, LIVE_COMPACT_LAYOUT, LIVE_APPROVED_LAYOUT):
        return True
    return _restore_matching_layout(canvas, BASE_COMPACT_LAYOUT, BASE_APPROVED_LAYOUT)


def execute():
    """Restore the previously approved undertaking layout without changing content."""
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return

    changed = False
    rows = frappe.get_all(
        "WAFD Document Template",
        filters={"reference_doctype": "WAFD Hotel Undertaking"},
        fields=["name", "canvas_json"],
    )
    for row in rows:
        try:
            canvas = json.loads(row.canvas_json or "{}")
        except (TypeError, ValueError):
            continue
        if not _restore_approved_layout(canvas):
            continue
        frappe.db.set_value(
            "WAFD Document Template",
            row.name,
            {"canvas_json": json.dumps(canvas, ensure_ascii=False), "compiled_html": ""},
            update_modified=False,
        )
        changed = True

    if changed:
        frappe.clear_cache(doctype="WAFD Document Template")
        frappe.clear_cache(doctype="WAFD Hotel Undertaking")
