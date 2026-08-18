import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

PRINT_FORMAT = "تعهد والتزام إعاشة — WAFD"
DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner"
DEFAULT_SIGNATORY = "نزار بن نذير بن ظفر"

PROTECTED_TEMPLATE_FIELDS = (
    "company_logo",
    "additional_terms",
    "authorized_signatory",
    "signatory_title",
    "include_signature",
    "include_stamp",
    "signature_image",
    "company_stamp",
)
UNDERTAKING_OFFICER_ROLE = "WAFD Undertaking Officer"
UNDERTAKING_TEMPLATE_ADMIN_ROLES = {"System Manager", "WAFD Operations Manager"}

class WAFDHotelUndertaking(Document):
    def _is_restricted_undertaking_officer(self):
        roles = set(frappe.get_roles(frappe.session.user))
        return UNDERTAKING_OFFICER_ROLE in roles and not (roles & UNDERTAKING_TEMPLATE_ADMIN_ROLES)

    def _protect_template_controlled_fields(self):
        """Prevent undertaking officers from changing company identity or template-controlled content.

        This is intentionally enforced server-side in addition to DocField permlevels/UI hiding.
        It protects against crafted API requests and future client-side regressions.
        """
        if not self._is_restricted_undertaking_officer():
            return

        if self.is_new():
            # Never trust protected values submitted by an officer on a new document.
            # They are re-populated from the management-controlled print/template settings.
            self.company_logo = ""
            self.additional_terms = ""
            self.authorized_signatory = ""
            self.signatory_title = ""
            self.include_signature = 1
            self.include_stamp = 1
            self.signature_image = ""
            self.company_stamp = ""
            return

        before = self.get_doc_before_save()
        if not before:
            return
        changed = []
        for fieldname in PROTECTED_TEMPLATE_FIELDS:
            old_value = before.get(fieldname)
            new_value = self.get(fieldname)
            if old_value != new_value:
                changed.append(fieldname)
            # Always restore the database value. Protected permlevel fields may be
            # absent from an officer's client payload, so rejecting on None would
            # incorrectly block ordinary beneficiary/data edits.
            self.set(fieldname, old_value)
        if changed:
            frappe.logger("wafd_one").warning(
                "Blocked protected undertaking field changes by %s on %s: %s",
                frappe.session.user, self.name, ", ".join(changed),
            )

    def before_insert(self):
        self.prepared_by_user = frappe.session.user
        self.prepared_by_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user

    def validate(self):
        self._protect_template_controlled_fields()
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
        self.approved_by_user = frappe.session.user
        self.approved_by_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
        self.approved_on = now_datetime()

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

    def _discover_uploaded_company_asset(self, kind):
        """Recover a previously uploaded company signature/stamp from Frappe File records.

        Older releases stored approval images in more than one place. Search only
        company print/template attachments and clearly named image files; never
        select an unrelated arbitrary attachment.
        """
        tokens = ("signature", "sign", "توقيع") if kind == "signature" else ("stamp", "seal", "ختم")
        candidates = []
        file_meta = frappe.get_meta("File")
        file_fields = ["file_url", "file_name", "creation"]
        if file_meta.has_field("attached_to_field"):
            file_fields.append("attached_to_field")
        # Highest confidence: files attached to the print settings/template doctypes.
        for attached_doctype in ("WAFD Print Settings", "WAFD Document Template"):
            if not frappe.db.exists("DocType", attached_doctype):
                continue
            rows = frappe.get_all(
                "File",
                filters={"attached_to_doctype": attached_doctype},
                fields=file_fields,
                order_by="creation desc",
                limit=100,
            )
            # Exact attachment-field matches win even when the uploaded filename
            # was something generic such as image.png.
            for row in rows:
                attached_field = (row.get("attached_to_field") or "").lower()
                expected = ("default_signature", "signature") if kind == "signature" else ("default_stamp", "stamp")
                if attached_field in expected and row.file_url:
                    return row.file_url
            candidates.extend(rows)
        # Compatibility fallback: old uploads may not have retained attachment metadata.
        rows = frappe.get_all(
            "File",
            filters={"is_folder": 0},
            fields=["file_url", "file_name", "creation"],
            order_by="creation desc",
            limit=250,
        )
        candidates.extend(rows)
        seen = set()
        for row in candidates:
            url = (row.file_url or "").strip()
            name = (row.file_name or "").lower().strip()
            key = (url, name)
            if not url or key in seen:
                continue
            seen.add(key)
            if not url.lower().split("?", 1)[0].endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            haystack = f"{name} {url.lower()}"
            if any(token in haystack for token in tokens):
                return url
        return ""

    def _fill_company_approval_assets(self):
        if not frappe.db.exists("DocType", "WAFD Print Settings"):
            return
        settings = frappe.get_single("WAFD Print Settings")
        default_signature = settings.default_signature or ""
        default_stamp = settings.default_stamp or ""
        # Older installations may have the uploaded assets stored on the
        # Document Studio template rather than Print Settings. Preserve them.
        if (not default_signature or not default_stamp) and frappe.db.exists("DocType", "WAFD Document Template"):
            template_name = frappe.db.get_value(
                "WAFD Document Template",
                {"reference_doctype": self.doctype, "enabled": 1, "is_default": 1},
                "name",
            ) or frappe.db.get_value("WAFD Document Template", {"reference_doctype": self.doctype, "enabled": 1}, "name")
            if template_name:
                template = frappe.get_doc("WAFD Document Template", template_name)
                default_signature = default_signature or (template.signature or "")
                default_stamp = default_stamp or (template.stamp or "")
        # A legacy template may still hold the original uploaded assets even if
        # the current default template was later regenerated.
        if frappe.db.exists("DocType", "WAFD Document Template"):
            if not default_signature:
                default_signature = frappe.db.get_value(
                    "WAFD Document Template",
                    {"reference_doctype": self.doctype, "signature": ["!=", ""]},
                    "signature",
                    order_by="modified desc",
                ) or ""
            if not default_stamp:
                default_stamp = frappe.db.get_value(
                    "WAFD Document Template",
                    {"reference_doctype": self.doctype, "stamp": ["!=", ""]},
                    "stamp",
                    order_by="modified desc",
                ) or ""
        if not default_signature:
            default_signature = self._discover_uploaded_company_asset("signature")
        if not default_stamp:
            default_stamp = self._discover_uploaded_company_asset("stamp")
        if not self.signature_image and default_signature:
            self.signature_image = default_signature
        if not self.company_stamp and default_stamp:
            self.company_stamp = default_stamp
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

