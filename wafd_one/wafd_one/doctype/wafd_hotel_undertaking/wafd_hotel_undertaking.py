import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime
from frappe.utils.pdf import get_pdf

PRINT_FORMAT = "تعهد والتزام إعاشة — WAFD"
DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner"

class WAFDHotelUndertaking(Document):
    def validate(self):
        self._fill_linked_data()
        self._fill_meals()
        self.supply_location = self._get_hotel_name() or self.supply_location
        self.company_logo = self.company_logo or "/assets/wafd_one/images/wafd-almadinah-official.png"
        self._validate_dates_and_count(draft_safe=True)

    def before_submit(self):
        self._validate_for_issue()
        self.status = "معتمد / Approved"

    def on_cancel(self):
        self.db_set("status", "ملغي / Cancelled", update_modified=False)

    def _validate_dates_and_count(self, draft_safe=False):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw(_("تاريخ النهاية يجب أن يكون بعد تاريخ البداية / End date must be after start date"))
        if self.beneficiary_count and cint(self.beneficiary_count) < 0:
            frappe.throw(_("عدد المستفيدين لا يمكن أن يكون سالباً / Beneficiary count cannot be negative"))
        if not draft_safe and cint(self.beneficiary_count) <= 0:
            frappe.throw(_("عدد المستفيدين يجب أن يكون أكبر من صفر / Beneficiary count must be greater than zero"))

    def _fill_linked_data(self):
        """The undertaking is intentionally linked only to the selected hotel.

        Client/company, dates, meals, beneficiary count and nationality remain
        explicit user inputs so this optional document never changes operational
        workflows or inherits unrelated project data.
        """
        if self.hotel:
            self.supply_location = self._get_hotel_name() or self.supply_location

    def _fill_meals(self):
        if not self.meal_types:
            self.meal_types = DEFAULT_MEALS

    def _get_hotel_name(self):
        if not self.hotel:
            return None
        return frappe.db.get_value("WAFD Hotel", self.hotel, "hotel_name") or self.hotel

    def _validate_for_issue(self):
        self._fill_linked_data(); self._fill_meals()
        required = {
            "hotel": "الفندق / Hotel",
            "beneficiary_count": "عدد المستفيدين / Beneficiary Count", "meal_types": "الوجبات / Meals",
            "start_date": "تاريخ البداية / Start Date", "end_date": "تاريخ النهاية / End Date",
        }
        missing=[label for field,label in required.items() if not self.get(field)]
        if missing:
            frappe.throw(_("لا يمكن إصدار التعهد قبل استكمال الحقول التالية:<br>{0}").format("<br>".join(f"- {x}" for x in missing)), title=_("بيانات التعهد غير مكتملة"))
        self._validate_dates_and_count(draft_safe=False)

@frappe.whitelist()
def load_linked_data(name):
    doc=frappe.get_doc("WAFD Hotel Undertaking", name); doc.check_permission("write")
    doc._fill_linked_data(); doc._fill_meals(); doc.supply_location=doc._get_hotel_name() or doc.supply_location
    doc.save(); return doc.as_dict()

@frappe.whitelist()
def approve_and_generate_pdf(name):
    doc=frappe.get_doc("WAFD Hotel Undertaking", name); doc.check_permission("write")
    doc._validate_for_issue()
    if doc.docstatus == 0:
        doc.save(); doc.submit(); doc.reload()
    if doc.docstatus == 2:
        frappe.throw(_("لا يمكن إصدار PDF لتعهد ملغي / Cannot generate a PDF for a cancelled undertaking"))
    html = frappe.get_print("WAFD Hotel Undertaking", doc.name, print_format=PRINT_FORMAT, as_pdf=False, no_letterhead=1)
    pdf_content = get_pdf(html, options={
        "page-size": "A4", "margin-top": "0mm", "margin-right": "0mm",
        "margin-bottom": "0mm", "margin-left": "0mm",
        "disable-smart-shrinking": "", "print-media-type": "", "encoding": "UTF-8",
    })
    filename=f"{doc.name}.pdf"
    existing=frappe.db.get_value("File", {"attached_to_doctype":doc.doctype,"attached_to_name":doc.name,"file_name":filename}, "name")
    if existing: frappe.delete_doc("File", existing, ignore_permissions=True, force=True)
    file_doc=frappe.get_doc({"doctype":"File","file_name":filename,"attached_to_doctype":doc.doctype,"attached_to_name":doc.name,"is_private":1,"content":pdf_content}).insert(ignore_permissions=True)
    generated_on=now_datetime()
    frappe.db.set_value(doc.doctype, doc.name, {"generated_pdf":file_doc.file_url,"generated_on":generated_on,"generated_by":frappe.session.user,"status":"تم إصدار PDF / PDF Generated"}, update_modified=True)
    return {"file_url":file_doc.file_url,"file_name":filename}
