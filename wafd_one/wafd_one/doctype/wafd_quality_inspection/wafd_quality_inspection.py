import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WafdQualityInspection(Document):
    def validate(self):
        failures = []
        if self.minimum_temperature and flt(self.temperature) < flt(self.minimum_temperature):
            failures.append("درجة الحرارة أقل من الحد الأدنى / Temperature below minimum")
        if self.maximum_temperature and flt(self.temperature) > flt(self.maximum_temperature):
            failures.append("درجة الحرارة أعلى من الحد الأعلى / Temperature above maximum")
        if self.target_weight and self.portion_weight:
            tolerance = flt(self.target_weight) * flt(self.weight_tolerance or 5) / 100
            if abs(flt(self.portion_weight) - flt(self.target_weight)) > tolerance:
                failures.append("وزن العينة خارج الهامش / Sample weight outside tolerance")
        for field, label in (("appearance", "المظهر"), ("taste", "الطعم"), ("packaging", "التغليف")):
            if self.get(field) == "غير مقبول / Unacceptable":
                failures.append(f"{label} غير مقبول")
        if not self.label_verified or not self.production_date_verified or not self.expiry_date_verified:
            failures.append("التحقق من الملصق والتواريخ غير مكتمل / Label and date checks are incomplete")
        if failures and self.result == "ناجح / Passed":
            frappe.throw("لا يمكن اعتماد الفحص ناجحًا:<br>" + "<br>".join(failures))
        if self.result == "مرفوض / Rejected" and not self.corrective_action:
            frappe.throw("الإجراء التصحيحي مطلوب عند الرفض / Corrective action is required when rejected")

    def on_update(self):
        if not self.production_batch:
            return
        frappe.db.set_value("WAFD Production Batch", self.production_batch, "quality_status", self.result or "لم يفحص / Not Inspected", update_modified=False)
        if self.result == "مرفوض / Rejected":
            frappe.db.set_value("WAFD Production Batch", self.production_batch, "status", "موقوف / Stopped", update_modified=False)
