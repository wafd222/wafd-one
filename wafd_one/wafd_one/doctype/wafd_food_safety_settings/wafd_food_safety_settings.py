import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint

class WAFDFoodSafetySettings(Document):
    def validate(self):
        for fieldname in (
            "minimum_cooking_temperature",
            "minimum_hot_holding_temperature",
            "maximum_cold_holding_temperature",
        ):
            value = flt(self.get(fieldname))
            if value < -50 or value > 150:
                frappe.throw(f"قيمة الحرارة غير منطقية: {fieldname} / Invalid temperature limit")
        if cint(self.maximum_ambient_exposure_minutes) <= 0:
            frappe.throw("مدة التعرض يجب أن تكون أكبر من صفر / Ambient exposure time must be greater than zero")
        if flt(self.default_weight_tolerance) < 0 or flt(self.default_weight_tolerance) > 100:
            frappe.throw("هامش الوزن يجب أن يكون بين 0 و100 / Weight tolerance must be between 0 and 100")
