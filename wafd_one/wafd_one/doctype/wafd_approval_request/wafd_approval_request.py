import json
import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

ALLOWED_REFERENCE_DOCTYPES = {
    "WAFD Contract", "WAFD Purchase Order", "WAFD Invoice", "WAFD Payment",
    "WAFD Project Cost", "WAFD Project Revenue",
}
FINAL_STATUSES = {"معتمد / Approved", "مرفوض / Rejected", "ملغي / Cancelled"}

class WAFDApprovalRequest(Document):
    def before_insert(self):
        self.requested_by = frappe.session.user
        self.requested_on = now_datetime()
        self.status = "بانتظار الاعتماد / Pending"
        self._load_reference_snapshot()

    def validate(self):
        if self.reference_doctype not in ALLOWED_REFERENCE_DOCTYPES:
            frappe.throw("نوع المستند غير مدعوم للموافقة / Unsupported approval reference")
        if not frappe.db.exists(self.reference_doctype, self.reference_name):
            frappe.throw("المستند المرجعي غير موجود / Referenced document does not exist")
        self._prevent_duplicate_pending()
        self._protect_decision()
        if self.status in {"مرفوض / Rejected", "ملغي / Cancelled"} and not (self.decision_notes or "").strip():
            frappe.throw("يجب تسجيل سبب الرفض أو الإلغاء / Rejection or cancellation reason is required")

    def _load_reference_snapshot(self):
        doc = frappe.get_doc(self.reference_doctype, self.reference_name)
        self.reference_title = doc.get_title() or doc.name
        from wafd_one.governance import get_document_amount, sanitized_snapshot
        self.amount = flt(get_document_amount(doc), 2)
        self.snapshot = json.dumps(sanitized_snapshot(doc), ensure_ascii=False, sort_keys=True, default=str)

    def _prevent_duplicate_pending(self):
        duplicate = frappe.db.exists("WAFD Approval Request", {
            "reference_doctype": self.reference_doctype,
            "reference_name": self.reference_name,
            "status": "بانتظار الاعتماد / Pending",
            "name": ("!=", self.name or ""),
        })
        if duplicate:
            frappe.throw("يوجد طلب اعتماد معلق لهذا المستند / A pending approval request already exists")

    def _protect_decision(self):
        if self.is_new():
            return
        previous = self.get_doc_before_save()
        if not previous:
            return
        identity_fields=("reference_doctype","reference_name","amount","requested_by","requested_on","snapshot")
        if any(self.get(f) != previous.get(f) for f in identity_fields):
            frappe.throw("لا يمكن تغيير مرجع أو لقطة طلب الاعتماد / Approval request reference and snapshot cannot be changed")
        if previous.status in FINAL_STATUSES:
            protected=("reference_doctype","reference_name","amount","status","requested_by","requested_on","decided_by","decided_on","snapshot")
            if any(self.get(f) != previous.get(f) for f in protected):
                frappe.throw("لا يمكن تعديل طلب اعتماد منتهي / A finalized approval request cannot be modified")
        if self.status != previous.status:
            if self.status not in FINAL_STATUSES:
                frappe.throw("انتقال حالة الاعتماد غير مسموح / Invalid approval status transition")
            settings = frappe.get_single("WAFD Governance Settings")
            approver_role = settings.approver_role or "WAFD Approver"
            roles = frappe.get_roles()
            if approver_role not in roles and "System Manager" not in roles:
                frappe.throw("ليست لديك صلاحية الاعتماد / You do not have approval permission")
            if settings.prevent_self_approval and self.requested_by == frappe.session.user:
                frappe.throw("لا يجوز لمقدم الطلب اعتماد طلبه / Requesters cannot approve their own request")
            self.decided_by = frappe.session.user
            self.decided_on = now_datetime()

    def on_trash(self):
        if self.status != "بانتظار الاعتماد / Pending":
            frappe.throw("لا يمكن حذف طلب اعتماد منتهي / A finalized approval request cannot be deleted")
