"""Mobile handover and usage workflow for cleaning materials."""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from wafd_one.ingredient_i18n import add_ingredient_labels

ROLE = "WAFD Cleaning Supervisor"
ELEVATED = {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}


def _check_supervisor():
    roles = set(frappe.get_roles())
    if ROLE not in roles and not roles.intersection(ELEVATED):
        frappe.throw(_("هذه الشاشة لمشرف النظافة / Cleaning Supervisor access required"), frappe.PermissionError)


def _movement_for_current_user(name, pending=False):
    movement = frappe.get_doc("WAFD Stock Movement", name)
    if movement.issued_to_user != frappe.session.user:
        frappe.throw(_("سند التسليم غير مسند لك / This handover is not assigned to you"), frappe.PermissionError)
    if movement.movement_type != "صرف / Issue" or movement.status != "مرحلة / Posted":
        frappe.throw(_("سند التسليم غير صالح / Invalid handover"))
    if frappe.db.get_value("WAFD Warehouse", movement.source_warehouse, "warehouse_type") != "نظافة / Cleaning":
        frappe.throw(_("السند ليس من مستودع النظافة / Handover is not from a cleaning warehouse"))
    if pending and movement.handover_status != "بانتظار الاستلام / Pending Receipt":
        frappe.throw(_("تمت معالجة سند التسليم مسبقاً / Handover was already processed"))
    return movement


def _movement_payload(movement, language=None):
    items = [
        {"ingredient": row.ingredient, "quantity": flt(row.quantity), "uom": row.uom}
        for row in movement.items or []
    ]
    add_ingredient_labels(items, language)
    return {
        "name": movement.name,
        "posting_date": movement.posting_date,
        "source_warehouse": movement.source_warehouse,
        "status": movement.handover_status,
        "sent_on": movement.handover_sent_on,
        "items": items,
    }


@frappe.whitelist()
def get_cleaning_dashboard(language=None):
    _check_supervisor()
    names = frappe.get_all(
        "WAFD Stock Movement",
        filters={
            "movement_type": "صرف / Issue",
            "status": "مرحلة / Posted",
            "issued_to_user": frappe.session.user,
            "handover_status": ["in", ["بانتظار الاستلام / Pending Receipt", "تم الاستلام / Received"]],
        },
        pluck="name",
        order_by="posting_date desc",
        limit_page_length=200,
    )
    movements = [
        doc for doc in (frappe.get_doc("WAFD Stock Movement", name) for name in names)
        if not doc.get("is_pre_go_live_test")
    ]
    pending = [_movement_payload(doc, language) for doc in movements if doc.handover_status == "بانتظار الاستلام / Pending Receipt"]

    used_rows = frappe.db.sql(
        """select u.source_handover, i.ingredient, sum(i.quantity) as quantity
             from `tabWAFD Cleaning Material Usage` u
             join `tabWAFD Cleaning Material Usage Item` i on i.parent=u.name
            where u.supervisor=%s
            group by u.source_handover, i.ingredient""",
        frappe.session.user,
        as_dict=True,
    )
    used = {(row.source_handover, row.ingredient): flt(row.quantity) for row in used_rows}
    custody = []
    for doc in movements:
        if doc.handover_status != "تم الاستلام / Received":
            continue
        for row in doc.items or []:
            remaining = flt(row.quantity) - used.get((doc.name, row.ingredient), 0)
            if remaining > 0.000001:
                custody.append({
                    "handover": doc.name,
                    "ingredient": row.ingredient,
                    "received_quantity": flt(row.quantity),
                    "remaining_quantity": remaining,
                    "uom": row.uom,
                })
    add_ingredient_labels(custody, language)

    recent = frappe.get_all(
        "WAFD Cleaning Material Usage",
        filters={"supervisor": frappe.session.user},
        fields=["name", "usage_date", "source_handover", "purpose", "location"],
        order_by="usage_date desc",
        limit_page_length=20,
    )
    for entry in recent:
        entry["items"] = frappe.get_all(
            "WAFD Cleaning Material Usage Item",
            filters={"parent": entry.name},
            fields=["ingredient", "quantity", "uom"],
            order_by="idx asc",
        )
        add_ingredient_labels(entry["items"], language)
    return {"pending": pending, "custody": custody, "recent_usage": recent}


@frappe.whitelist()
def respond_cleaning_handover(movement_name, action, rejection_reason=None):
    _check_supervisor()
    frappe.db.sql("select name from `tabWAFD Stock Movement` where name=%s for update", movement_name)
    movement = _movement_for_current_user(movement_name, pending=True)
    if action == "accept":
        movement.db_set({
            "handover_status": "تم الاستلام / Received",
            "handover_received_by": frappe.session.user,
            "handover_received_on": now_datetime(),
            "handover_rejection_reason": None,
        }, update_modified=True)
    elif action == "reject":
        reason = (rejection_reason or "").strip()
        if not reason:
            frappe.throw(_("اكتب سبب رفض الاستلام / Enter a rejection reason"))
        from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import reverse_posted_movement
        reverse_posted_movement(movement, reason=f"cleaning handover rejected: {reason}")
        frappe.db.set_value("WAFD Stock Movement", movement.name, {
            "handover_status": "مرفوض / Rejected",
            "handover_received_by": frappe.session.user,
            "handover_received_on": now_datetime(),
            "handover_rejection_reason": reason,
        }, update_modified=True)
    else:
        frappe.throw(_("إجراء غير صالح / Invalid action"))
    return {"name": movement.name, "action": action}


@frappe.whitelist()
def record_cleaning_usage(source_handover, ingredient, quantity, purpose, location=None, notes=None):
    _check_supervisor()
    _movement_for_current_user(source_handover)
    doc = frappe.get_doc({
        "doctype": "WAFD Cleaning Material Usage",
        "supervisor": frappe.session.user,
        "usage_date": now_datetime(),
        "source_handover": source_handover,
        "purpose": (purpose or "").strip(),
        "location": (location or "").strip(),
        "notes": (notes or "").strip(),
        "items": [{"ingredient": ingredient, "quantity": flt(quantity)}],
    })
    # The supervisor has no general DocType create permission. Creation is only
    # allowed through this validated, role-scoped workflow.
    doc.insert(ignore_permissions=True)
    return {"name": doc.name}
