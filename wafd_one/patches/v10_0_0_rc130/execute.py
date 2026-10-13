from __future__ import annotations

import json
from pathlib import Path
import frappe


def execute():
    # Force-refresh the supervisor receipt definition so sites that retained an older
    # 15-row database copy receive the current 10-row template.
    base = Path(frappe.get_app_path("wafd_one")) / "wafd_one" / "print_format" / "wafd_iftar_supervisor_receipt" / "wafd_iftar_supervisor_receipt.json"
    if base.exists() and frappe.db.exists("Print Format", "WAFD Iftar Supervisor Receipt"):
        data = json.loads(base.read_text(encoding="utf-8"))
        frappe.db.set_value("Print Format", "WAFD Iftar Supervisor Receipt", "html", data.get("html") or "", update_modified=False)
    frappe.clear_cache(doctype="WAFD Iftar Daily Operation")
