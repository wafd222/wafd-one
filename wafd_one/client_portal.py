from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, today

CLIENT_ROLE = "WAFD Client Portal User"


def _require_portal_user() -> str:
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw(_("يجب تسجيل الدخول / Login required"), frappe.PermissionError)
    roles = set(frappe.get_roles(user))
    if CLIENT_ROLE not in roles and "System Manager" not in roles and "WAFD Operations Manager" not in roles:
        frappe.throw(_("غير مصرح لك باستخدام بوابة العملاء / Client portal access denied"), frappe.PermissionError)
    return user


def _access_rows(user: str | None = None) -> list[dict[str, Any]]:
    user = user or _require_portal_user()
    if "System Manager" in set(frappe.get_roles(user)) or "WAFD Operations Manager" in set(frappe.get_roles(user)):
        # Management preview: only explicit mappings, never silently expose all clients/projects.
        pass
    return frappe.get_all(
        "WAFD Client Portal Access",
        filters={"user": user, "active": 1},
        fields=["name", "entity_type", "entity_name", "project", "contract"],
        order_by="modified desc",
    )


def _get_access(project: str, user: str | None = None) -> frappe._dict:
    user = user or _require_portal_user()
    row = frappe.db.get_value(
        "WAFD Client Portal Access",
        {"user": user, "project": project, "active": 1},
        ["name", "entity_type", "entity_name", "project", "contract"],
        as_dict=True,
    )
    if not row:
        frappe.throw(_("هذا المشروع غير مرتبط بحسابك / Project is not assigned to your account"), frappe.PermissionError)
    return row


def _latest(doctype: str, filters: dict, fields: list[str], order_by: str = "modified desc"):
    rows = frappe.get_all(doctype, filters=filters, fields=fields, order_by=order_by, limit=1)
    return rows[0] if rows else None


def _safe_status(value: Any) -> str:
    return str(value or "").strip()


def _project_summary(project_name: str, access: dict | None = None) -> dict[str, Any]:
    project = frappe.db.get_value(
        "WAFD Catering Project",
        project_name,
        [
            "name", "project_name", "status", "start_date", "end_date", "beneficiary_count",
            "total_meals", "delivered_meals", "remaining_meals", "progress_percent", "primary_hotel",
            "delivery_location", "delivery_window", "mission",
        ],
        as_dict=True,
    )
    if not project:
        return {}
    return {
        "name": project.name,
        "project_name": project.project_name or project.name,
        "status": _safe_status(project.status),
        "start_date": project.start_date,
        "end_date": project.end_date,
        "beneficiary_count": cint(project.beneficiary_count),
        "total_meals": cint(project.total_meals),
        "delivered_meals": cint(project.delivered_meals),
        "remaining_meals": cint(project.remaining_meals),
        "progress_percent": float(project.progress_percent or 0),
        "hotel": project.primary_hotel,
        "delivery_location": project.delivery_location,
        "delivery_window": project.delivery_window,
        "entity_name": (access or {}).get("entity_name") if access else None,
        "entity_type": (access or {}).get("entity_type") if access else None,
    }


def _day_tracking(project: str, service_date: str | None = None) -> dict[str, Any]:
    service_date = str(getdate(service_date or today()))
    daily = _latest(
        "WAFD Daily Meal Plan",
        {"project": project, "service_date": service_date},
        ["name", "service_date", "status", "total_quantity", "hotel", "production_batch_count"],
        "modified desc",
    )
    batch = _latest(
        "WAFD Production Batch",
        {"project": project, "batch_date": service_date},
        ["name", "quality_status", "planned_quantity", "produced_quantity", "rejected_quantity", "completion_percent", "daily_plan"],
        "modified desc",
    )
    quality = None
    if batch:
        quality = _latest(
            "WAFD Quality Inspection",
            {"production_batch": batch.name},
            ["name", "inspection_date", "result", "decision_time"],
            "inspection_date desc",
        )
    packaging = _latest(
        "WAFD Packaging Record",
        {"project": project, "packaging_date": service_date},
        ["name", "status", "planned_quantity", "packed_quantity", "rejected_quantity", "completion_percent", "box_count", "ready_for_loading"],
        "modified desc",
    )
    loading = _latest(
        "WAFD Loading Record",
        {"project": project, "loading_date": ["between", [f"{service_date} 00:00:00", f"{service_date} 23:59:59"]]},
        ["name", "status", "quantity", "vehicle", "driver", "loading_date", "dispatch_time", "hotel", "box_count", "hot_cabinet_count"],
        "loading_date desc",
    )
    trip = _latest(
        "WAFD Delivery Trip",
        {"project": project, "trip_date": service_date},
        [
            "name", "status", "quantity", "vehicle", "driver", "hotel", "planned_departure", "actual_departure",
            "planned_arrival", "actual_arrival", "on_time_status", "delay_minutes", "transit_duration_minutes",
        ],
        "modified desc",
    )
    receipt = None
    acknowledgement = None
    if trip:
        receipt = _latest(
            "WAFD Receiving Note",
            {"delivery_trip": trip.name},
            ["name", "status", "receipt_time", "delivered_quantity", "received_quantity", "rejected_quantity", "condition_status", "receiver_name"],
            "receipt_time desc",
        )
        acknowledgement = _latest(
            "WAFD Client Receipt Acknowledgement",
            {"delivery_trip": trip.name},
            ["name", "confirmed_at", "received_quantity", "receiver_name", "receiver_title"],
            "confirmed_at desc",
        )

    planned_qty = cint((daily or {}).get("total_quantity"))
    produced_qty = cint((batch or {}).get("produced_quantity"))
    packed_qty = cint((packaging or {}).get("packed_quantity"))
    loaded_qty = cint((loading or {}).get("quantity"))
    trip_qty = cint((trip or {}).get("quantity"))
    received_qty = cint((receipt or {}).get("received_quantity"))

    stages = [
        {"key":"planned","label":"مجدولة","done": bool(daily), "status": _safe_status((daily or {}).get("status")), "qty": planned_qty},
        {"key":"production","label":"الإنتاج","done": bool(batch and produced_qty > 0), "status": _safe_status((batch or {}).get("quality_status")), "qty": produced_qty},
        {"key":"quality","label":"الجودة","done": bool(quality and _safe_status(quality.get("result")) in ("ناجح / Passed", "مشروط / Conditional")), "status": _safe_status((quality or {}).get("result")), "qty": produced_qty},
        {"key":"packaging","label":"التغليف","done": bool(packaging and (packaging.get("ready_for_loading") or _safe_status(packaging.get("status")) in ("مكتمل / Completed", "جاهز للتحميل / Ready for Loading"))), "status": _safe_status((packaging or {}).get("status")), "qty": packed_qty},
        {"key":"loading","label":"التحميل","done": bool(loading and _safe_status(loading.get("status")) in ("تم التحميل / Loaded", "خرجت / Dispatched")), "status": _safe_status((loading or {}).get("status")), "qty": loaded_qty},
        {"key":"transit","label":"في الطريق","done": bool(trip and _safe_status(trip.get("status")) in ("في الطريق / In Transit", "وصلت / Arrived", "تم التسليم / Delivered")), "status": _safe_status((trip or {}).get("status")), "qty": trip_qty},
        {"key":"arrival","label":"الوصول","done": bool(trip and (_safe_status(trip.get("status")) in ("وصلت / Arrived", "تم التسليم / Delivered") or trip.get("actual_arrival"))), "status": _safe_status((trip or {}).get("on_time_status")), "qty": trip_qty},
        {"key":"receipt","label":"الاستلام","done": bool(receipt and _safe_status(receipt.get("status")) == "تم الاستلام / Received"), "status": _safe_status((receipt or {}).get("condition_status")), "qty": received_qty},
    ]
    return {
        "service_date": service_date,
        "planned_quantity": planned_qty,
        "stages": stages,
        "daily_plan": daily,
        "production": batch,
        "quality": quality,
        "packaging": packaging,
        "loading": loading,
        "trip": trip,
        "receipt": receipt,
        "client_acknowledgement": acknowledgement,
    }


