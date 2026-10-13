"""Secure, read-only delivery tracking links for selected beneficiaries."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_datetime, get_url, now_datetime


ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"}
MANAGER_ROLES = {"System Manager", "WAFD Operations Manager"}
VIEWER_ROLE = "WAFD Delivery Viewer"


def _check_manager_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("غير مصرح لك بمشاركة متابعة التوصيل / Delivery tracking share access required"), frappe.PermissionError)


def _check_viewer_access():
    if frappe.session.user == "Guest" or VIEWER_ROLE not in frappe.get_roles():
        frappe.throw(_("غير مصرح لك بعرض بيانات التسليم / Delivery data access required"), frappe.PermissionError)


def _clean_token(token):
    token = (token or "").strip()
    if not 32 <= len(token) <= 128 or not all(char.isalnum() or char in "-_" for char in token):
        frappe.throw(_("رابط المتابعة غير صالح أو منتهي / Tracking link is invalid or expired"), frappe.PermissionError)
    return token


def _active_share(token):
    token = _clean_token(token)
    rows = frappe.get_all(
        "WAFD Delivery Tracking Share",
        filters={"share_token": token, "enabled": 1},
        fields=["name", "delivery_trip", "viewer_name", "expires_on", "access_count"],
        limit_page_length=1,
    )
    if not rows or not rows[0].expires_on or get_datetime(rows[0].expires_on) < now_datetime():
        frappe.throw(_("رابط المتابعة غير صالح أو منتهي / Tracking link is invalid or expired"), frappe.PermissionError)
    return rows[0]


def _tracking_url(token):
    return f"{get_url()}/wafd-delivery-tracking?token={quote(token, safe='-_')}"


@frappe.whitelist()
def create_tracking_share(trip_name, viewer_name, viewer_mobile=None, expires_on=None):
    _check_manager_access()
    trip_name = (trip_name or "").strip()
    viewer_name = (viewer_name or "").strip()
    if not frappe.db.exists("WAFD Delivery Trip", trip_name):
        frappe.throw(_("رحلة التوصيل غير موجودة / Delivery trip not found"))
    if not viewer_name:
        frappe.throw(_("أدخل اسم الشخص الذي سيستلم الرابط / Enter the link viewer name"))
    expiry = get_datetime(expires_on) if expires_on else add_days(now_datetime(), 30)
    if expiry <= now_datetime():
        frappe.throw(_("تاريخ انتهاء الرابط يجب أن يكون مستقبلاً / Link expiry must be in the future"))
    doc = frappe.get_doc({
        "doctype": "WAFD Delivery Tracking Share",
        "delivery_trip": trip_name,
        "viewer_name": viewer_name[:140],
        "viewer_mobile": (viewer_mobile or "").strip()[:40],
        "expires_on": expiry,
        "enabled": 1,
    }).insert(ignore_permissions=True)
    return {"name": doc.name, "url": _tracking_url(doc.share_token), "expires_on": doc.expires_on}


@frappe.whitelist()
def get_tracking_shares(trip_name):
    _check_manager_access()
    rows = frappe.get_all(
        "WAFD Delivery Tracking Share",
        filters={"delivery_trip": (trip_name or "").strip()},
        fields=["name", "viewer_name", "viewer_mobile", "expires_on", "enabled", "last_opened_on", "access_count", "share_token"],
        order_by="creation desc",
        limit_page_length=100,
    )
    for row in rows:
        row["url"] = _tracking_url(row.pop("share_token")) if row.enabled else None
    return rows


@frappe.whitelist()
def revoke_tracking_share(share_name):
    _check_manager_access()
    if not frappe.db.exists("WAFD Delivery Tracking Share", share_name):
        frappe.throw(_("الرابط غير موجود / Link not found"))
    frappe.db.set_value("WAFD Delivery Tracking Share", share_name, "enabled", 0)
    return {"name": share_name, "enabled": 0}


@frappe.whitelist()
def list_delivery_viewers():
    """Managers see all employees; supervisors see only approved delivery viewers."""
    _check_manager_access()
    is_manager = bool(set(frappe.get_roles()) & MANAGER_ROLES)
    approved_users = set(frappe.get_all(
        "Has Role", filters={"role": VIEWER_ROLE, "parenttype": "User"}, pluck="parent"
    ))
    users = None
    if not is_manager:
        users = sorted(approved_users)
        if not users:
            return []
    filters = {"enabled": 1, "user_type": "System User"}
    if users is not None:
        filters["name"] = ["in", sorted(set(users))]
    rows = frappe.get_all(
        "User",
        filters=filters,
        fields=["name", "full_name", "email", "mobile_no"],
        order_by="full_name asc",
        limit_page_length=1000,
    )
    return [{**row, "display_name": row.full_name or row.email or row.name,
             "has_viewer_task": row.name in approved_users} for row in rows]


def _prepare_viewer(viewer_user):
    viewer_user = (viewer_user or "").strip().lower()
    user = frappe.db.get_value(
        "User", viewer_user, ["name", "full_name", "email", "mobile_no", "enabled", "user_type"], as_dict=True
    )
    if not user or not user.enabled or user.user_type != "System User":
        frappe.throw(_("اختر حساب موظف مفعلاً / Select an active employee account"))
    roles = set(frappe.get_roles(user.name))
    caller_is_manager = bool(set(frappe.get_roles()) & MANAGER_ROLES)
    if VIEWER_ROLE not in roles:
        if not caller_is_manager:
            frappe.throw(_("اختر حساباً لديه مهمة متابعة بيانات التسليم / Select an approved delivery viewer account"))
        account = frappe.get_doc("User", user.name)
        account.add_roles(VIEWER_ROLE)
    return user


def _assign_one(trip_name, user):
    existing = frappe.db.get_value(
        "WAFD Delivery Tracking Share", {"delivery_trip": trip_name, "viewer_user": user.name}, "name"
    )
    values = {
        "viewer_name": user.full_name or user.email or user.name,
        "viewer_mobile": user.mobile_no or "",
        "expires_on": add_days(now_datetime(), 3650),
        "enabled": 1,
    }
    if existing:
        frappe.db.set_value("WAFD Delivery Tracking Share", existing, values)
        return existing, 0
    doc = frappe.get_doc({
        "doctype": "WAFD Delivery Tracking Share", "delivery_trip": trip_name,
        "viewer_user": user.name, **values,
    }).insert(ignore_permissions=True)
    return doc.name, 1


@frappe.whitelist()
def assign_delivery_viewer(trip_name, viewer_user):
    """Assign a standalone trip or every trip belonging to the same schedule."""
    _check_manager_access()
    trip_name = (trip_name or "").strip()
    if not frappe.db.exists("WAFD Delivery Trip", trip_name):
        frappe.throw(_("رحلة التوصيل غير موجودة / Delivery trip not found"))
    user = _prepare_viewer(viewer_user)
    schedule_id = frappe.db.get_value("WAFD Delivery Trip", trip_name, "delivery_schedule_id")
    trip_names = frappe.get_all(
        "WAFD Delivery Trip", filters={"delivery_schedule_id": schedule_id}, pluck="name", limit_page_length=20000
    ) if schedule_id else [trip_name]
    created = 0
    last_name = None
    for current_trip in trip_names:
        last_name, was_created = _assign_one(current_trip, user)
        created += was_created
    return {"name": last_name, "viewer_user": user.name, "created": created,
            "delivery_schedule_id": schedule_id, "affected_trips": len(trip_names)}


def assign_schedule_viewers(trip_names, viewer_users):
    """Internal bulk assignment used when a recurring delivery table is created."""
    assigned = 0
    for viewer_user in dict.fromkeys(viewer_users or []):
        user = _prepare_viewer(viewer_user)
        for trip_name in trip_names:
            _name, created = _assign_one(trip_name, user)
            assigned += created
    return assigned


def inherit_schedule_viewers(trip_name):
    """Copy viewers from an existing trip when a trip joins a saved schedule."""
    schedule_id = frappe.db.get_value("WAFD Delivery Trip", trip_name, "delivery_schedule_id")
    if not schedule_id:
        return 0
    sibling = frappe.db.get_value(
        "WAFD Delivery Trip", {"delivery_schedule_id": schedule_id, "name": ["!=", trip_name]}, "name"
    )
    if not sibling:
        return 0
    viewers = frappe.get_all(
        "WAFD Delivery Tracking Share",
        filters={"delivery_trip": sibling, "viewer_user": ["is", "set"], "enabled": 1}, pluck="viewer_user"
    )
    assigned = 0
    for viewer_user in viewers:
        user = frappe.db.get_value(
            "User", viewer_user, ["name", "full_name", "email", "mobile_no"], as_dict=True
        )
        if user:
            _name, created = _assign_one(trip_name, user)
            assigned += created
    return assigned


@frappe.whitelist()
def get_trip_viewers(trip_name):
    _check_manager_access()
    schedule_id = frappe.db.get_value("WAFD Delivery Trip", (trip_name or "").strip(), "delivery_schedule_id")
    trip_names = frappe.get_all(
        "WAFD Delivery Trip", filters={"delivery_schedule_id": schedule_id}, pluck="name", limit_page_length=20000
    ) if schedule_id else [(trip_name or "").strip()]
    rows = frappe.get_all(
        "WAFD Delivery Tracking Share",
        filters={"delivery_trip": ["in", trip_names], "viewer_user": ["is", "set"], "enabled": 1},
        fields=["name", "viewer_user", "viewer_name", "viewer_mobile"],
        order_by="creation asc", limit_page_length=1000,
    )
    unique = {}
    for row in rows:
        unique.setdefault(row.viewer_user, row)
    return list(unique.values())


@frappe.whitelist()
def remove_delivery_viewer(share_name):
    _check_manager_access()
    row = frappe.db.get_value(
        "WAFD Delivery Tracking Share", share_name, ["name", "viewer_user"], as_dict=True
    )
    if not row or not row.viewer_user:
        frappe.throw(_("تعيين المستفيد غير موجود / Beneficiary assignment not found"))
    trip_name = frappe.db.get_value("WAFD Delivery Tracking Share", row.name, "delivery_trip")
    schedule_id = frappe.db.get_value("WAFD Delivery Trip", trip_name, "delivery_schedule_id")
    affected = 1
    if schedule_id:
        trip_names = frappe.get_all(
            "WAFD Delivery Trip", filters={"delivery_schedule_id": schedule_id}, pluck="name", limit_page_length=20000
        )
        share_names = frappe.get_all(
            "WAFD Delivery Tracking Share",
            filters={"delivery_trip": ["in", trip_names], "viewer_user": row.viewer_user, "enabled": 1},
            pluck="name", limit_page_length=20000,
        )
        for current_share in share_names:
            frappe.db.set_value("WAFD Delivery Tracking Share", current_share, "enabled", 0)
        affected = len(share_names)
    else:
        frappe.db.set_value("WAFD Delivery Tracking Share", row.name, "enabled", 0)
    return {"name": row.name, "enabled": 0, "affected_trips": affected}


def _delivery_data(trip_name):
    trip = frappe.db.get_value(
        "WAFD Delivery Trip",
        trip_name,
        ["name", "destination_name", "destination_name_en", "meal_type", "quantity", "safandash_count", "hot_cabinet_count", "trip_date", "planned_arrival", "loading_record", "driver", "vehicle", "driver_accepted_on", "actual_departure", "actual_arrival", "status", "delivery_schedule_id", "schedule_customer"],
        as_dict=True,
    )
    if not trip:
        return None
    driver = frappe.db.get_value("WAFD Driver", trip.driver, ["driver_name", "mobile"], as_dict=True) if trip.driver else None
    vehicle = frappe.db.get_value("WAFD Vehicle", trip.vehicle, ["plate_number"], as_dict=True) if trip.vehicle else None
    loading = frappe.db.get_value("WAFD Loading Record", trip.loading_record, ["loading_date", "quantity", "dispatch_time"], as_dict=True) if trip.loading_record else None
    proof_rows = frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": trip.name},
        fields=["receiver_name", "delivery_time", "delivery_photo"],
        order_by="creation desc",
        limit_page_length=1,
    )
    proof = proof_rows[0] if proof_rows else None
    return {
        "name": trip.name,
        "delivery_schedule_id": trip.delivery_schedule_id,
        "schedule_customer": trip.schedule_customer,
        "destination_name": trip.destination_name or trip.destination_name_en or "—",
        "destination_name_en": trip.destination_name_en,
        "meal_type": trip.meal_type,
        "quantity": (loading.quantity if loading else None) or trip.quantity,
        "safandash_count": cint(trip.safandash_count),
        "hot_cabinet_count": cint(trip.hot_cabinet_count),
        "trip_date": trip.trip_date,
        "planned_arrival": trip.planned_arrival,
        "loading_time": loading.loading_date if loading else None,
        "driver_name": driver.driver_name if driver else trip.driver,
        "driver_mobile": driver.mobile if driver else None,
        "plate_number": vehicle.plate_number if vehicle else trip.vehicle,
        "driver_accepted_on": trip.driver_accepted_on or trip.actual_departure,
        "departure_time": trip.actual_departure or (loading.dispatch_time if loading else None),
        "arrival_time": trip.actual_arrival,
        "delivery_time": proof.delivery_time if proof else None,
        "receiver_name": proof.receiver_name if proof else None,
        "has_delivery_photo": bool(proof and proof.delivery_photo),
        "status": "تم التسليم / Delivered" if proof else trip.status,
    }


def _tracking_bucket(row):
    """Use the same mutually exclusive operational states as the supervisor board."""
    if row.get("delivery_time"):
        return "delivered"
    if row.get("status") in {"تم التحميل / Loaded", "في الطريق / In Transit", "وصلت / Arrived"}:
        return "in_transit"
    planned_arrival = row.get("planned_arrival")
    if row.get("status") == "متأخرة / Delayed" or (
        planned_arrival and get_datetime(planned_arrival) < now_datetime()
    ):
        return "attention"
    return "planned"


@frappe.whitelist()
def get_my_delivery_tracking():
    """Read-only delivery list restricted to the signed-in beneficiary account."""
    _check_viewer_access()
    assignments = frappe.get_all(
        "WAFD Delivery Tracking Share",
        filters={"viewer_user": frappe.session.user, "enabled": 1},
        fields=["name", "delivery_trip"],
        order_by="creation desc",
        limit_page_length=5000,
    )
    rows = []
    for assignment in assignments:
        trip = _delivery_data(assignment.delivery_trip)
        if trip:
            trip["assignment_name"] = assignment.name
            trip["board_bucket"] = _tracking_bucket(trip)
            rows.append(trip)
    rows.sort(key=lambda row: str(row.get("planned_arrival") or row.get("trip_date") or ""))
    delivered = [row for row in rows if row["board_bucket"] == "delivered"]
    delivered.sort(key=lambda row: str(row.get("delivery_time") or ""), reverse=True)
    rows = [row for row in rows if row["board_bucket"] != "delivered"] + delivered
    summary = {
        bucket: sum(1 for row in rows if row["board_bucket"] == bucket)
        for bucket in ("in_transit", "planned", "attention", "delivered")
    }
    viewer_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
    return {"read_only": True, "viewer_name": viewer_name, "trips": rows, "summary": summary}


@frappe.whitelist(allow_guest=True)
def get_shared_tracking(token, record_access=1):
    share = _active_share(token)
    trip = _delivery_data(share.delivery_trip)
    if not trip:
        frappe.throw(_("رابط المتابعة غير صالح أو منتهي / Tracking link is invalid or expired"), frappe.PermissionError)
    if cint(record_access):
        frappe.db.set_value(
            "WAFD Delivery Tracking Share",
            share.name,
            {"last_opened_on": now_datetime(), "access_count": cint(share.access_count) + 1},
            update_modified=False,
        )
        # Public tracking is intentionally read through GET; commit this small
        # audit update explicitly because Frappe rolls back writes on safe verbs.
        frappe.db.commit()
    return {
        "read_only": True,
        "viewer_name": share.viewer_name,
        "expires_on": share.expires_on,
        "trip": trip,
    }


def _send_delivery_photo(trip_name):
    proof = frappe.db.get_value(
        "WAFD Delivery Proof", {"delivery_trip": trip_name}, ["delivery_photo"], as_dict=True
    )
    if not proof or not proof.delivery_photo:
        frappe.throw(_("صورة التسليم غير متاحة / Delivery photo is unavailable"))
    file_name = frappe.db.get_value(
        "File",
        {"file_url": proof.delivery_photo, "attached_to_doctype": "WAFD Delivery Trip", "attached_to_name": trip_name},
        "name",
    )
    if not file_name:
        frappe.throw(_("صورة التسليم غير متاحة / Delivery photo is unavailable"), frappe.PermissionError)
    file_doc = frappe.get_doc("File", file_name)
    frappe.local.response.filename = file_doc.file_name
    frappe.local.response.filecontent = file_doc.get_content()
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "inline"


@frappe.whitelist(allow_guest=True)
def get_shared_delivery_photo(token):
    share = _active_share(token)
    _send_delivery_photo(share.delivery_trip)


@frappe.whitelist()
def get_my_delivery_photo(assignment_name):
    _check_viewer_access()
    assignment = frappe.db.get_value(
        "WAFD Delivery Tracking Share",
        {"name": assignment_name, "viewer_user": frappe.session.user, "enabled": 1},
        ["delivery_trip"],
        as_dict=True,
    )
    if not assignment:
        frappe.throw(_("غير مصرح لك بعرض هذه الصورة / Delivery photo access denied"), frappe.PermissionError)
    _send_delivery_photo(assignment.delivery_trip)
