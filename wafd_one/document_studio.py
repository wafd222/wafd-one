import json
from html import escape
import frappe
from frappe.utils.pdf import get_pdf

ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Project Manager"}
ALLOWED_PAGE_SIZES = {"A4", "A5", "Letter"}
ALLOWED_ORIENTATIONS = {"Portrait", "Landscape"}
ALLOWED_DIRECTIONS = {"RTL", "LTR"}
DANGEROUS_MARKUP = (
    "<script", "</style", "javascript:", "vbscript:", "expression(",
    "@import", "onerror=", "onload=", "onclick=", "onmouseover=",
)


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
        base = f"position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;z-index:{z};overflow:hidden;{style}"
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
    payload = json.loads(canvas_json)
    if not isinstance(payload, dict) or not isinstance(payload.get("blocks", []), list):
        frappe.throw(frappe._("Invalid designer payload."))
    if len(payload.get("blocks", [])) > 250:
        frappe.throw(frappe._("A template cannot contain more than 250 elements."))
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
