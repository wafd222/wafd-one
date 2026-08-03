import json
import frappe
from wafd_one.document_studio import compile_template
from wafd_one.patches.v10_0_0_rc38.execute import undertaking_canvas


def _final_undertaking_canvas():
    canvas = undertaking_canvas()
    blocks = canvas.get("blocks") or []
    # Remove the obsolete empty image boxes and handwritten signature line.
    blocks = [b for b in blocks if b.get("id") not in {"signature", "stamp"}]
    for block in blocks:
        if block.get("id") == "signatory":
            block["x"] = 70
            block["y"] = 790
            block["w"] = 285
            block["h"] = 105
            block["html"] = (
                '<div style="direction:rtl;text-align:center;font-size:10.5px;line-height:1.7;">'
                '<b>شركة وفد المدينة لخدمات الإعاشة</b><br>'
                '{{ doc.authorized_signatory or doc.company_representative or "الممثل المعتمد" }}<br>'
                '{{ doc.signatory_title or "" }}'
                '</div>'
            )
    # Conditional HTML blocks render real images only; no placeholder rectangles.
    blocks.extend([
        {
            "id": "signature_image_final", "type": "field", "x": 390, "y": 780,
            "w": 145, "h": 110, "z": 10,
            "html": (
                '{% set sig = doc.signature_image or template.signature %}'
                '{% if sig %}<div style="width:100%;height:100%;text-align:center;">'
                '<img src="{{ sig }}" alt="" style="max-width:100%;max-height:100%;object-fit:contain;">'
                '</div>{% endif %}'
            ),
            "font_family": "Arial", "font_size": 10, "color": "#111111",
            "background": "transparent", "opacity": 1, "rotation": 0,
        },
        {
            "id": "stamp_image_final", "type": "field", "x": 555, "y": 765,
            "w": 175, "h": 135, "z": 11,
            "html": (
                '{% set seal = doc.company_stamp or template.stamp %}'
                '{% if seal %}<div style="width:100%;height:100%;text-align:center;">'
                '<img src="{{ seal }}" alt="" style="max-width:100%;max-height:100%;object-fit:contain;">'
                '</div>{% endif %}'
            ),
            "font_family": "Arial", "font_size": 10, "color": "#111111",
            "background": "transparent", "opacity": 1, "rotation": 0,
        },
    ])
    canvas["blocks"] = blocks
    return canvas


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    canvas = _final_undertaking_canvas()
    names = frappe.get_all(
        "WAFD Document Template",
        filters={"reference_doctype": "WAFD Hotel Undertaking"},
        pluck="name",
    )
    for name in names:
        doc = frappe.get_doc("WAFD Document Template", name)
        doc.canvas_json = json.dumps(canvas, ensure_ascii=False)
        doc.page_size = "A4"
        doc.orientation = "Portrait"
        doc.direction = "RTL"
        doc.margin_top_mm = doc.margin_right_mm = 0
        doc.margin_bottom_mm = doc.margin_left_mm = 0
        doc.enabled = 1
        doc.is_default = 1
        doc.compiled_html = compile_template(doc)
        doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype="WAFD Document Template")
