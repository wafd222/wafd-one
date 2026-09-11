"""Secure, read-only delivery tracking links for selected beneficiaries."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_datetime, get_url, now_datetime


ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"}


def _check_manager_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("غير مصرح لك بمشاركة متابعة التوصيل / Delivery tracking share access required"), frappe.PermissionError)


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


@frappe.whitelist(allow_guest=True)
def get_shared_tracking(token, record_access=1):
    share = _active_share(token)
    trip = frappe.db.get_value(
        "WAFD Delivery Trip",
        share.delivery_trip,
        ["name", "destination_name", "destination_name_en", "meal_type", "quantity", "trip_date", "loading_record", "driver", "vehicle", "driver_accepted_on", "actual_departure", "actual_arrival", "status"],
        as_dict=True,
    )
    if not trip:
        frappe.throw(_("رابط المتابعة غير صالح أو منتهي / Tracking link is invalid or expired"), frappe.PermissionError)
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
        "trip": {
            "destination_name": trip.destination_name or trip.destination_name_en or "—",
            "meal_type": trip.meal_type,
            "quantity": (loading.quantity if loading else None) or trip.quantity,
            "trip_date": trip.trip_date,
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
        },
    }


@frappe.whitelist(allow_guest=True)
def get_shared_delivery_photo(token):
    share = _active_share(token)
    proof = frappe.db.get_value(
        "WAFD Delivery Proof", {"delivery_trip": share.delivery_trip}, ["delivery_photo"], as_dict=True
    )
    if not proof or not proof.delivery_photo:
        frappe.throw(_("صورة التسليم غير متاحة / Delivery photo is unavailable"))
    file_name = frappe.db.get_value(
        "File",
        {"file_url": proof.delivery_photo, "attached_to_doctype": "WAFD Delivery Trip", "attached_to_name": share.delivery_trip},
        "name",
    )
    if not file_name:
        frappe.throw(_("صورة التسليم غير متاحة / Delivery photo is unavailable"), frappe.PermissionError)
    file_doc = frappe.get_doc("File", file_name)
    frappe.local.response.filename = file_doc.file_name
    frappe.local.response.filecontent = file_doc.get_content()
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "inline"
