import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

WAFD_MENU = "منيو وفد المدينة / WAFD Menu"
CUSTOMER_MENU = "حسب طلب الشركة / Customer Requested Menu"
APPROVAL_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Approver"}
ALLOWED_STATUSES = {
    "مسودة / Draft", "بانتظار الاعتماد / Pending Approval", "معتمد / Approved",
    "أرسل للعميل / Sent", "مقبول / Accepted", "مرفوض / Rejected",
    "منتهي / Expired", "ملغي / Cancelled",
}
STATUS_TRANSITIONS = {
    "معتمد / Approved": {"أرسل للعميل / Sent", "ملغي / Cancelled"},
    "أرسل للعميل / Sent": {"مقبول / Accepted", "مرفوض / Rejected", "ملغي / Cancelled"},
    "مقبول / Accepted": {"ملغي / Cancelled"},
}


class WAFDQuotation(Document):
    def before_insert(self):
        self.prepared_by_user = frappe.session.user
        self.prepared_by_name = _user_name(frappe.session.user)
        self.status = "مسودة / Draft"
        self.quotation_date = self.quotation_date or today()
        self.valid_until = self.valid_until or add_days(self.quotation_date, 15)

    def validate(self):
        self._protect_status()
        self._fill_customer()
        self._fill_company_assets()
        self._calculate(validate_rows=False)
        self._validate_dates()
        if self.status not in ALLOWED_STATUSES:
            frappe.throw(_("حالة عرض السعر غير صحيحة / Invalid quotation status"))

    def _protect_status(self):
        if self.is_new() or self.flags.get("quotation_status_change"):
            return
        before = self.get_doc_before_save()
        if before and before.status != self.status:
            frappe.throw(_("غيّر حالة عرض السعر من أزرار الإجراءات المعتمدة / Change quotation status only with the approved action buttons"), frappe.PermissionError)

    def _fill_customer(self):
        if not self.customer_company:
            return
        row = frappe.db.get_value(
            "WAFD Mission", self.customer_company,
            ["mission_name", "official_name", "contact_person", "mobile", "email", "address"],
            as_dict=True,
        )
        if not row:
            return
        self.customer_name = self.customer_name or row.official_name or row.mission_name
        self.contact_person = self.contact_person or row.contact_person
        self.customer_phone = self.customer_phone or row.mobile
        self.customer_email = self.customer_email or row.email
        self.supply_location = self.supply_location or row.address

    def _validate_dates(self):
        if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(_("تاريخ النهاية يجب أن يكون بعد تاريخ البداية / End date must be after start date"))
        if self.quotation_date and self.valid_until and getdate(self.valid_until) < getdate(self.quotation_date):
            frappe.throw(_("تاريخ صلاحية العرض لا يمكن أن يسبق تاريخ العرض / Valid-until date cannot precede quotation date"))
        if self.beneficiary_count and cint(self.beneficiary_count) <= 0:
            frappe.throw(_("عدد الوجبات اليومي يجب أن يكون أكبر من صفر / Daily meal count must be greater than zero"))

    def _calculate(self, validate_rows=False):
        days = 0
        if self.start_date and self.end_date and getdate(self.end_date) >= getdate(self.start_date):
            days = (getdate(self.end_date) - getdate(self.start_date)).days + 1
        self.service_days = days
        subtotal = 0.0
        for index, row in enumerate(self.items or [], 1):
            row.service_days = days
            if not row.daily_quantity and self.beneficiary_count:
                row.daily_quantity = cint(self.beneficiary_count)
            if row.menu_source == WAFD_MENU:
                if row.wafd_menu:
                    recipe = frappe.db.get_value(
                        "WAFD Recipe", row.wafd_menu,
                        ["recipe_name", "recommended_price_ex_vat"], as_dict=True,
                    )
                    if recipe:
                        row.menu_description = recipe.recipe_name or row.wafd_menu
                        if not flt(row.unit_price):
                            row.unit_price = flt(recipe.recommended_price_ex_vat)
                if validate_rows and not row.wafd_menu:
                    frappe.throw(_("اختر منيو وفد في البند رقم {0} / Select a WAFD menu for row {0}").format(index))
            elif row.menu_source == CUSTOMER_MENU:
                row.menu_description = row.custom_menu_description
                if validate_rows and not (row.custom_menu_description or "").strip():
                    frappe.throw(_("اكتب وصف طلب الشركة في البند رقم {0} / Enter the customer menu description for row {0}").format(index))
            elif validate_rows:
                frappe.throw(_("اختر مصدر المنيو في البند رقم {0} / Select the menu source for row {0}").format(index))
            if validate_rows and cint(row.daily_quantity) <= 0:
                frappe.throw(_("الكمية اليومية يجب أن تكون أكبر من صفر في البند رقم {0} / Daily quantity must be positive in row {0}").format(index))
            if validate_rows and flt(row.unit_price) <= 0:
                frappe.throw(_("سعر الوحدة يجب أن يكون أكبر من صفر في البند رقم {0} / Unit price must be positive in row {0}").format(index))
            row.total_quantity = cint(row.daily_quantity) * days
            row.amount = flt(row.total_quantity) * flt(row.unit_price)
            subtotal += flt(row.amount)
        subtotal += flt(self.additional_charges)
        taxable = max(subtotal - flt(self.discount_amount), 0)
        self.subtotal = subtotal
        self.tax_rate = 15
        self.tax_amount = taxable * flt(self.tax_rate) / 100
        self.grand_total = taxable + self.tax_amount

    def _fill_company_assets(self):
        self.company_name = self.company_name or "شركة وفد المدينة لخدمات الإعاشة"
        self.company_cr = self.company_cr or "7051832694"
        self.company_phone = self.company_phone or "0500336989"
        self.company_email = self.company_email or "wafd.almadinah@gmail.com"
        self.company_address = self.company_address or "المدينة المنورة، المملكة العربية السعودية"
        self.company_logo = self.company_logo or "/assets/wafd_one/images/wafd-almadinah-official.png"
        if self.include_signature is None:
            self.include_signature = 1
        if self.include_stamp is None:
            self.include_stamp = 1
        if not frappe.db.exists("DocType", "WAFD Print Settings"):
            return
        settings = frappe.get_single("WAFD Print Settings")
        self.authorized_signatory = self.authorized_signatory or settings.signatory_name or "نزار بن نذير بن ظفر"
        self.signatory_title = self.signatory_title or settings.signatory_title or "المدير العام"
        self.company_logo = settings.company_logo or self.company_logo
        # Never clear stored assets when the display checkbox is disabled.
        signature = settings.default_signature or self._template_asset("signature") or self._find_asset("signature")
        stamp = settings.default_stamp or self._template_asset("stamp") or self._find_asset("stamp")
        self.signature_image = self.signature_image or signature
        self.company_stamp = self.company_stamp or stamp

    def _template_asset(self, kind):
        if not frappe.db.exists("DocType", "WAFD Document Template"):
            return ""
        fieldname = "signature" if kind == "signature" else "stamp"
        return frappe.db.get_value(
            "WAFD Document Template", {fieldname: ["!=", ""]}, fieldname, order_by="modified desc"
        ) or ""

    def _find_asset(self, kind):
        tokens = ("signature", "sign", "توقيع") if kind == "signature" else ("stamp", "seal", "ختم")
        fields = ["file_url", "file_name"]
        if frappe.get_meta("File").has_field("attached_to_field"):
            fields.append("attached_to_field")
        rows = frappe.get_all(
            "File", filters={"attached_to_doctype": "WAFD Print Settings"},
            fields=fields, order_by="creation desc", limit=100,
        )
        expected = {"default_signature", "signature"} if kind == "signature" else {"default_stamp", "stamp"}
        for row in rows:
            if (row.get("attached_to_field") or "").lower() in expected and row.file_url:
                return row.file_url
        for row in rows:
            haystack = f"{row.file_name or ''} {row.file_url or ''}".lower()
            if row.file_url and any(token in haystack for token in tokens):
                return row.file_url
        return ""

    def validate_for_approval(self):
        required = {
            "customer_name": "اسم الشركة / Company name",
            "supply_location": "موقع التوريد / Supply location", "start_date": "تاريخ البداية / Start date",
            "end_date": "تاريخ النهاية / End date", "beneficiary_count": "عدد الوجبات اليومي / Daily meals",
        }
        missing = [label for field, label in required.items() if not self.get(field)]
        if not self.items:
            missing.append("بنود عرض السعر / Quotation items")
        if missing:
            frappe.throw(_("استكمل البيانات التالية قبل الاعتماد:<br>{0}").format("<br>".join(f"- {x}" for x in missing)))
        self._calculate(validate_rows=True)
        self._validate_dates()


