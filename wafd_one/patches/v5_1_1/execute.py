import frappe


def execute():
    """Safely normalize legacy/partial print settings without overwriting user choices."""
    if not frappe.db.exists("DocType", "WAFD Print Settings"):
        return

    doc = frappe.get_single("WAFD Print Settings")
    changed = False

    safe_defaults = {
        "document_title": "تعهد والتزام إعاشة",
        "primary_color": "#AA8C27",
        "text_color": "#111111",
        "muted_color": "#6C6C6C",
        "font_family": "Tahoma",
        "paper_size": "A4",
        "orientation": "Portrait",
        "intro_text": "الحمد لله، والصلاة والسلام على رسول الله، وبعد:",
        "agreement_text": "فقد تم الاتفاق على هذا التعهد بين:",
    }
    for field, value in safe_defaults.items():
        current = doc.get(field)
        if current is None or (isinstance(current, str) and not current.strip()):
            doc.set(field, value)
            changed = True

    numeric_defaults = {
        "base_font_size": 13,
        "title_font_size": 18,
        "margin_top": 12,
        "margin_bottom": 13,
        "margin_right": 14,
        "margin_left": 14,
        "header_line_width": 8,
    }
    for field, value in numeric_defaults.items():
        if doc.get(field) is None:
            doc.set(field, value)
            changed = True

    if changed:
        doc.save(ignore_permissions=True)
