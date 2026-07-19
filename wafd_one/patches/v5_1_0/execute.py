import frappe


DEFAULTS = {
    "company_logo": "/assets/wafd_one/images/wafd-almadinah-official.png",
    "document_title": "تعهد والتزام إعاشة",
    "primary_color": "#AA8C27",
    "text_color": "#111111",
    "muted_color": "#6C6C6C",
    "font_family": "Tahoma",
    "base_font_size": 13,
    "title_font_size": 18,
    "paper_size": "A4",
    "orientation": "Portrait",
    "margin_top": 12,
    "margin_bottom": 13,
    "margin_right": 14,
    "margin_left": 14,
    "header_line_width": 8,
    "intro_text": "الحمد لله، والصلاة والسلام على رسول الله، وبعد:",
    "agreement_text": "فقد تم الاتفاق على هذا التعهد بين:",
    "closing_text": "نأمل من إدارة الفندق التعاون والتواصل معنا بشكل مباشر عند وجود أي ملاحظات ليتم تلافيها فورًا من قبلنا، وعرض هذا التعهد للجهات المسؤولة عند الحاجة.",
    "footer_text": "حي الملك فهد، المدينة المنورة",
    "show_watermark": 1,
    "watermark_text": "وفد",
    "watermark_opacity": 0.05,
    "signatory_name": "نزار نذير بن ظفر",
    "signatory_title": "المدير العام",
    "show_company_details": 1,
    "show_reference_number": 1,
    "show_second_party_signature": 0,
}


def _is_unset(value):
    """Only initialize genuinely empty values; preserve intentional 0/unchecked settings."""
    return value is None or (isinstance(value, str) and not value.strip())


def execute():
    if not frappe.db.exists("DocType", "WAFD Print Settings"):
        return

    doc = frappe.get_single("WAFD Print Settings")
    changed = False
    for field, value in DEFAULTS.items():
        if _is_unset(doc.get(field)):
            doc.set(field, value)
            changed = True

    if changed:
        doc.save(ignore_permissions=True)
