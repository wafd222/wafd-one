import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


PRINT_FORMAT = "تعهد والتزام إعاشة — WAFD"


class WAFDHotelUndertaking(Document):
    def validate(self):
        self._validate_dates_and_count()
        self._fill_linked_data()
        self.supply_location = self._get_hotel_name() or self.supply_location

    def before_submit(self):
        self.status = "معتمد / Approved"

    def on_cancel(self):
        self.db_set("status", "ملغي / Cancelled", update_modified=False)

    def _validate_dates_and_count(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw(_("تاريخ النهاية يجب أن يكون بعد تاريخ البداية / End date must be after start date"))
        if cint(self.beneficiary_count) <= 0:
            frappe.throw(_("عدد المستفيدين يجب أن يكون أكبر من صفر / Beneficiary count must be greater than zero"))

    def _fill_linked_data(self):
        if self.project:
            project = frappe.get_doc("WAFD Catering Project", self.project)
            self.contract = self.contract or project.contract
            self.mission = self.mission or project.mission
            self.hotel = self.hotel or project.primary_hotel
            self.beneficiary_count = self.beneficiary_count or project.beneficiary_count
            self.start_date = self.start_date or project.start_date
            self.end_date = self.end_date or project.end_date
        if self.contract:
            contract = frappe.get_doc("WAFD Contract", self.contract)
            self.mission = self.mission or contract.mission
            self.hotel = self.hotel or contract.hotel
            self.beneficiary_count = self.beneficiary_count or contract.beneficiary_count
            self.start_date = self.start_date or contract.start_date
            self.end_date = self.end_date or contract.end_date
            self.second_party_name = self.second_party_name or contract.contract_title
        if self.mission and not self.nationality:
            mission = frappe.get_doc("WAFD Mission", self.mission)
            self.nationality = mission.country or ""
            self.second_party_name = self.second_party_name or mission.mission_name

    def _get_hotel_name(self):
        if not self.hotel:
            return None
        return frappe.db.get_value("WAFD Hotel", self.hotel, "hotel_name") or self.hotel


@frappe.whitelist()
def load_linked_data(name):
    doc = frappe.get_doc("WAFD Hotel Undertaking", name)
    doc.check_permission("write")
    doc._fill_linked_data()
    doc.supply_location = doc._get_hotel_name() or doc.supply_location
    doc.save()
    return doc.as_dict()


@frappe.whitelist()
def approve_and_generate_pdf(name):
    doc = frappe.get_doc("WAFD Hotel Undertaking", name)
    doc.check_permission("write")
    if doc.docstatus == 0:
        doc.submit()
        doc.reload()
    if doc.docstatus == 2:
        frappe.throw(_("لا يمكن إصدار PDF لتعهد ملغي / Cannot generate a PDF for a cancelled undertaking"))

    pdf_content = frappe.get_print(
        "WAFD Hotel Undertaking",
        doc.name,
        print_format=PRINT_FORMAT,
        as_pdf=True,
    )
    filename = f"{doc.name}.pdf"
    existing = frappe.db.get_value(
        "File",
        {"attached_to_doctype": doc.doctype, "attached_to_name": doc.name, "file_name": filename},
        "name",
    )
    if existing:
        frappe.delete_doc("File", existing, ignore_permissions=True, force=True)

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "attached_to_doctype": doc.doctype,
        "attached_to_name": doc.name,
        "is_private": 1,
        "content": pdf_content,
    }).insert(ignore_permissions=True)

    generated_on = now_datetime()
    frappe.db.set_value(doc.doctype, doc.name, {
        "generated_pdf": file_doc.file_url,
        "generated_on": generated_on,
        "generated_by": frappe.session.user,
        "status": "تم إصدار PDF / PDF Generated",
    }, update_modified=True)
    return {"file_url": file_doc.file_url, "file_name": filename}
