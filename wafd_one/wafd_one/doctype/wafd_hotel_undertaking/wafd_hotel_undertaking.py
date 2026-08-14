import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

PRINT_FORMAT = "تعهد والتزام إعاشة — WAFD"
DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner"
DEFAULT_SIGNATORY = "نزار بن نذير بن ظفر"

class WAFDHotelUndertaking(Document):
    def validate(self):
        self._fill_linked_data()
        self._fill_meals()
        self._fill_company_approval_assets()
        self.supply_location = self._get_hotel_name() or self.supply_location
        self.company_logo = self.company_logo or "/assets/wafd_one/images/wafd-almadinah-official.png"
        self.authorized_signatory = self.authorized_signatory or DEFAULT_SIGNATORY
        self._validate_dates_and_count(draft_safe=True)

    def after_insert(self):
        self._save_beneficiary_reference_if_requested()

    def on_update(self):
        if not self.flags.in_insert:
            self._save_beneficiary_reference_if_requested()

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
        if self.project:
            project = frappe.db.get_value(
                "WAFD Catering Project", self.project,
                ["contract", "mission", "primary_hotel", "beneficiary_count", "start_date", "end_date"],
                as_dict=True,
            )
            if project:
                self.contract = self.contract or project.contract
                self.mission = self.mission or project.mission
                self.hotel = self.hotel or project.primary_hotel
                self.beneficiary_count = self.beneficiary_count or project.beneficiary_count
                self.start_date = self.start_date or project.start_date
                self.end_date = self.end_date or project.end_date
        if self.mission:
            mission = frappe.db.get_value(
                "WAFD Mission", self.mission,
                ["mission_name", "official_name", "country"], as_dict=True,
            )
            if mission:
                self.second_party_name = self.second_party_name or mission.official_name or mission.mission_name
                self.party_nationality = self.party_nationality or mission.country
                self.nationality = self.nationality or mission.country
        if self.saved_beneficiary:
            ref = frappe.db.get_value(
                "WAFD Undertaking Beneficiary", self.saved_beneficiary,
                ["beneficiary_name", "identity_number", "nationality", "representative_name"], as_dict=True
            )
            if ref:
                self.second_party_name = self.second_party_name or ref.beneficiary_name
                self.second_party_cr = self.second_party_cr or ref.identity_number
                self.party_nationality = self.party_nationality or ref.nationality
                self.second_party_representative = self.second_party_representative or ref.representative_name
        if self.hotel:
            self.supply_location = self._get_hotel_name() or self.supply_location

    def _fill_meals(self):
        if not self.meal_types:
            self.meal_types = DEFAULT_MEALS

    def _fill_company_approval_assets(self):
        if not frappe.db.exists("DocType", "WAFD Print Settings"):
            return
        settings = frappe.get_single("WAFD Print Settings")
        if not self.signature_image and settings.default_signature:
            self.signature_image = settings.default_signature
        if not self.company_stamp and settings.default_stamp:
            self.company_stamp = settings.default_stamp
        if self.include_signature is None:
            self.include_signature = 1
        if self.include_stamp is None:
            self.include_stamp = 1

    def _save_beneficiary_reference_if_requested(self):
        if not cint(self.save_beneficiary_reference) or self.project or not self.second_party_name:
            return
        name = self.second_party_name.strip()
        existing = frappe.db.exists("WAFD Undertaking Beneficiary", {"beneficiary_name": name})
        values = {
            "identity_number": self.second_party_cr,
            "nationality": self.party_nationality,
            "representative_name": self.second_party_representative,
            "disabled": 0,
        }
        if existing:
            frappe.db.set_value("WAFD Undertaking Beneficiary", existing, values, update_modified=True)
            ref_name = existing
        else:
            ref = frappe.get_doc({"doctype":"WAFD Undertaking Beneficiary", "beneficiary_name":name, **values})
            ref.insert(ignore_permissions=True)
            ref_name = ref.name
        if self.saved_beneficiary != ref_name:
            frappe.db.set_value(self.doctype, self.name, "saved_beneficiary", ref_name, update_modified=False)
            self.saved_beneficiary = ref_name

    def _get_hotel_name(self):
        if not self.hotel:
            return None
        return frappe.db.get_value("WAFD Hotel", self.hotel, "hotel_name") or self.hotel

    def _validate_for_issue(self):
        self._fill_linked_data(); self._fill_meals(); self._fill_company_approval_assets()
        required = {
            "hotel": "الفندق / Hotel", "second_party_name": "اسم المستفيد / Beneficiary Name",
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
    doc._fill_linked_data(); doc._fill_meals(); doc._fill_company_approval_assets(); doc.supply_location=doc._get_hotel_name() or doc.supply_location
    doc.save(); return doc.as_dict()

@frappe.whitelist()
def get_saved_beneficiary(name):
    if not name:
        return {}
    return frappe.db.get_value("WAFD Undertaking Beneficiary", name,
        ["beneficiary_name", "identity_number", "nationality", "representative_name"], as_dict=True) or {}

@frappe.whitelist()
def approve_and_generate_pdf(name):
    doc=frappe.get_doc("WAFD Hotel Undertaking", name); doc.check_permission("write")
    doc._validate_for_issue()
    if doc.docstatus == 0:
        doc.save(); doc.submit(); doc.reload()
    if doc.docstatus == 2:
        frappe.throw(_("لا يمكن إصدار PDF لتعهد ملغي / Cannot generate a PDF for a cancelled undertaking"))
    from wafd_one.document_studio import get_default_template, render_pdf_bytes
    template_name = get_default_template("WAFD Hotel Undertaking")
    if not template_name:
        frappe.throw(_("لا يوجد قالب تعهد مفعل / No active undertaking template was found"))
    pdf_content = render_pdf_bytes(template_name, doc.doctype, doc.name)
    filename=f"{doc.name}.pdf"
    existing=frappe.db.get_value("File", {"attached_to_doctype":doc.doctype,"attached_to_name":doc.name,"file_name":filename}, "name")
    if existing: frappe.delete_doc("File", existing, ignore_permissions=True, force=True)
    file_doc=frappe.get_doc({"doctype":"File","file_name":filename,"attached_to_doctype":doc.doctype,"attached_to_name":doc.name,"is_private":1,"content":pdf_content}).insert(ignore_permissions=True)
    generated_on=now_datetime()
    frappe.db.set_value(doc.doctype, doc.name, {"generated_pdf":file_doc.file_url,"generated_on":generated_on,"generated_by":frappe.session.user,"status":"تم إصدار PDF / PDF Generated"}, update_modified=True)
    return {"file_url":file_doc.file_url,"file_name":filename}
