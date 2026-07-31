import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, now_datetime

class WAFDCCPCheck(Document):
    def validate(self):
        if not frappe.db.exists("WAFD Production Batch", self.production_batch):
            frappe.throw("دفعة الإنتاج غير موجودة / Production batch not found")
        if get_datetime(self.check_time) > now_datetime():
            frappe.throw("وقت الفحص لا يمكن أن يكون مستقبليًا / Check time cannot be in the future")
        if self.minimum_limit is not None and self.maximum_limit is not None and flt(self.minimum_limit) > flt(self.maximum_limit):
            frappe.throw("الحد الأدنى لا يمكن أن يتجاوز الحد الأعلى / Minimum limit cannot exceed maximum limit")
        self._apply_default_limits()
        compliant = True
        if self.minimum_limit is not None and flt(self.measured_value) < flt(self.minimum_limit):
            compliant = False
        if self.maximum_limit is not None and flt(self.measured_value) > flt(self.maximum_limit):
            compliant = False
        self.compliance_status = "مطابق / Compliant" if compliant else "غير مطابق / Noncompliant"
        if not compliant:
            if not self.deviation_details or not self.corrective_action:
                frappe.throw("تفاصيل الانحراف والإجراء التصحيحي مطلوبة / Deviation details and corrective action are required")
            settings = frappe.get_single("WAFD Food Safety Settings")
            if settings.require_rejection_photo and not self.evidence_photo:
                frappe.throw("صورة الدليل مطلوبة عند عدم المطابقة / Evidence photo is required for nonconformance")
        if self.verification_status == "تم التحقق / Verified":
            if not self.verified_by:
                self.verified_by = frappe.session.user
            if not self.verified_on:
                self.verified_on = now_datetime()

    def _apply_default_limits(self):
        settings = frappe.get_single("WAFD Food Safety Settings")
        if self.ccp_type == "الطهي / Cooking" and self.minimum_limit is None:
            self.minimum_limit = settings.minimum_cooking_temperature
        elif self.ccp_type == "الحفظ الساخن / Hot Holding" and self.minimum_limit is None:
            self.minimum_limit = settings.minimum_hot_holding_temperature
        elif self.ccp_type == "الحفظ البارد / Cold Holding" and self.maximum_limit is None:
            self.maximum_limit = settings.maximum_cold_holding_temperature

    def before_save(self):
        if self.is_new():
            return
        previous = self.get_doc_before_save()
        if previous and previous.verification_status == "تم التحقق / Verified":
            protected = ("production_batch", "ccp_type", "check_time", "measured_value", "unit", "minimum_limit", "maximum_limit", "compliance_status", "deviation_details", "corrective_action")
            changed = [field for field in protected if self.get(field) != previous.get(field)]
            if changed:
                frappe.throw("لا يمكن تعديل قياس تم التحقق منه / A verified CCP check cannot be modified")

    def before_delete(self):
        if self.verification_status == "تم التحقق / Verified":
            frappe.throw("لا يمكن حذف فحص تم التحقق منه / A verified CCP check cannot be deleted")
