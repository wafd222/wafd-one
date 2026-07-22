import json
from html import escape
import frappe
from frappe.utils.pdf import get_pdf

ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Project Manager"}
ALLOWED_PAGE_SIZES = {"A4", "A5", "Letter"}
ALLOWED_ORIENTATIONS = {"Portrait", "Landscape"}
ALLOWED_DIRECTIONS = {"RTL", "LTR"}
ALLOWED_BLOCK_TYPES = {"text", "field", "image", "logo", "stamp", "signature", "line", "table", "qr"}
DANGEROUS_MARKUP = (
    "<script", "</style", "javascript:", "vbscript:", "expression(",
    "@import", "onerror=", "onload=", "onclick=", "onmouseover=",
)



QUICK_TEMPLATE_TYPES = {
    "undertaking": {"title": "تعهد فندق", "doctype": "WAFD Hotel Undertaking", "category": "Hotel Undertaking"},
    "contract": {"title": "عقد", "doctype": "WAFD Contract", "category": "Contract"},
    "quotation": {"title": "عرض سعر", "doctype": "WAFD Contract", "category": "Quotation"},
    "invoice": {"title": "فاتورة", "doctype": "WAFD Invoice", "category": "Invoice"},
    "operation": {"title": "أمر تشغيل", "doctype": "WAFD Catering Project", "category": "Operation Order"},
    "certificate": {"title": "شهادة", "doctype": "WAFD Hotel Undertaking", "category": "Certificate"},
}


def _starter_canvas(title):
    return {
        "version": 2,
        "blocks": [
            {"id": "header", "type": "text", "x": 70, "y": 45, "w": 650, "h": 44, "z": 1, "html": '<div style="text-align:center;font-size:20px;font-weight:700">شركة وفد المدينة لخدمات الإعاشة</div>', "font_family": "Arial", "font_size": 18, "color": "#111111", "background": "transparent", "opacity": 1, "rotation": 0},
            {"id": "title", "type": "text", "x": 120, "y": 120, "w": 550, "h": 55, "z": 2, "html": f'<div style="text-align:center;font-size:26px;font-weight:700">{escape(title)}</div>', "font_family": "Arial", "font_size": 24, "color": "#111111", "background": "transparent", "opacity": 1, "rotation": 0},
            {"id": "date", "type": "field", "x": 500, "y": 190, "w": 230, "h": 32, "z": 2, "html": '<div style="text-align:right">التاريخ: {{ frappe.utils.formatdate(frappe.utils.nowdate()) }}</div>', "font_family": "Arial", "font_size": 14, "color": "#111111", "background": "transparent", "opacity": 1, "rotation": 0},
            {"id": "docname", "type": "field", "x": 70, "y": 190, "w": 260, "h": 32, "z": 2, "html": '<div style="text-align:left">الرقم: {{ doc.get("name") or "" }}</div>', "font_family": "Arial", "font_size": 14, "color": "#111111", "background": "transparent", "opacity": 1, "rotation": 0},
            {"id": "body", "type": "text", "x": 75, "y": 250, "w": 650, "h": 430, "z": 2, "html": '<div style="direction:rtl;text-align:right;line-height:2">اكتب نص المستند هنا. اضغط مرتين على النص للتعديل، أو أضف بيانات المستند من القائمة.</div>', "font_family": "Arial", "font_size": 16, "color": "#111111", "background": "transparent", "opacity": 1, "rotation": 0},
            {"id": "signature", "type": "text", "x": 430, "y": 760, "w": 290, "h": 80, "z": 2, "html": '<div style="text-align:center;line-height:1.8">شركة وفد المدينة لخدمات الإعاشة<br>التوقيع والختم</div>', "font_family": "Arial", "font_size": 14, "color": "#111111", "background": "transparent", "opacity": 1, "rotation": 0},
            {"id": "footerline", "type": "line", "x": 70, "y": 930, "w": 660, "h": 10, "z": 1, "html": "", "font_family": "Arial", "font_size": 12, "color": "#111111", "background": "transparent", "opacity": 1, "rotation": 0},
        ],
    }


