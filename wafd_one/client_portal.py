from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, getdate, get_datetime, now_datetime, today

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


def _latest_service_date(project: str) -> str:
    """Return the most recent operational date for the project.

    The portal is often opened after a project/day has finished. Defaulting to
    today's date made a completed historical project look like it had zero
    production/delivery activity. Prefer the latest real service/trip date.
    """
    candidates: list[str] = []
    for doctype, field in (
        ("WAFD Daily Meal Plan", "service_date"),
        ("WAFD Production Batch", "batch_date"),
        ("WAFD Packaging Record", "packaging_date"),
        ("WAFD Delivery Trip", "trip_date"),
    ):
        row = frappe.get_all(
            doctype,
            filters={"project": project},
            fields=[field],
            order_by=f"{field} desc",
            limit=1,
        )
        if row and row[0].get(field):
            candidates.append(str(getdate(row[0].get(field))))
    return max(candidates) if candidates else str(getdate(today()))


def _sum(rows: list[dict[str, Any]], field: str) -> int:
    return sum(cint(row.get(field)) for row in rows)


def _status_from_rows(rows: list[dict[str, Any]], field: str) -> str:
    values = [_safe_status(row.get(field)) for row in rows if _safe_status(row.get(field))]
    if not values:
        return ""
    # Keep the newest/last visible status while aggregation uses all rows.
    return values[0]


def _first_datetime(values: list[Any]):
    parsed = [get_datetime(value) for value in values if value]
    return min(parsed) if parsed else None


def _last_datetime(values: list[Any]):
    parsed = [get_datetime(value) for value in values if value]
    return max(parsed) if parsed else None


