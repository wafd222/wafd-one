import frappe
from frappe import _
from frappe.model.document import Document

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

class WAFDPrintSettings(Document):
    def validate(self):
        self.watermark_opacity = max(0, min(float(self.watermark_opacity or 0), 1))
        for field in ("margin_top", "margin_bottom", "margin_right", "margin_left"):
            if float(self.get(field) or 0) < 0:
                frappe.throw(_("الهوامش لا يمكن أن تكون سالبة / Margins cannot be negative"))
        base_size = int(self.base_font_size or 0)
        title_size = int(self.title_font_size or 0)
        line_width = int(self.header_line_width or 0)
        if base_size < 8 or base_size > 30:
            frappe.throw(_("حجم النص يجب أن يكون بين 8 و30 / Font size must be between 8 and 30"))
        if title_size < 10 or title_size > 48:
            frappe.throw(_("حجم العنوان يجب أن يكون بين 10 و48 / Title size must be between 10 and 48"))
        if line_width < 0 or line_width > 30:
            frappe.throw(_("سماكة خط الرأس يجب أن تكون بين 0 و30 / Header line width must be between 0 and 30"))
        for field in ("margin_top", "margin_bottom", "margin_right", "margin_left"):
            if float(self.get(field) or 0) > 60:
                frappe.throw(_("الهوامش يجب ألا تتجاوز 60 مم / Margins cannot exceed 60 mm"))

@frappe.whitelist()
def reset_defaults():
    doc = frappe.get_single("WAFD Print Settings")
    doc.check_permission("write")
    for key, value in DEFAULTS.items():
        doc.set(key, value)
    doc.save()
    return doc.as_dict()