def _persist_approval_assets(doc):
    """Persist default signature/stamp before a renderer reloads the document.

    Submitted legacy undertakings cannot be saved normally.  Rendering through
    Document Studio loads a fresh database copy, so assets filled only in memory
    disappear.  Persist only the missing approval assets/flags and never alter
    business data or submission state.
    """
    doc._fill_company_approval_assets()
    values = {}
    for fieldname in ("signature_image", "company_stamp"):
        value = doc.get(fieldname)
        if value and frappe.db.get_value(doc.doctype, doc.name, fieldname) != value:
            values[fieldname] = value
    for fieldname in ("include_signature", "include_stamp"):
        value = cint(doc.get(fieldname))
        current = frappe.db.get_value(doc.doctype, doc.name, fieldname)
        if current is None or cint(current) != value:
            values[fieldname] = value
    if values:
        frappe.db.set_value(doc.doctype, doc.name, values, update_modified=False)
    return values

@frappe.whitelist()
def approve_and_generate_pdf(name):
    source = frappe.get_doc("WAFD Hotel Undertaking", name)
    source.check_permission("write")

    # A cancelled Frappe document (docstatus=2) is immutable. Instead of leaving
    # the mobile action disabled, create a clean draft copy and issue that copy.
    if source.docstatus == 2:
        doc = frappe.copy_doc(source)
        doc.name = None
        doc.docstatus = 0
        doc.status = "مسودة / Draft"
        doc.generated_pdf = None
        doc.generated_on = None
        doc.generated_by = None
        doc.signature_image = source.signature_image or None
        doc.company_stamp = source.company_stamp or None
        doc._fill_company_approval_assets()
        doc.insert(ignore_permissions=False)
    else:
        doc = source

    doc._validate_for_issue()
    if doc.docstatus == 0:
        doc.save()
        doc.submit()
        doc.reload()
    _persist_approval_assets(doc)
    doc.reload()

    from wafd_one.document_studio import get_default_template, render_pdf_bytes
    template_name = get_default_template("WAFD Hotel Undertaking")
    if not template_name:
        frappe.throw(_("لا يوجد قالب تعهد مفعل / No active undertaking template was found"))
    pdf_content = render_pdf_bytes(template_name, doc.doctype, doc.name)
    filename = f"{doc.name}.pdf"
    existing = frappe.db.get_value("File", {
        "attached_to_doctype": doc.doctype,
        "attached_to_name": doc.name,
        "file_name": filename,
    }, "name")
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
    return {
        "file_url": file_doc.file_url,
        "file_name": filename,
        "docname": doc.name,
        "created_from_cancelled": source.docstatus == 2,
    }

