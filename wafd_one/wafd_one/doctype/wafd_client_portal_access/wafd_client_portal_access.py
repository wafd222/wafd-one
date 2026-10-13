import frappe
from frappe.model.document import Document


class WAFDClientPortalAccess(Document):
    def validate(self):
        if not self.user or self.user == "Guest":
            frappe.throw("حدد مستخدم البوابة / Select a portal user")
        if not self.project:
            frappe.throw("حدد المشروع / Select a project")
        self.entity_name = (self.entity_name or "").strip()
        duplicate = frappe.db.exists(
            "WAFD Client Portal Access",
            {
                "user": self.user,
                "project": self.project,
                "name": ["!=", self.name or ""],
            },
        )
        if duplicate:
            frappe.throw("هذا المستخدم مرتبط بالفعل بهذا المشروع / User is already linked to this project")
