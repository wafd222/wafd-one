import json

import frappe


REMOVED_CLAUSES = (
    "، وعرض هذا التعهد للجهات المسؤولة عند الحاجة.",
    "، وعرض هذا التعهد للجهات المسؤولة.",
)


def _remove_clause(value):
    if not isinstance(value, str):
        return value
    for clause in REMOVED_CLAUSES:
        value = value.replace(clause, ".")
    return value


def _update_canvas_templates():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return False

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

        canvas_changed = False
        for block in canvas.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            for fieldname in ("html", "text", "content"):
                old_value = block.get(fieldname)
                new_value = _remove_clause(old_value)
                if new_value != old_value:
                    block[fieldname] = new_value
                    canvas_changed = True

        if canvas_changed:
            frappe.db.set_value(
                "WAFD Document Template",
                row.name,
                {
                    "canvas_json": json.dumps(canvas, ensure_ascii=False),
                    "compiled_html": "",
                },
                update_modified=False,
            )
            changed = True
    return changed


def _update_print_format():
    name = "تعهد والتزام إعاشة — WAFD"
    if not frappe.db.exists("Print Format", name):
        return False
    html = frappe.db.get_value("Print Format", name, "html") or ""
    updated = _remove_clause(html)
    if updated == html:
        return False
    frappe.db.set_value("Print Format", name, "html", updated, update_modified=False)
    return True


def _update_print_settings():
    if not frappe.db.exists("DocType", "WAFD Print Settings"):
        return False
    current = frappe.db.get_single_value("WAFD Print Settings", "closing_text") or ""
    updated = _remove_clause(current)
    if updated == current:
        return False
    frappe.db.set_single_value("WAFD Print Settings", "closing_text", updated)
    return True


def execute():
    """Remove only the requested undertaking clause; preserve content and layout otherwise."""
    canvas_changed = _update_canvas_templates()
    print_format_changed = _update_print_format()
    settings_changed = _update_print_settings()

    if canvas_changed:
        frappe.clear_cache(doctype="WAFD Document Template")
        frappe.clear_cache(doctype="WAFD Hotel Undertaking")
    if print_format_changed:
        frappe.clear_cache(doctype="Print Format")
    if settings_changed:
        frappe.clear_cache(doctype="WAFD Print Settings")
