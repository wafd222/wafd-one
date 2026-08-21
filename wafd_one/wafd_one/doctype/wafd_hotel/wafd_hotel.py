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


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def hotel_link_query(doctype, txt, searchfield, start, page_len, filters):
    txt = (txt or "").strip()
    like = f"%{txt}%"
    return frappe.db.sql(
        """select name, hotel_name, coalesce(hotel_name_en, ''), coalesce(central_map_number, ''), coalesce(district, '')
           from `tabWAFD Hotel`
           where status = 'نشط / Active'
             and (proximity_band in ('داخل المنطقة المركزية / Central Area', 'قريب من المنطقة المركزية حتى 2 كم / Near Central up to 2 km')
                  or zone_type = 'المنطقة المركزية / Central Zone')
             and (%(txt)s = '' or hotel_name like %(like)s or hotel_name_en like %(like)s or central_map_number like %(like)s)
           order by case when central_map_number is null or central_map_number='' then 1 else 0 end, cast(central_map_number as unsigned), hotel_name
           limit %(start)s, %(page_len)s""",
        {"txt": txt, "like": like, "start": int(start), "page_len": int(page_len)},
    )


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def hotel_link_query_for_undertaking(doctype, txt, searchfield, start, page_len, filters):
    """All active hotels are selectable for undertakings, including newly added hotels."""
    txt = (txt or "").strip()
    like = f"%{txt}%"
    return frappe.db.sql(
        """select name, hotel_name, coalesce(hotel_name_en, ''), coalesce(district, ''), coalesce(city, '')
           from `tabWAFD Hotel`
           where status = 'نشط / Active'
             and (%(txt)s = '' or hotel_name like %(like)s or hotel_name_en like %(like)s or district like %(like)s)
           order by hotel_name
           limit %(start)s, %(page_len)s""",
        {"txt": txt, "like": like, "start": int(start), "page_len": int(page_len)},
    )


@frappe.whitelist()
def create_hotel_for_undertaking(hotel_name, hotel_name_en=None, district=None):
    """Create a minimal hotel from the undertaking screen without granting edit rights."""
    roles = set(frappe.get_roles())
    allowed = {"System Manager", "WAFD Operations Manager", "WAFD Undertaking Officer"}
    if not roles.intersection(allowed):
        frappe.throw(frappe._("You are not permitted to add hotels."), frappe.PermissionError)
    hotel_name = (hotel_name or "").strip()
    if not hotel_name:
        frappe.throw(frappe._("اسم الفندق مطلوب / Hotel name is required"))
    existing = frappe.db.get_value("WAFD Hotel", {"hotel_name": hotel_name}, "name")
    if existing:
        return {"name": existing, "created": False}
    doc = frappe.get_doc({
        "doctype": "WAFD Hotel",
        "hotel_name": hotel_name,
        "hotel_name_en": (hotel_name_en or "").strip(),
        "district": (district or "").strip(),
        "city": "المدينة المنورة",
        "status": "نشط / Active",
        "verification_status": "يحتاج مراجعة / Needs Review",
    })
    doc.insert(ignore_permissions=False)
    return {"name": doc.name, "created": True}
