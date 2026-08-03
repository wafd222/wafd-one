import json
from copy import deepcopy
import frappe
from frappe.utils import cint, flt, now_datetime

CRITICAL_DOCTYPES = {
    "WAFD Contract": ("enable_contract_approval", "contract_threshold", "contract_value"),
    "WAFD Purchase Order": ("enable_purchase_approval", "purchase_threshold", "grand_total"),
    "WAFD Invoice": ("enable_invoice_approval", "invoice_threshold", "grand_total"),
    "WAFD Payment": ("enable_payment_approval", "payment_threshold", "amount"),
    "WAFD Project Cost": ("enable_cost_approval", "cost_threshold", "amount"),
    "WAFD Project Revenue": ("enable_revenue_approval", "revenue_threshold", "amount"),
}
AUDITED_DOCTYPES = set(CRITICAL_DOCTYPES) | {
    "WAFD Catering Project", "WAFD Meal Plan", "WAFD Production Batch",
    "WAFD Stock Movement", "WAFD Delivery Trip", "WAFD Delivery Proof",
    "WAFD Quality Inspection", "WAFD CCP Check", "WAFD Approval Request",
}
SENSITIVE_FIELDS = {"password", "api_key", "api_secret", "secret", "token"}


def _settings():
    if not frappe.db.exists("DocType", "WAFD Governance Settings"):
        return None
    return frappe.get_single("WAFD Governance Settings")


def get_document_amount(doc):
    spec = CRITICAL_DOCTYPES.get(doc.doctype)
    return flt(doc.get(spec[2])) if spec else 0


