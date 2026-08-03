import json
import frappe
from frappe.model.document import Document

class WAFDDocumentTemplate(Document):
    def validate(self):
        self._validate_canvas()
        self._enforce_single_default()
        self.revision = max(int(self.revision or 0), 0) + 1
        from wafd_one.document_studio import compile_template
        self.compiled_html = compile_template(self)

    def _validate_canvas(self):
        if not self.canvas_json:
            self.canvas_json = json.dumps({"version": 1, "blocks": []}, ensure_ascii=False)
            return
        try:
            value = json.loads(self.canvas_json)
        except Exception:
            frappe.throw(frappe._("Canvas JSON is invalid."))
        if not isinstance(value, dict) or not isinstance(value.get("blocks", []), list):
            frappe.throw(frappe._("Canvas JSON must contain a blocks list."))

    def _enforce_single_default(self):
        if self.is_default and self.reference_doctype:
            frappe.db.set_value(
                "WAFD Document Template",
                {"reference_doctype": self.reference_doctype, "is_default": 1, "name": ["!=", self.name]},
                "is_default", 0, update_modified=False,
            )
