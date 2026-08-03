import json
import frappe


def _restore_approved_canvas():
    """Restore the previously approved one-page undertaking design.

    Only the three requested adjustments are applied:
    1) signature overlays the authorised signatory name,
    2) stamp is larger and below the General Manager title,
    3) saved company defaults from RC81 remain untouched.
    """
    from wafd_one.patches.v10_0_0_rc36.execute import undertaking_canvas

    canvas = undertaking_canvas()
    blocks = canvas.get("blocks") or []

    # Keep every original block and coordinate exactly as approved, replacing
    # only the signature area blocks.
    blocks = [
        block for block in blocks
        if block.get("id") not in {"signatory", "signature", "stamp"}
    ]

    blocks.extend([
        {
            "id": "signatory", "type": "field", "x": 48, "y": 842,
            "w": 300, "h": 100, "z": 5,
            "html": (
                '<div style="direction:rtl;text-align:center;font-size:11px;line-height:1.8;">'
                '<b>شركة وفد المدينة لخدمات الإعاشة</b><br>'
                '<span style="position:relative;display:inline-block;min-width:210px;padding:16px 8px 4px;">'
                '{{ doc.authorized_signatory or doc.company_representative or "نزار بن مذير بن ظفر" }}'
                '</span><br>'
                '{{ doc.signatory_title or "المدير العام / General Manager" }}'
                '</div>'
            ),
            "font_family": "Arial", "font_size": 12, "color": "#111111",
            "background": "transparent", "opacity": 1, "rotation": 0,
        },
        {
            "id": "signature", "type": "signature", "x": 88, "y": 850,
            "w": 220, "h": 72, "z": 15,
            "html": "", "src": '{{ doc.signature_image or "" }}',
            "font_family": "Arial", "font_size": 12, "color": "#111111",
            "background": "transparent", "opacity": 1, "rotation": 0,
        },
        {
            "id": "stamp", "type": "stamp", "x": 95, "y": 922,
            "w": 205, "h": 92, "z": 12,
            "html": "", "src": '{{ doc.company_stamp or "" }}',
            "font_family": "Arial", "font_size": 12, "color": "#111111",
            "background": "transparent", "opacity": 1, "rotation": 0,
        },
    ])
    canvas["blocks"] = blocks
    return canvas


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return

    canvas_json = json.dumps(_restore_approved_canvas(), ensure_ascii=False)
    names = frappe.get_all(
        "WAFD Document Template",
        filters={"reference_doctype": "WAFD Hotel Undertaking"},
        pluck="name",
    )
    for name in names:
        template = frappe.get_doc("WAFD Document Template", name)
        template.page_size = "A4"
        template.orientation = "Portrait"
        template.direction = "RTL"
        template.canvas_json = canvas_json
        template.compiled_html = ""
        template.save(ignore_permissions=True)

    # Keep the approved standard print format from RC80 synchronized as a
    # fallback, without changing its layout.
    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()

    frappe.clear_cache(doctype="WAFD Document Template")
    frappe.clear_cache(doctype="WAFD Hotel Undertaking")
