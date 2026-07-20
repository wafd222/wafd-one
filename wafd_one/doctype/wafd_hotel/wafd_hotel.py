import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class WAFDHotel(Document):
    def validate(self):
        self.hotel_name = (self.hotel_name or "").strip()
        if not self.hotel_name:
            frappe.throw("اسم الفندق مطلوب / Hotel name is required")
        if self.latitude is not None and not (-90 <= float(self.latitude) <= 90):
            frappe.throw("خط العرض يجب أن يكون بين -90 و90 / Latitude must be between -90 and 90")
        if self.longitude is not None and not (-180 <= float(self.longitude) <= 180):
            frappe.throw("خط الطول يجب أن يكون بين -180 و180 / Longitude must be between -180 and 180")
        if self.last_verified_on and getdate(self.last_verified_on) > getdate(nowdate()):
            frappe.throw("تاريخ التحقق لا يمكن أن يكون في المستقبل / Verification date cannot be in the future")
        if self.listing_checked_on and getdate(self.listing_checked_on) > getdate(nowdate()):
            frappe.throw("تاريخ فحص منصات الحجز لا يمكن أن يكون في المستقبل / Listing check date cannot be in the future")
        if self.zone_type != "المنطقة المركزية / Central Zone":
            self.central_map_number = None
            self.central_sector = None
