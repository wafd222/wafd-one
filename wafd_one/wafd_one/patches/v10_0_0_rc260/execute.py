import json

import frappe


SOURCE_LAYOUT = {
    "intro": {"y": 168, "h": 180},
    "details": {"y": 360, "h": 265},
    "terms": {"y": 610, "h": 170},
    "signatory": {"y": 790, "h": 82},
    "signature": {"y": 785, "h": 90},
    "stamp": {"y": 770, "h": 120},
}

TARGET_LAYOUT = {
    "intro": {"y": 168, "h": 105},
    "details": {"y": 285, "h": 265},
    "terms": {"y": 535, "h": 170},
    "signatory": {"y": 715, "h": 82},
    "signature": {"y": 710, "h": 90},
    "stamp": {"y": 695, "h": 120},
}


def _matches_known_layout(blocks_by_id):
    for block_id, source_position in SOURCE_LAYOUT.items():
        block = blocks_by_id.get(block_id)
        if not block:
            return False
        current = {key: block.get(key) for key in ("y", "h")}
        if current not in (source_position, TARGET_LAYOUT[block_id]):
            return False
    return True


def _tighten_spacing(canvas):
    blocks = canvas.get("blocks") if isinstance(canvas, dict) else None
    if not isinstance(blocks, list):
        return False

    blocks_by_id = {
        block.get("id"): block
        for block in blocks
        if isinstance(block, dict) and block.get("id")
    }
    if not _matches_known_layout(blocks_by_id):
        return False

    changed = False
    for block_id, target_position in TARGET_LAYOUT.items():
        block = blocks_by_id[block_id]
        for key, value in target_position.items():
            if block.get(key) != value:
                block[key] = value
                changed = True
    return changed


def execute():
    """Tighten undertaking spacing without replacing text, styling or template data."""
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return

    changed = False
    names = frappe.get_all(
        "WAFD Document Template",
        filters={"document_category": "Hotel Undertaking"},
        pluck="name",
    )
    for name in names:
        raw_canvas = frappe.db.get_value("WAFD Document Template", name, "canvas_json")
        if not raw_canvas:
            continue
        try:
            canvas = json.loads(raw_canvas)
        except (TypeError, ValueError):
            continue
        if not _tighten_spacing(canvas):
            continue
        frappe.db.set_value(
            "WAFD Document Template",
            name,
            "canvas_json",
            json.dumps(canvas, ensure_ascii=False),
            update_modified=False,
        )
        changed = True

    if changed:
        frappe.clear_cache(doctype="WAFD Document Template")
