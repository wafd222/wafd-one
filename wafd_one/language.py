"""One account-level language choice for every WAFD ONE screen."""

import frappe
from frappe import _


SUPPORTED_LANGUAGES = {"ar", "en", "id", "ur", "hi", "bn", "fr", "ha", "sw", "uz"}


@frappe.whitelist()
def set_user_language(language):
    if frappe.session.user == "Guest":
        frappe.throw(_("سجل الدخول أولاً / Please sign in"), frappe.PermissionError)
    language = (language or "").strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        frappe.throw(_("لغة غير مدعومة / Unsupported language"))
    frappe.db.set_value("User", frappe.session.user, "language", language, update_modified=False)
    frappe.clear_cache(user=frappe.session.user)
    return {"language": language}
