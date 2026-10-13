import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class WAFDQualityInspection(Document):
    def validate(self):
        failures = []
        if not frappe.db.exists("WAFD Production Batch", self.production_batch):
            frappe.throw("دفعة الإنتاج غير موجودة / Production batch not found")
        if self.minimum_temperature and flt(self.temperature) < flt(self.minimum_temperature): failures.append("درجة الحرارة أقل من الحد الأدنى / Temperature below minimum")
        if self.maximum_temperature and flt(self.temperature) > flt(self.maximum_temperature): failures.append("درجة الحرارة أعلى من الحد الأعلى / Temperature above maximum")
        if self.target_weight and self.portion_weight:
            tolerance = flt(self.target_weight) * flt(self.weight_tolerance or 5) / 100
            if abs(flt(self.portion_weight) - flt(self.target_weight)) > tolerance: failures.append("وزن العينة خارج الهامش / Sample weight outside tolerance")
        for fieldname, label in (("appearance","المظهر"),("taste","الطعم"),("packaging","التغليف")):
            if self.get(fieldname) == "غير مقبول / Unacceptable": failures.append(f"{label} غير مقبول")
        if not self.label_verified or not self.production_date_verified or not self.expiry_date_verified: failures.append("التحقق من الملصق والتواريخ غير مكتمل / Label and date checks are incomplete")
        if not self.menu_verified: failures.append("المنيو غير مطابق / Menu not verified")
        if not self.hygiene_verified: failures.append("فحص النظافة غير مكتمل / Hygiene check incomplete")
        if failures and self.result == "ناجح / Passed": frappe.throw("لا يمكن اعتماد الفحص ناجحًا:<br>" + "<br>".join(failures))
        if self.result in ("مرفوض / Rejected", "مشروط / Conditional") and not self.corrective_action: frappe.throw("الإجراء التصحيحي مطلوب / Corrective action is required")
        if self.result == "مرفوض / Rejected" and not self.rejection_photo: frappe.throw("صورة الملاحظة مطلوبة عند الرفض / Rejection photo is required")
        self.decision_time = self.decision_time or now_datetime()

    def on_update(self):
        frappe.db.set_value("WAFD Production Batch", self.production_batch, "quality_status", self.result or "لم يفحص / Not Inspected", update_modified=False)
        if self.result == "مرفوض / Rejected":
            frappe.db.set_value("WAFD Production Batch", self.production_batch, {"status": "موقوف / Stopped", "food_safety_release_status": "مرفوض / Rejected"}, update_modified=False)
        elif self.result == "مشروط / Conditional":
            frappe.db.set_value("WAFD Production Batch", self.production_batch, "food_safety_release_status", "موقوف / On Hold", update_modified=False)
