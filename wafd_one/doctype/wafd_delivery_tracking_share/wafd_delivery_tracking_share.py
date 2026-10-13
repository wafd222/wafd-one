from __future__ import annotations

import secrets

import frappe
from frappe.model.document import Document


class WAFDDeliveryTrackingShare(Document):
    def before_insert(self):
        self.share_token = self.share_token or secrets.token_urlsafe(32)
        self.created_by_user = self.created_by_user or frappe.session.user

    def validate(self):
        self.viewer_name = (self.viewer_name or "").strip()
        if not self.viewer_name:
            frappe.throw("اسم الشخص المستفيد مطلوب / Viewer name is required")