def _user_name(user):
    return frappe.db.get_value("User", user, "full_name") or user


def _get_writable(name):
    doc = frappe.get_doc("WAFD Quotation", name)
    doc.check_permission("write")
    return doc


@frappe.whitelist()
def request_approval(name):
    doc = _get_writable(name)
    if doc.status != "مسودة / Draft":
        frappe.throw(_("يمكن إرسال المسودة فقط للاعتماد / Only a draft can be submitted for approval"))
    doc.validate_for_approval()
    doc.status = "بانتظار الاعتماد / Pending Approval"
    doc.flags.quotation_status_change = True
    doc.save()
    return doc.as_dict()


@frappe.whitelist()
def approve_quotation(name):
    roles = set(frappe.get_roles(frappe.session.user))
    if not roles.intersection(APPROVAL_ROLES):
        frappe.throw(_("ليست لديك صلاحية اعتماد عروض الأسعار / You are not permitted to approve quotations"), frappe.PermissionError)
    doc = _get_writable(name)
    if doc.status != "بانتظار الاعتماد / Pending Approval":
        frappe.throw(_("يجب أن يكون العرض بانتظار الاعتماد / Quotation must be pending approval"))
    doc.validate_for_approval()
    doc.status = "معتمد / Approved"
    doc.approved_by_user = frappe.session.user
    doc.approved_by_name = _user_name(frappe.session.user)
    doc.approved_on = now_datetime()
    doc.flags.quotation_status_change = True
    doc.save()
    return doc.as_dict()


@frappe.whitelist()
def set_quotation_status(name, status):
    doc = _get_writable(name)
    if status not in STATUS_TRANSITIONS.get(doc.status, set()):
        frappe.throw(_("الانتقال المطلوب لحالة عرض السعر غير مسموح / Requested status transition is not allowed"))
    doc.status = status
    doc.flags.quotation_status_change = True
    doc.save()
    return doc.as_dict()
