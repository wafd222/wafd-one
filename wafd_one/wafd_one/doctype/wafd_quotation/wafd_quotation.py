from pathlib import Path

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
ARABIC_LANGUAGE = "العربية / Arabic"
ENGLISH_LANGUAGE = "English"


class WAFDQuotation(Document):
    def before_insert(self):
        self.prepared_by_user = frappe.session.user
        self.prepared_by_name = _user_name(frappe.session.user)
        self.status = "مسودة / Draft"
        self.quotation_date = self.quotation_date or today()
        self.valid_until = self.valid_until or add_days(self.quotation_date, 15)
        self.quotation_language = self.quotation_language or ARABIC_LANGUAGE

    def validate(self):
        self.quotation_language = self.quotation_language or ARABIC_LANGUAGE
        if self.quotation_language not in {ARABIC_LANGUAGE, ENGLISH_LANGUAGE}:
            frappe.throw(_("لغة عرض السعر غير صحيحة / Invalid quotation language"))
        self._protect_status()
        self._fill_customer()
        self._fill_company_assets()
        self._fill_default_texts()
        self._calculate(validate_rows=False)
        self._validate_dates()
        if self.status not in ALLOWED_STATUSES:
            frappe.throw(_("حالة عرض السعر غير صحيحة / Invalid quotation status"))

    def _fill_default_texts(self):
        defaults = {
            "quotation_subject": "عرض سعر لتقديم خدمات الإعاشة اليومية",
            "introduction_text": "يسر شركة وفد المدينة لخدمات الإعاشة أن تتقدم لكم بعرضها لتوفير وجبات الإعاشة اليومية وفقاً للكميات والمدة الموضحة في هذا العرض.\nيشمل العرض تجهيز الوجبات وتغليفها وتوصيلها وتوزيعها في الموقع المتفق عليه.\nيتم تطبيق المنيو المتفق عليه بصورة متكررة طوال مدة التعاقد.",
            "quotation_terms": "1. السعر مبني على العدد اليومي ومدة التعاقد الموضحين في عرض السعر.\n2. تشمل الأسعار تجهيز الوجبات والتغليف والتوصيل والتوزيع إلى موقع واحد وفي المواعيد اليومية المتفق عليها.\n3. تضاف ضريبة القيمة المضافة بنسبة 15% إلى جميع الفواتير.\n4. يتم اعتماد العدد النهائي للوجبات يومياً حسب الكمية المؤكدة من ممثل العميل.\n5. يجب إبلاغ شركة وفد المدينة بأي زيادة أو تخفيض في عدد الوجبات قبل موعد التقديم بما لا يقل عن 48 ساعة.\n6. يجوز استبدال أي صنف غير متوفر بصنف مماثل في القيمة والجودة بعد التنسيق مع ممثل العميل.\n7. لا يشمل السعر توفير صالات الطعام أو الأثاث أو أدوات التقديم الدائمة أو أعمال النظافة خارج نطاق توزيع الوجبات، ما لم يتم الاتفاق عليها كتابةً.\n8. أي توصيل إلى مواقع إضافية أو تغيير جوهري في مواعيد التوزيع تتم دراسته وتسعيره بشكل مستقل.\n9. الوجبات التي يتم تجهيزها بناءً على العدد المعتمد تُحتسب بالكامل عند الإلغاء المتأخر.\n10. مدة صلاحية عرض السعر 15 يوماً من تاريخ إصداره.\n11. يبدأ تنفيذ الخدمة بعد اعتماد العرض وتوقيع العقد أو إصدار أمر الشراء وتحديد الموقع ومواعيد التسليم.",
            "payment_terms": "1. دفعة مقدمة قدرها 50% من القيمة التقديرية للشهر الأول عند اعتماد العرض وتوقيع العقد أو إصدار أمر الشراء.\n2. دفعة قدرها 50% بعد مرور 15 يوماً من بداية تقديم الخدمة.\n3. تطبق آلية الدفعات نفسها على كل شهر تعاقدي لاحق، ما لم يتم الاتفاق كتابياً على خلاف ذلك.\n4. يتم السداد عن طريق التحويل البنكي إلى الحساب الرسمي لشركة وفد المدينة لخدمات الإعاشة.\n5. يحق لمقدم الخدمة تعليق التوريد بعد إشعار العميل كتابياً في حال تأخر أي دفعة عن موعد استحقاقها.",
            "closing_text": "نأمل أن يحوز عرضنا على رضاكم، ونتطلع إلى التعاون مع شركتكم الموقرة وتقديم خدمات إعاشة تتميز بالجودة والالتزام وسلامة الغذاء.\nوتفضلوا بقبول خالص التحية والتقدير.",
            "quotation_subject_en": "Quotation for Daily Catering Services",
            "introduction_text_en": "Wafd Al Madinah Catering Services is pleased to submit this quotation for the provision of daily catering meals in accordance with the quantities and service period stated herein.\nThis quotation includes meal preparation, packaging, delivery and distribution at the agreed location.\nThe agreed menu will be provided on a recurring weekly basis throughout the contract term.",
            "quotation_terms_en": "1. The price is based on the daily meal count and service period stated in this quotation.\n2. Prices include meal preparation, packaging, delivery and distribution to one location at the agreed daily times.\n3. Value Added Tax (VAT) at 15% is added to all invoices.\n4. The final daily meal count will be based on the quantity confirmed by the customer's representative.\n5. Wafd Al Madinah must be notified of any increase or decrease in meal quantities at least 48 hours before service.\n6. Any unavailable item may be replaced with an item of comparable value and quality after coordination with the customer's representative.\n7. The price does not include dining halls, furniture, permanent serving equipment or cleaning work beyond meal distribution unless agreed in writing.\n8. Delivery to additional locations or a material change to distribution times will be reviewed and quoted separately.\n9. Meals prepared according to the confirmed quantity will be charged in full in the event of late cancellation.\n10. This quotation is valid for 15 days from its issue date.\n11. Service begins after quotation approval and contract signature or purchase-order issuance, and after confirming the location and delivery times.",
            "payment_terms_en": "1. An advance payment of 50% of the estimated first-month value is due upon quotation approval and contract signature or purchase-order issuance.\n2. The remaining 50% is due 15 days after service begins.\n3. The same payment schedule applies to every subsequent contract month unless otherwise agreed in writing.\n4. Payment shall be made by bank transfer to the official account of Wafd Al Madinah Catering Services.\n5. The service provider may suspend supply after written notice to the customer if any payment is overdue.",
            "closing_text_en": "We hope this quotation meets your approval and look forward to working with your respected company and providing catering services distinguished by quality, commitment and food safety.\nSincerely yours,",
        }
        for fieldname, value in defaults.items():
            if not (self.get(fieldname) or "").strip():
                self.set(fieldname, value)

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
            self.signature_image = self.signature_image or self._undertaking_asset("signature") or self._template_asset("signature")
            self.company_stamp = self.company_stamp or self._undertaking_asset("stamp") or self._template_asset("stamp")
            return
        settings = frappe.get_single("WAFD Print Settings")
        self.authorized_signatory = self.authorized_signatory or settings.signatory_name or "نزار بن نذير بن ظفر"
        self.signatory_title = self.signatory_title or settings.signatory_title or "المدير العام"
        self.company_logo = settings.company_logo or self.company_logo
        # Never clear stored assets when the display checkbox is disabled.
        signature = settings.default_signature or self._undertaking_asset("signature") or self._template_asset("signature") or self._find_asset("signature")
        stamp = settings.default_stamp or self._undertaking_asset("stamp") or self._template_asset("stamp") or self._find_asset("stamp")
        self.signature_image = self.signature_image or signature
        self.company_stamp = self.company_stamp or stamp

    def _undertaking_asset(self, kind):
        """Reuse the approved undertaking assets when print settings are legacy/incomplete."""
        if not frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
            return ""
        fieldname = "signature_image" if kind == "signature" else "company_stamp"
        if not frappe.get_meta("WAFD Hotel Undertaking").has_field(fieldname):
            return ""
        return frappe.db.get_value(
            "WAFD Hotel Undertaking", {fieldname: ["!=", ""]},
            fieldname, order_by="modified desc",
        ) or ""

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