def _duration_payload(start, end) -> dict[str, Any]:
    if not start or not end:
        return {"start": start, "end": end, "minutes": None, "display": "—"}
    start_dt, end_dt = get_datetime(start), get_datetime(end)
    minutes = max(0, int((end_dt - start_dt).total_seconds() // 60))
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        display = f"{hours} ساعة و {mins} دقيقة"
    elif hours:
        display = f"{hours} ساعة"
    else:
        display = f"{mins} دقيقة"
    return {"start": start_dt, "end": end_dt, "minutes": minutes, "display": display}


def _day_tracking(project: str, service_date: str | None = None) -> dict[str, Any]:
    # If no date is explicitly selected, open on the latest day that actually
    # contains project operations instead of today's empty date.
    service_date = str(getdate(service_date)) if service_date else _latest_service_date(project)
    day_start = f"{service_date} 00:00:00"
    day_end = f"{service_date} 23:59:59"

    daily_rows = frappe.get_all(
        "WAFD Daily Meal Plan",
        filters={"project": project, "service_date": service_date},
        fields=["name", "service_date", "status", "total_quantity", "hotel", "production_batch_count"],
        order_by="modified desc",
    )
    batch_rows = frappe.get_all(
        "WAFD Production Batch",
        filters={"project": project, "batch_date": service_date},
        fields=["name", "quality_status", "status", "planned_quantity", "produced_quantity", "rejected_quantity", "completion_percent", "daily_plan", "start_time", "end_time"],
        order_by="modified desc",
    )
    batch_names = [row.name for row in batch_rows]
    quality_rows = []
    if batch_names:
        quality_rows = frappe.get_all(
            "WAFD Quality Inspection",
            filters={"production_batch": ["in", batch_names]},
            fields=["name", "production_batch", "inspection_date", "result", "decision_time"],
            order_by="inspection_date desc",
        )

    packaging_rows = frappe.get_all(
        "WAFD Packaging Record",
        filters={"project": project, "packaging_date": service_date},
        fields=["name", "status", "planned_quantity", "packed_quantity", "rejected_quantity", "completion_percent", "box_count", "ready_for_loading", "start_time", "end_time"],
        order_by="modified desc",
    )
    # Start with loading records on the selected service date. Historical data may
    # have a loading timestamp shortly before midnight / on the previous date while
    # the delivery trip is dated to the service day, so we also merge any loading
    # records explicitly linked from the day's delivery trips below.
    loading_rows = frappe.get_all(
        "WAFD Loading Record",
        filters={"project": project, "loading_date": ["between", [day_start, day_end]]},
        fields=["name", "status", "quantity", "vehicle", "driver", "loading_date", "dispatch_time", "hotel", "box_count", "hot_cabinet_count"],
        order_by="loading_date desc",
    )
    trip_rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"project": project, "trip_date": service_date},
        fields=[
            "name", "status", "quantity", "vehicle", "driver", "hotel", "loading_record", "planned_departure", "actual_departure",
            "planned_arrival", "actual_arrival", "on_time_status", "delay_minutes", "transit_duration_minutes",
        ],
        order_by="actual_departure asc, modified asc",
    )
    trip_names = [row.name for row in trip_rows]

    # Merge loading records referenced by the delivery trips. This makes the
    # loading stage reliable even when legacy/test data has a loading timestamp
    # on the previous calendar date.
    linked_loading_names = [row.get("loading_record") for row in trip_rows if row.get("loading_record")]
    if linked_loading_names:
        linked_rows = frappe.get_all(
            "WAFD Loading Record",
            filters={"name": ["in", linked_loading_names], "project": project},
            fields=["name", "status", "quantity", "vehicle", "driver", "loading_date", "dispatch_time", "hotel", "box_count", "hot_cabinet_count"],
            order_by="loading_date desc",
        )
        by_name = {row.get("name"): row for row in loading_rows}
        for row in linked_rows:
            by_name[row.get("name")] = row
        loading_rows = list(by_name.values())

    receipt_rows = []
    acknowledgement_rows = []
    if trip_names:
        receipt_rows = frappe.get_all(
            "WAFD Receiving Note",
            filters={"delivery_trip": ["in", trip_names]},
            fields=["name", "delivery_trip", "status", "receipt_time", "delivered_quantity", "received_quantity", "rejected_quantity", "condition_status", "receiver_name", "receiver_title"],
            order_by="receipt_time desc",
        )
        acknowledgement_rows = frappe.get_all(
            "WAFD Client Receipt Acknowledgement",
            filters={"delivery_trip": ["in", trip_names]},
            fields=["name", "delivery_trip", "confirmed_at", "received_quantity", "receiver_name", "receiver_title"],
            order_by="confirmed_at desc",
        )

    planned_qty = _sum(daily_rows, "total_quantity")
    produced_qty = _sum(batch_rows, "produced_quantity")
    packed_qty = _sum(packaging_rows, "packed_quantity")
    loaded_qty = _sum(loading_rows, "quantity")
    trip_qty = _sum(trip_rows, "quantity")
    # A receiving note only counts as an actual receipt after its workflow status
    # is explicitly marked Received. Client acknowledgement is also an explicit
    # receipt event. Draft receiving notes must not create a receiver/time.
    completed_receipts = [
        row for row in receipt_rows
        if _safe_status(row.get("status")) == "تم الاستلام / Received"
    ]
    received_qty = _sum(completed_receipts, "received_quantity")
    acknowledged_qty = _sum(acknowledgement_rows, "received_quantity")
    final_received_qty = max(received_qty, acknowledged_qty)

    passed_batches = {
        row.get("production_batch")
        for row in quality_rows
        if _safe_status(row.get("result")) in ("ناجح / Passed", "مشروط / Conditional")
    }
    quality_qty = sum(cint(row.get("produced_quantity")) for row in batch_rows if row.name in passed_batches)

    loading_done = any(_safe_status(row.get("status")) in ("تم التحميل / Loaded", "خرجت / Dispatched") for row in loading_rows) or loaded_qty > 0
    transit_done = any(
        _safe_status(row.get("status")) in ("في الطريق / In Transit", "وصلت / Arrived", "تم التسليم / Delivered") or row.get("actual_departure")
        for row in trip_rows
    )
    arrival_done = any(
        _safe_status(row.get("status")) in ("وصلت / Arrived", "تم التسليم / Delivered") or row.get("actual_arrival")
        for row in trip_rows
    )
    receipt_done = bool(completed_receipts) or bool(acknowledgement_rows)

    stages = [
        {"key":"planned","label":"مجدولة","done": bool(daily_rows), "status": _status_from_rows(daily_rows, "status"), "qty": planned_qty},
        {"key":"production","label":"الإنتاج","done": produced_qty > 0, "status": _status_from_rows(batch_rows, "status") or _status_from_rows(batch_rows, "quality_status"), "qty": produced_qty},
        {"key":"quality","label":"الجودة","done": bool(passed_batches), "status": _status_from_rows(quality_rows, "result"), "qty": quality_qty},
        {"key":"packaging","label":"التغليف","done": packed_qty > 0 or any(row.get("ready_for_loading") for row in packaging_rows), "status": _status_from_rows(packaging_rows, "status"), "qty": packed_qty},
        {"key":"loading","label":"التحميل","done": loading_done, "status": _status_from_rows(loading_rows, "status"), "qty": loaded_qty},
        {"key":"transit","label":"في الطريق","done": transit_done, "status": _status_from_rows(trip_rows, "status"), "qty": trip_qty},
        {"key":"arrival","label":"الوصول","done": arrival_done, "status": ("وصلت / Arrived" if arrival_done else ""), "qty": trip_qty},
        {"key":"receipt","label":"الاستلام","done": receipt_done, "status": _status_from_rows(completed_receipts, "condition_status") or ("مؤكد من الجهة" if acknowledgement_rows else ""), "qty": final_received_qty},
    ]

    # Delivery timing is based on REAL operational events only. Never use planned
    # departure or arrival as a substitute for an actual event, and never use
    # arrival as a substitute for receipt. This prevents false zero-minute trips
    # and false receipt timestamps.
    delivery_start = _first_datetime([row.get("actual_departure") for row in trip_rows])
    if not delivery_start:
        delivery_start = _first_datetime([row.get("dispatch_time") for row in loading_rows])

    actual_arrival = _last_datetime([row.get("actual_arrival") for row in trip_rows])
    receipt_end = _last_datetime([row.get("receipt_time") for row in completed_receipts])
    ack_end = _last_datetime([row.get("confirmed_at") for row in acknowledgement_rows])
    if ack_end and (not receipt_end or ack_end > receipt_end):
        receipt_end = ack_end

    delivery_timing = _duration_payload(delivery_start, receipt_end)
    delivery_timing["arrival"] = actual_arrival

    # Receiver comes only from a completed receiving note or an explicit client
    # acknowledgement. Prefer the latest event and keep name/title together.
    receiver_candidates = []
    for row in completed_receipts:
        if row.get("receipt_time"):
            receiver_candidates.append((get_datetime(row.get("receipt_time")), row.get("receiver_name"), row.get("receiver_title"), row.get("received_quantity"), "receiving_note"))
    for row in acknowledgement_rows:
        if row.get("confirmed_at"):
            receiver_candidates.append((get_datetime(row.get("confirmed_at")), row.get("receiver_name"), row.get("receiver_title"), row.get("received_quantity"), "client_ack"))
    receiver_candidates.sort(key=lambda item: item[0], reverse=True)
    if receiver_candidates:
        _, receiver_name, receiver_title, receiver_qty, receiver_source = receiver_candidates[0]
        delivery_timing["receiver_name"] = receiver_name or ""
        delivery_timing["receiver_title"] = receiver_title or ""
        delivery_timing["received_quantity"] = cint(receiver_qty)
        delivery_timing["receiver_source"] = receiver_source
    else:
        delivery_timing["receiver_name"] = ""
        delivery_timing["receiver_title"] = ""
        delivery_timing["received_quantity"] = 0
        delivery_timing["receiver_source"] = ""

    # Per-trip timing gives large daily clients a useful audit trail while
    # exposing only their assigned project delivery information.
    receipts_by_trip = {row.get("delivery_trip"): row for row in completed_receipts}
    acks_by_trip = {row.get("delivery_trip"): row for row in acknowledgement_rows}
    trip_details = []
    for trip in trip_rows:
        rec = receipts_by_trip.get(trip.name)
        ack = acks_by_trip.get(trip.name)
        start = trip.get("actual_departure")
        if not start and trip.get("loading_record"):
            linked_loading = next((row for row in loading_rows if row.get("name") == trip.get("loading_record")), None)
            start = (linked_loading or {}).get("dispatch_time")
        end = (rec or {}).get("receipt_time") or (ack or {}).get("confirmed_at")
        timing = _duration_payload(start, end)
        trip_details.append({
            **dict(trip),
            "receipt_time": (rec or {}).get("receipt_time") or (ack or {}).get("confirmed_at"),
            "received_quantity": max(cint((rec or {}).get("received_quantity")), cint((ack or {}).get("received_quantity"))),
            "delivery_duration_minutes": timing.get("minutes"),
            "delivery_duration_display": timing.get("display"),
        })

    return {
        "service_date": service_date,
        "planned_quantity": planned_qty,
        "stages": stages,
        "daily_plan": daily_rows[0] if daily_rows else None,
        "production": batch_rows[0] if batch_rows else None,
        "quality": quality_rows[0] if quality_rows else None,
        "packaging": packaging_rows[0] if packaging_rows else None,
        "loading": loading_rows[0] if loading_rows else None,
        "trip": trip_rows[0] if trip_rows else None,
        "receipt": completed_receipts[0] if completed_receipts else None,
        "client_acknowledgement": acknowledgement_rows[0] if acknowledgement_rows else None,
        "receiver": {
            "name": delivery_timing.get("receiver_name") or "",
            "title": delivery_timing.get("receiver_title") or "",
            "received_quantity": delivery_timing.get("received_quantity") or 0,
            "received_at": delivery_timing.get("end"),
        } if receipt_done else None,
        "delivery_timing": delivery_timing,
        "delivery_trips": trip_details,
        "counts": {
            "daily_plans": len(daily_rows), "production_batches": len(batch_rows), "quality_inspections": len(quality_rows),
            "packaging_records": len(packaging_rows), "loading_records": len(loading_rows), "delivery_trips": len(trip_rows),
            "receipts": len(completed_receipts),
        },
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