@frappe.whitelist()
def get_portal_home():
    user = _require_portal_user()
    accesses = _access_rows(user)
    projects = [_project_summary(row["project"], row) for row in accesses]
    projects = [row for row in projects if row]
    display_name = frappe.db.get_value("User", user, "full_name") or user
    return {
        "user": user,
        "display_name": display_name,
        "projects": projects,
        "project_count": len(projects),
        "today": today(),
    }


@frappe.whitelist()
def get_project_tracking(project: str, service_date: str | None = None):
    user = _require_portal_user()
    access = _get_access(project, user)
    return {
        "project": _project_summary(project, access),
        "tracking": _day_tracking(project, service_date),
    }


@frappe.whitelist()
def get_recent_deliveries(project: str, limit: int = 10):
    user = _require_portal_user()
    _get_access(project, user)
    limit = max(1, min(cint(limit) or 10, 30))
    rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"project": project},
        fields=["name", "trip_date", "status", "quantity", "hotel", "vehicle", "planned_arrival", "actual_arrival", "on_time_status", "delay_minutes"],
        order_by="trip_date desc, modified desc",
        limit=limit,
    )
    return rows


@frappe.whitelist()
def acknowledge_receipt(delivery_trip: str, receiver_name: str, receiver_title: str | None = None, notes: str | None = None):
    user = _require_portal_user()
    trip = frappe.db.get_value(
        "WAFD Delivery Trip", delivery_trip,
        ["name", "project", "status", "quantity", "actual_arrival"], as_dict=True,
    )
    if not trip:
        frappe.throw(_("رحلة التوصيل غير موجودة / Delivery trip not found"))
    access = _get_access(trip.project, user)
    if _safe_status(trip.status) not in ("وصلت / Arrived", "تم التسليم / Delivered") and not trip.actual_arrival:
        frappe.throw(_("لا يمكن تأكيد الاستلام قبل وصول الرحلة / Arrival must be recorded first"))
    if frappe.db.exists("WAFD Client Receipt Acknowledgement", {"delivery_trip": delivery_trip}):
        return frappe.db.get_value(
            "WAFD Client Receipt Acknowledgement", {"delivery_trip": delivery_trip},
            ["name", "confirmed_at", "received_quantity", "receiver_name", "receiver_title"], as_dict=True,
        )
    receiver_name = (receiver_name or "").strip()
    if not receiver_name:
        frappe.throw(_("اسم المستلم مطلوب / Receiver name is required"))
    doc = frappe.get_doc({
        "doctype": "WAFD Client Receipt Acknowledgement",
        "portal_user": user,
        "portal_access": access.name,
        "project": trip.project,
        "delivery_trip": delivery_trip,
        "confirmed_at": now_datetime(),
        "received_quantity": cint(trip.quantity),
        "receiver_name": receiver_name,
        "receiver_title": (receiver_title or "").strip(),
        "notes": (notes or "").strip(),
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {
        "name": doc.name,
        "confirmed_at": doc.confirmed_at,
        "received_quantity": doc.received_quantity,
        "receiver_name": doc.receiver_name,
        "receiver_title": doc.receiver_title,
    }