@frappe.whitelist()
def mark_quotation_sent(name):
    """Record a completed share and expose it in the sent-quotations register."""
    doc = _get_writable(name)
    if doc.status not in {"مقبول / Accepted", "مرفوض / Rejected", "ملغي / Cancelled", "منتهي / Expired"}:
        doc.status = "أرسل للعميل / Sent"
        doc.flags.quotation_status_change = True
    doc.sent_on = now_datetime()
    doc.sent_by = frappe.session.user
    doc.save()
    return doc.as_dict()


def _quotation_template_source():
    path = Path(__file__).resolve().parents[2] / "print_format" / "wafd_quotation" / "wafd_quotation.html"
    return path.read_text(encoding="utf-8")


def _normalize_quotation_language(language=None, doc=None):
    value = str(language or (doc and doc.get("quotation_language")) or ARABIC_LANGUAGE).strip().lower()
    return "en" if value in {"en", "english"} else "ar"


def _render_quotation_html(doc, language=None):
    from wafd_one.document_studio import _embed_pdf_images

    doc._fill_company_assets()
    doc._fill_default_texts()
    html = frappe.render_template(
        _quotation_template_source(),
        {"doc": doc, "language": _normalize_quotation_language(language, doc)},
    )
    return _embed_pdf_images(html)


