from __future__ import annotations
import json
import frappe

TARGET_DOCTYPE = "WAFD Hotel Undertaking"

def _replace_text(value):
    if not isinstance(value, str):
        return value
    replacements = {
        "البعثة أو العميل / Mission or Client": "المستفيد / Beneficiary",
        "Mission or Client / البعثة أو العميل": "المستفيد / Beneficiary",
        "البعثة أو العميل": "المستفيد",
        "Mission or Client": "Beneficiary",
        '{{ doc.mission or doc.second_party_name or "" }}': '{{ doc.second_party_name or "" }}',
        "{{ doc.mission or doc.second_party_name or '' }}": "{{ doc.second_party_name or '' }}",
        '{{ doc.mission or "" }}': '{{ doc.second_party_name or "" }}',
        "{{ doc.mission or '' }}": "{{ doc.second_party_name or '' }}",
        "موقع التوريد / Supply Location": "رقم السجل التجاري / الهوية / الجواز",
        "Supply Location / موقع التوريد": "رقم السجل التجاري / الهوية / الجواز",
        "موقع التوريد": "رقم السجل التجاري / الهوية / الجواز",
        "Supply Location": "CR / ID / Passport No.",
        '{{ doc.supply_location or doc.hotel or "" }}': '{{ doc.second_party_cr or "" }}',
        "{{ doc.supply_location or doc.hotel or '' }}": "{{ doc.second_party_cr or '' }}",
        '{{ doc.supply_location or "" }}': '{{ doc.second_party_cr or "" }}',
        "{{ doc.supply_location or '' }}": "{{ doc.second_party_cr or '' }}",
    }
    for old,new in replacements.items(): value=value.replace(old,new)
    return value

def _walk(obj):
    if isinstance(obj, dict):
        out={k:_walk(v) for k,v in obj.items()}
        # Enlarge only stamp elements, preserving the approved design.
        typ=str(out.get("type") or out.get("element_type") or "").lower()
        if typ == "stamp" or str(out.get("id") or "").lower() == "stamp":
            for key in ("width","w"):
                if isinstance(out.get(key),(int,float)): out[key]=round(out[key]*1.35)
            for key in ("height","h"):
                if isinstance(out.get(key),(int,float)): out[key]=round(out[key]*1.35)
        return out
    if isinstance(obj, list): return [_walk(x) for x in obj]
    if isinstance(obj, str): return _replace_text(obj)
    return obj

def execute():
    if frappe.db.exists("DocType", "WAFD Print Settings"):
        settings=frappe.get_single("WAFD Print Settings")
        frappe.db.sql("""update `tabWAFD Hotel Undertaking`
            set include_signature=coalesce(include_signature,1), include_stamp=coalesce(include_stamp,1),
                signature_image=coalesce(nullif(signature_image,''), %s),
                company_stamp=coalesce(nullif(company_stamp,''), %s),
                authorized_signatory=coalesce(nullif(authorized_signatory,''),'نزار بن نذير بن ظفر')""",
            (settings.default_signature or '', settings.default_stamp or ''))
    if frappe.db.exists("DocType", "WAFD Document Template"):
        names=frappe.get_all("WAFD Document Template",filters={"reference_doctype":TARGET_DOCTYPE},pluck="name")
        for name in names:
            doc=frappe.get_doc("WAFD Document Template",name)
            if doc.canvas_json:
                try: doc.canvas_json=json.dumps(_walk(json.loads(doc.canvas_json)),ensure_ascii=False)
                except Exception: doc.canvas_json=_replace_text(doc.canvas_json)
            doc.compiled_html=_replace_text(doc.compiled_html)
            # Increase only stamp image limits in generated HTML/CSS.
            doc.compiled_html=(doc.compiled_html or '').replace('max-width:46mm','max-width:62mm').replace('max-height:34mm','max-height:46mm')
            doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype=TARGET_DOCTYPE)
    frappe.clear_cache(doctype="WAFD Document Template")