def _unique_template_title(base_title):
    title = base_title
    number = 2
    while frappe.db.exists("WAFD Document Template", {"template_title": title}):
        title = f"{base_title} {number}"
        number += 1
    return title


@frappe.whitelist()
def quick_create_template(kind):
    _check_access(write=True)
    config = QUICK_TEMPLATE_TYPES.get(kind)
    if not config:
        frappe.throw(frappe._("Unsupported document type."))
    if not frappe.db.exists("DocType", config["doctype"]):
        frappe.throw(frappe._("The required document type is not installed: {0}").format(config["doctype"]))
    title = _unique_template_title(config["title"])
    doc = frappe.get_doc({
        "doctype": "WAFD Document Template",
        "template_title": title,
        "reference_doctype": config["doctype"],
        "document_category": config["category"],
        "enabled": 1,
        "page_size": "A4",
        "orientation": "Portrait",
        "direction": "RTL",
        "margin_top_mm": 10,
        "margin_right_mm": 10,
        "margin_bottom_mm": 10,
        "margin_left_mm": 10,
        "canvas_json": json.dumps(_starter_canvas(title), ensure_ascii=False),
    })
    doc.insert()
    return doc.name

def _check_access(write=False):
    roles = set(frappe.get_roles())
    if not roles.intersection(ALLOWED_ROLES):
        frappe.throw(frappe._("You are not permitted to use WAFD Document Studio."), frappe.PermissionError)
    if write and not roles.intersection({"System Manager", "WAFD Operations Manager"}):
        frappe.throw(frappe._("You are not permitted to modify document templates."), frappe.PermissionError)


def _num(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _assert_safe_markup(value, label):
    value = str(value or "")
    lowered = value.lower().replace(" ", "")
    if any(token.replace(" ", "") in lowered for token in DANGEROUS_MARKUP):
        frappe.throw(frappe._("Unsafe content detected in {0}.").format(label))
    return value


def _safe_style(value):
    value = _assert_safe_markup(value, frappe._("CSS style"))
    return escape(value, quote=True)


def _page_dimensions(size, orientation):
    sizes = {"A4": (210, 297), "A5": (148, 210), "Letter": (216, 279)}
    w, h = sizes.get(size, sizes["A4"])
    return (h, w) if orientation == "Landscape" else (w, h)


def compile_template(template):
    try:
        canvas = json.loads(template.canvas_json or "{}")
    except Exception:
        canvas = {"blocks": []}
    blocks = canvas.get("blocks") or []
    width_mm, height_mm = _page_dimensions(template.page_size, template.orientation)
    direction = "rtl" if template.direction == "RTL" else "ltr"
    items = []
    for block in blocks:
        btype = block.get("type", "text")
        x, y = _num(block.get("x"), 0), _num(block.get("y"), 0)
        w, h = max(_num(block.get("w"), 20), 5), max(_num(block.get("h"), 20), 5)
        z = int(_num(block.get("z"), 1))
        style = _safe_style(block.get("style"))
        font_family = escape(str(block.get("font_family") or "Arial"), quote=True)
        font_size = max(min(_num(block.get("font_size"), 14), 200), 6)
        color = escape(str(block.get("color") or "#111111"), quote=True)
        background = escape(str(block.get("background") or "transparent"), quote=True)
        opacity = max(min(_num(block.get("opacity"), 1), 1), 0)
        rotation = max(min(_num(block.get("rotation"), 0), 360), -360)
        formatting = ""
        if block.get("bold"):
            formatting += "font-weight:700;"
        if block.get("italic"):
            formatting += "font-style:italic;"
        if block.get("underline"):
            formatting += "text-decoration:underline;"
        base = (
            f"position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;z-index:{z};"
            f"overflow:hidden;font-family:{font_family};font-size:{font_size}px;color:{color};"
            f"background:{background};opacity:{opacity};transform:rotate({rotation}deg);{formatting}{style}"
        )
        if btype in {"image", "logo", "stamp", "signature"}:
            src = escape(str(block.get("src") or getattr(template, btype, "") or ""), quote=True)
            content = f'<img src="{src}" alt="" style="width:100%;height:100%;object-fit:contain">' if src else ""
        elif btype == "line":
            content = '<div style="border-top:1px solid #222;margin-top:50%"></div>'
        elif btype == "qr":
            content = '<div style="border:1px solid #222;width:100%;height:100%;display:flex;align-items:center;justify-content:center">QR</div>'
        else:
            content = _assert_safe_markup(block.get("html") or "", frappe._("document element"))
        items.append(f'<div class="wds-print-block" style="{base}">{content}</div>')
    css = _assert_safe_markup(template.custom_css or "", frappe._("custom CSS"))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size:{template.page_size} {template.orientation.lower()}; margin:0; }}
