from __future__ import annotations

import json
from pathlib import Path
import frappe


def _refresh_print_format(folder: str, name: str):
    path = Path(frappe.get_app_path("wafd_one")) / "wafd_one" / "print_format" / folder / f"{folder}.json"
    if not path.exists() or not frappe.db.exists("Print Format", name):
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    frappe.db.set_value("Print Format", name, {
        "html": data.get("html") or "",
        "css": data.get("css") or "",
        "disabled": 0,
    }, update_modified=False)


def execute():
    _refresh_print_format("wafd_iftar_supervisor_receipt", "WAFD Iftar Supervisor Receipt")
    _refresh_print_format("wafd_iftar_official_daily_report", "WAFD Iftar Official Daily Report")
    frappe.clear_cache(doctype="WAFD Iftar Daily Operation")