def _remove_quotation_blank_pages(pdf_bytes):
    """Remove wkhtmltopdf spacer pages, including page-number-only pages."""
    import re
    from io import BytesIO
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(BytesIO(pdf_bytes))
    kept = []
    for page in reader.pages:
        raw_text = " ".join((page.extract_text() or "").split())
        page_number_only = bool(re.fullmatch(r"[0-9]+\s*/\s*[0-9]+", raw_text))
        if page_number_only:
            continue
        text = raw_text.strip()
        resources = page.get("/Resources") or {}
        xobjects = resources.get("/XObject") if hasattr(resources, "get") else None
        if text or xobjects:
            kept.append(page)
    if not kept or len(kept) == len(reader.pages):
        return pdf_bytes
    writer = PdfWriter()
    for page in kept:
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@frappe.whitelist()
def preview_quotation_html(name, language=None):
    doc = frappe.get_doc("WAFD Quotation", name)
    doc.check_permission("read")
    html = _render_quotation_html(doc, language)
    frappe.local.response.filename = f"{doc.name}.html"
    frappe.local.response.filecontent = html.encode("utf-8")
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "inline"
    frappe.local.response.content_type = "text/html; charset=utf-8"


@frappe.whitelist()
def generate_quotation_pdf(name, language=None):
    from frappe.utils.pdf import get_pdf
    from wafd_one.document_studio import _remove_trailing_blank_pages

    doc = frappe.get_doc("WAFD Quotation", name)
    doc.check_permission("print")
    language = _normalize_quotation_language(language, doc)
    html = _render_quotation_html(doc, language)
    pdf = get_pdf(html, options={
        "page-size": "A4", "margin-top": "0mm", "margin-right": "0mm",
        "margin-bottom": "0mm", "margin-left": "0mm", "encoding": "UTF-8",
        "disable-smart-shrinking": None, "print-media-type": None,
    })
    pdf = _remove_trailing_blank_pages(pdf)
    pdf = _remove_quotation_blank_pages(pdf)
    filename = f"{doc.name}{'-EN' if language == 'en' else ''}.pdf"
    existing = frappe.db.get_value("File", {
        "attached_to_doctype": doc.doctype, "attached_to_name": doc.name,
        "file_name": filename,
    }, "name")
    if existing:
        frappe.delete_doc("File", existing, ignore_permissions=True, force=True)
    file_doc = frappe.get_doc({
        "doctype": "File", "file_name": filename,
        "attached_to_doctype": doc.doctype, "attached_to_name": doc.name,
        "is_private": 1, "content": pdf,
    }).insert(ignore_permissions=True)
    frappe.db.set_value(doc.doctype, doc.name, {
        "generated_pdf": file_doc.file_url,
        "generated_on": now_datetime(), "generated_by": frappe.session.user,
    }, update_modified=False)
    return {"file_url": file_doc.file_url, "file_name": filename, "docname": doc.name}


@frappe.whitelist()
def download_generated_pdf(name, download=0):
    doc = frappe.get_doc("WAFD Quotation", name)
    doc.check_permission("read")
    if not doc.generated_pdf:
        frappe.throw(_("لم يتم إنشاء ملف PDF لعرض السعر / No PDF has been generated"))
    file_name = frappe.db.get_value("File", {
        "file_url": doc.generated_pdf, "attached_to_doctype": doc.doctype,
        "attached_to_name": doc.name,
    }, "name")
    if not file_name:
        frappe.throw(_("ملف PDF غير موجود / PDF file was not found"))
    file_doc = frappe.get_doc("File", file_name)
    content = file_doc.get_content()
    if isinstance(content, str):
        content = content.encode()
    frappe.local.response.filename = file_doc.file_name or f"{doc.name}.pdf"
    frappe.local.response.filecontent = content
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "attachment" if cint(download) else "inline"
    frappe.local.response.content_type = "application/pdf"