html,body{{margin:0;padding:0;background:white;}}
.wds-print-page{{position:relative;box-sizing:border-box;width:{width_mm}mm;height:{height_mm}mm;padding:{_num(template.margin_top_mm,10)}mm {_num(template.margin_right_mm,10)}mm {_num(template.margin_bottom_mm,10)}mm {_num(template.margin_left_mm,10)}mm;direction:{direction};font-family:Arial,"Noto Naskh Arabic",sans-serif;overflow:hidden;page-break-after:avoid;}}
.wds-print-block table{{border-collapse:collapse;}}
{css}
</style></head><body><div class="wds-print-page">{''.join(items)}</div></body></html>"""


@frappe.whitelist()
def list_templates():
    _check_access()
    return frappe.get_all("WAFD Document Template", filters={"enabled": 1}, fields=["name", "template_title", "reference_doctype", "document_category", "is_default"], order_by="reference_doctype asc, is_default desc, template_title asc")


@frappe.whitelist()
def get_template(template_name):
    _check_access()
    doc = frappe.get_doc("WAFD Document Template", template_name)
    doc.check_permission("read")
    try:
        canvas = json.loads(doc.canvas_json or "{}")
    except Exception:
        canvas = {"version": 1, "blocks": []}
    meta = frappe.get_meta(doc.reference_doctype)
    fields = [{"fieldname": "name", "label": frappe._("Document ID"), "fieldtype": "Data"}]
    fields += [{"fieldname": f.fieldname, "label": f.label, "fieldtype": f.fieldtype} for f in meta.fields if f.fieldname and f.fieldtype not in {"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Table"}]
    result = doc.as_dict(no_nulls=False)
    result["canvas"] = canvas
    result["meta_fields"] = fields
    return result


@frappe.whitelist()
def create_template(template_title, reference_doctype, document_category="Other"):
    _check_access(write=True)
    if not frappe.db.exists("DocType", reference_doctype):
        frappe.throw(frappe._("Reference DocType does not exist."))
    doc = frappe.get_doc({"doctype": "WAFD Document Template", "template_title": template_title, "reference_doctype": reference_doctype, "document_category": document_category, "enabled": 1, "page_size": "A4", "orientation": "Portrait", "direction": "RTL", "canvas_json": json.dumps({"version": 1, "blocks": []})})
    doc.insert()
    return doc.name


@frappe.whitelist()
def save_template(template_name, canvas_json, page_settings=None):
    _check_access(write=True)
    doc = frappe.get_doc("WAFD Document Template", template_name)
    doc.check_permission("write")
    try:
        payload = json.loads(canvas_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        frappe.throw(frappe._("Designer data is not valid JSON."))
    if not isinstance(payload, dict) or not isinstance(payload.get("blocks", []), list):
        frappe.throw(frappe._("Invalid designer payload."))
    blocks = payload.get("blocks", [])
    if len(blocks) > 250:
        frappe.throw(frappe._("A template cannot contain more than 250 elements."))
    for index, block in enumerate(blocks, start=1):
        if not isinstance(block, dict) or block.get("type") not in ALLOWED_BLOCK_TYPES:
            frappe.throw(frappe._("Invalid element at position {0}.").format(index))
        for key in ("x", "y", "w", "h", "z", "font_size", "opacity", "rotation"):
            if key in block and not isinstance(block[key], (int, float)):
                frappe.throw(frappe._("Invalid numeric value in element {0}.").format(index))
        if _num(block.get("x"), 0) < 0 or _num(block.get("y"), 0) < 0:
            frappe.throw(frappe._("Element positions cannot be negative."))
        if _num(block.get("w"), 20) < 5 or _num(block.get("h"), 20) < 5:
            frappe.throw(frappe._("Element dimensions are too small."))
        # Compile once during validation to reject unsafe HTML/CSS before saving.
        _assert_safe_markup(block.get("html") or "", frappe._("document element"))
        _assert_safe_markup(block.get("style") or "", frappe._("CSS style"))
    doc.canvas_json = json.dumps(payload, ensure_ascii=False)
    if page_settings:
        settings = json.loads(page_settings)
        page_size = settings.get("page_size", doc.page_size)
        orientation = settings.get("orientation", doc.orientation)
        direction = settings.get("direction", doc.direction)
        if page_size not in ALLOWED_PAGE_SIZES:
            frappe.throw(frappe._("Invalid page size."))
        if orientation not in ALLOWED_ORIENTATIONS:
            frappe.throw(frappe._("Invalid page orientation."))
        if direction not in ALLOWED_DIRECTIONS:
            frappe.throw(frappe._("Invalid text direction."))
        doc.page_size = page_size
        doc.orientation = orientation
        doc.direction = direction
        for key in ("margin_top_mm", "margin_right_mm", "margin_bottom_mm", "margin_left_mm"):
            if key in settings:
                value = _num(settings[key], 10)
                if value < 0 or value > 50:
                    frappe.throw(frappe._("Page margins must be between 0 and 50 mm."))
                setattr(doc, key, value)
    doc.save()
    return {"name": doc.name, "revision": doc.revision}


def _render(template_name, doctype=None, docname=None):
    template = frappe.get_doc("WAFD Document Template", template_name)
    template.check_permission("read")
    html = template.compiled_html or compile_template(template)
    if doctype and docname:
        if doctype != template.reference_doctype:
            frappe.throw(frappe._("The selected document does not match the template DocType."))
        doc = frappe.get_doc(doctype, docname)
        doc.check_permission("read")
    else:
        doc = frappe._dict(name="PREVIEW", title=frappe._("Preview"))
    return frappe.render_template(html, {"doc": doc, "template": template})


@frappe.whitelist()
def preview_html(template_name, doctype=None, docname=None):
    _check_access()
    html = _render(template_name, doctype, docname)
    frappe.local.response.filename = f"{frappe.scrub(template_name)}.html"
    frappe.local.response.filecontent = html.encode("utf-8")
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "inline"
    frappe.local.response.content_type = "text/html; charset=utf-8"


@frappe.whitelist()
def download_pdf(template_name, doctype=None, docname=None):
    _check_access()
    html = _render(template_name, doctype, docname)
    pdf = get_pdf(html)
    frappe.local.response.filename = f"{frappe.scrub(template_name)}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


@frappe.whitelist()
def get_default_template(reference_doctype):
    _check_access()
    return frappe.db.get_value("WAFD Document Template", {"reference_doctype": reference_doctype, "enabled": 1, "is_default": 1}, "name") or frappe.db.get_value("WAFD Document Template", {"reference_doctype": reference_doctype, "enabled": 1}, "name")
