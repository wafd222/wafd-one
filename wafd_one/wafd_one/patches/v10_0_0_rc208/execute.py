"""RC208: contract number metadata + undertaking template cleanup."""
import json
import frappe

TARGET = "WAFD Hotel Undertaking"

def _replace_template_blocks(canvas):
    changed = False
    for block in canvas.get("blocks") or []:
        blob = " ".join(str(block.get(k) or "") for k in ("html", "text", "content"))
        bid = str(block.get("id") or "").lower()
        if bid == "signatory" or ("شركة وفد المدينة لخدمات الإعاشة" in blob and "التوقيع:" in blob):
            new = blob.replace("<br>التوقيع: ____________________", "").replace("التوقيع: ____________________", "")
            for key in ("html", "text", "content"):
                if block.get(key): block[key] = str(block[key]).replace("<br>التوقيع: ____________________", "").replace("التوقيع: ____________________", "")
            changed = True
        if bid in {"details", "meta", "info"} or "Undertaking No" in blob or "رقم التعهد" in blob:
            # Keep existing design; only enrich a project row when recognizable.
            for key in ("html", "text", "content"):
                val = str(block.get(key) or "")
                if not val: continue
                val2 = val
                for old in ('{{ doc.project or "" }}', "{{ doc.project or '' }}"):
                    val2 = val2.replace(old, '{{ doc.project_display_name or doc.project or "" }}')
                # append contract number below project without changing table geometry
                if val2 != val and "رقم العقد" not in val2:
                    val2 = val2.replace('{{ doc.project_display_name or doc.project or "" }}', '{{ doc.project_display_name or doc.project or "" }}<br><span style="font-size:8.5px;color:#555">رقم العقد / Contract No.: {{ doc.contract_number or "" }}</span>')
                if val2 != val:
                    block[key] = val2; changed = True
    return changed

def execute():
    if frappe.db.exists("DocType", "WAFD Document Template"):
        rows = frappe.get_all("WAFD Document Template", filters={"reference_doctype": TARGET}, fields=["name", "canvas_json"])
        for row in rows:
            try: canvas = json.loads(row.canvas_json or "{}")
            except Exception: canvas = {}
            if _replace_template_blocks(canvas):
                frappe.db.set_value("WAFD Document Template", row.name, {"canvas_json": json.dumps(canvas, ensure_ascii=False), "compiled_html": ""}, update_modified=False)
    # backfill contract numbers for linked-project undertakings
    for row in frappe.get_all(TARGET, filters={"project": ["is", "set"]}, fields=["name", "project", "contract", "contract_number"]):
        contract = row.contract or frappe.db.get_value("WAFD Catering Project", row.project, "contract")
        number = frappe.db.get_value("WAFD Contract", contract, "contract_number") if contract else None
        project_name = frappe.db.get_value("WAFD Catering Project", row.project, "project_name")
        values = {}
        if project_name:
            values["project_display_name"] = project_name
        if number and row.contract_number != number:
            values.update({"contract": contract, "contract_number": number})
        if values:
            frappe.db.set_value(TARGET, row.name, values, update_modified=False)
    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()
    frappe.clear_cache(doctype=TARGET)
