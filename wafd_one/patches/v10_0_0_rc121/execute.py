import json
from pathlib import Path
import frappe


def execute():
    root = Path(frappe.get_app_path("wafd_one")) / "wafd_one" / "print_format"
    for path in root.glob("wafd_iftar_*/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("name")
        if not name:
            continue
        values = {
            "doc_type": data.get("doc_type"),
            "html": data.get("html") or "",
            "css": data.get("css") or "",
            "custom_format": 1,
            "print_format_type": "Jinja",
            "disable_letterhead": 1,
            "letter_head": None,
            "margin_top": 4,
            "margin_bottom": 4,
            "margin_left": 5,
            "margin_right": 5,
            "disabled": 0,
        }
        if frappe.db.exists("Print Format", name):
            frappe.db.set_value("Print Format", name, values, update_modified=False)
        else:
            doc = frappe.new_doc("Print Format")
            doc.update({"name": name, "module": "WAFD ONE", "standard": "Yes", **values})
            doc.insert(ignore_permissions=True)
    frappe.clear_cache()