def sanitized_snapshot(doc):
    data = deepcopy(doc.as_dict(no_nulls=True))

    def clean(value):
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if key in {"__islocal", "name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "parent", "parentfield", "parenttype", "status"}:
                    continue
                if any(word in key.lower() for word in SENSITIVE_FIELDS):
                    result[key] = "***"
                else:
                    result[key] = clean(item)
            return result
        return value

    return clean(data)


def approval_required(doc):
    spec = CRITICAL_DOCTYPES.get(doc.doctype)
    settings = _settings()
    if not spec or not settings or not cint(settings.get(spec[0])):
        return False
    return get_document_amount(doc) >= flt(settings.get(spec[1]))


def get_approved_request(doc):
    return frappe.db.get_value("WAFD Approval Request", {
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "status": "معتمد / Approved",
    }, ["name", "amount", "snapshot"], as_dict=True, order_by="decided_on desc")


def ensure_approved(doc, action_label="تنفيذ العملية / perform this action"):
    if not approval_required(doc):
        return
    approval = get_approved_request(doc)
    if not approval:
        frappe.throw("يتطلب هذا المستند اعتمادًا قبل {0} / This document requires approval before {0}".format(action_label))
    current_snapshot = json.dumps(sanitized_snapshot(doc), ensure_ascii=False, sort_keys=True, default=str)
    if flt(approval.amount, 2) != flt(get_document_amount(doc), 2) or (approval.snapshot or "") != current_snapshot:
        frappe.throw("تم تعديل المستند بعد اعتماده. أنشئ طلب اعتماد جديدًا / The document changed after approval; create a new approval request")


def request_approval(reference_doctype, reference_name, reason=None):
    if reference_doctype not in CRITICAL_DOCTYPES:
        frappe.throw("نوع المستند غير مدعوم / Unsupported document type")
    doc = frappe.get_doc(reference_doctype, reference_name)
    doc.check_permission("write")
    if not approval_required(doc):
        return {"required": False, "message": "Approval is not required by current settings."}
    existing = frappe.db.get_value("WAFD Approval Request", {
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "status": "بانتظار الاعتماد / Pending",
    }, "name")
    if existing:
        return {"required": True, "name": existing, "created": False}
    request = frappe.get_doc({
        "doctype": "WAFD Approval Request",
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "reason": reason,
    }).insert()
    record_event(request, "طلب اعتماد / Approval Requested", details=reason)
    return {"required": True, "name": request.name, "created": True}


def decide_approval(request_name, decision, notes=None):
    mapping = {
        "approve": "معتمد / Approved",
        "reject": "مرفوض / Rejected",
        "cancel": "ملغي / Cancelled",
    }
    if decision not in mapping:
        frappe.throw("قرار غير صحيح / Invalid decision")

    request = frappe.get_doc("WAFD Approval Request", request_name)
    request.check_permission("write")
    if request.status != "بانتظار الاعتماد / Pending":
        frappe.throw("تم اتخاذ قرار على هذا الطلب مسبقًا / This approval request is already finalized")

    settings = _settings()
    approver_role = (settings.approver_role if settings else None) or "WAFD Approver"
    roles = frappe.get_roles()
    if approver_role not in roles and "System Manager" not in roles:
        frappe.throw("ليست لديك صلاحية الاعتماد / You do not have approval permission")
    if settings and cint(settings.prevent_self_approval) and request.requested_by == frappe.session.user:
        frappe.throw("لا يجوز لمقدم الطلب اعتماد طلبه / Requesters cannot approve their own request")
    if decision in {"reject", "cancel"} and not (notes or "").strip():
        frappe.throw("يجب تسجيل سبب الرفض أو الإلغاء / Rejection or cancellation reason is required")

    request.status = mapping[decision]
    request.decision_notes = notes
    request.save()
    event = {
        "approve": "اعتماد / Approved",
        "reject": "رفض / Rejected",
        "cancel": "إلغاء / Cancelled",
    }[decision]
    record_event(request, event, details=notes)
    return {"name": request.name, "status": request.status}


def _changed_fields(doc):
    previous=doc.get_doc_before_save()
    if not previous:
        return {}
    changes={}
    for field in doc.meta.fields:
        if field.fieldtype in ("Section Break","Column Break","HTML","Button"):
            continue
        before=previous.get(field.fieldname)
        after=doc.get(field.fieldname)
        if field.fieldtype == "Table":
            before=[r.as_dict(no_nulls=True) for r in (before or [])]
            after=[r.as_dict(no_nulls=True) for r in (after or [])]
        if before != after:
            changes[field.fieldname]={"before":before,"after":after}
    return changes


def record_event(doc,event_type,details=None,changes=None):
    if getattr(frappe.flags,"wafd_recording_audit",False):
        return
    if doc.doctype == "WAFD Audit Event":
        return
    settings=_settings()
    if settings and not cint(settings.enable_audit_log):
        return
    try:
        frappe.flags.wafd_recording_audit=True
        request=getattr(frappe.local,"request",None)
        audit=frappe.get_doc({
            "doctype":"WAFD Audit Event",
            "event_time":now_datetime(),
            "event_type":event_type,
            "user":frappe.session.user if getattr(frappe,"session",None) else "Administrator",
            "reference_doctype":doc.doctype,
            "reference_name":doc.name,
            "reference_title":doc.get_title() or doc.name,
            "details":details,
            "changes":json.dumps(changes or {},ensure_ascii=False,default=str,sort_keys=True),
            "request_id":getattr(frappe.local,"request_id",None),
            "ip_address":getattr(request,"remote_addr",None) if request else None,
        })
        audit.flags.ignore_permissions=True
        audit.flags.ignore_version=True
        audit.insert(ignore_permissions=True)
    finally:
        frappe.flags.wafd_recording_audit=False


def audit_after_insert(doc,method=None):
    if doc.doctype in AUDITED_DOCTYPES:
        record_event(doc,"إنشاء / Insert",changes={"created":sanitized_snapshot(doc)})


def audit_on_update(doc,method=None):
    if doc.doctype in AUDITED_DOCTYPES:
        changes=_changed_fields(doc)
        if changes:
            record_event(doc,"تعديل / Update",changes=changes)


def audit_on_trash(doc,method=None):
    if doc.doctype in AUDITED_DOCTYPES:
        record_event(doc,"حذف / Delete",changes={"deleted":sanitized_snapshot(doc)})


@frappe.whitelist()
def request_document_approval(reference_doctype, reference_name, reason=None):
    return request_approval(reference_doctype,reference_name,reason)

@frappe.whitelist()
def decide_document_approval(request_name, decision, notes=None):
    return decide_approval(request_name,decision,notes)

@frappe.whitelist()
def governance_health_check():
    if "System Manager" not in frappe.get_roles() and "WAFD Operations Manager" not in frappe.get_roles():
        frappe.throw("Not permitted",frappe.PermissionError)
    required=["WAFD Governance Settings","WAFD Approval Request","WAFD Audit Event"]
    missing=[x for x in required if not frappe.db.exists("DocType",x)]
    duplicate_pending=frappe.db.sql("""select reference_doctype,reference_name,count(*) c from `tabWAFD Approval Request`
        where status='بانتظار الاعتماد / Pending' group by reference_doctype,reference_name having count(*)>1""",as_dict=True) if not missing else []
    result={
      "ok":not missing and not duplicate_pending,
      "missing_doctypes":missing,
      "duplicate_pending_approvals":duplicate_pending,
      "audit_events":frappe.db.count("WAFD Audit Event") if not missing else 0,
      "pending_approvals":frappe.db.count("WAFD Approval Request",{"status":"بانتظار الاعتماد / Pending"}) if not missing else 0,
    }
    record_event(frappe.get_doc("WAFD Governance Settings"),"فحص صحة / Health Check",details=json.dumps(result,ensure_ascii=False,default=str)) if not missing else None
    return result
