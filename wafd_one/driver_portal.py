"""Secure mobile delivery workflow for assigned WAFD drivers."""

from __future__ import annotations

import base64
import binascii
import re
import uuid
from datetime import timedelta
from urllib.parse import quote_plus

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from wafd_one.driver_security import (
    get_drivers_for_user,
    repair_trip_assignments,
    trip_is_assigned_to_user,
    trips_for_user,
)
from wafd_one.employee_team import _normalize_mobile
from wafd_one.delivery_reconciliation import reconcile_missing_delivery_trips


DRIVER_ROLE = "WAFD Driver"
LOADING_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"}
DELIVERY_OPERATOR_ROLES = LOADING_ROLES
ALLOWED_LANGUAGES = {"ar", "en", "id", "ur", "hi", "bn", "fr", "ha", "sw", "uz"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
IMAGE_MIMES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
QUICK_NOTES_AR = {
    "delivered_ok": "تم التسليم بالكامل دون ملاحظات",
    "receiver_delay": "تأخر حضور المستلم",
    "quantity_issue": "يوجد اختلاف في الكمية",
    "access_issue": "تعذر الوصول إلى موقع التسليم",
    "receiver_refused": "رفض المستلم استلام الشحنة",
}
SEQUENCE_GRACE_HOURS = 2
LOCKED_PREVIEW_COUNT = 2
OFFLINE_PRELOAD_COUNT = 100
DRIVER_QUEUE_LIMIT = 10000


def _roles(user=None):
    return set(frappe.get_roles(user or frappe.session.user))


def _assert_loading_operator():
    if not (_roles() & LOADING_ROLES):
        frappe.throw(_("غير مصرح لك برفع صورة التحميل."), frappe.PermissionError)


def _driver_names(required=True):
    user = frappe.session.user
    if DRIVER_ROLE not in _roles(user):
        frappe.throw(_("هذه الصفحة مخصصة للسائقين."), frappe.PermissionError)
    drivers = get_drivers_for_user(user)
    if required and not drivers:
        frappe.throw(_("حساب السائق غير مرتبط بسجل سائق. راجع مدير النظام."))
    return list(dict.fromkeys(drivers))


def _driver_name(required=True):
    drivers = _driver_names(required=required)
    return drivers[0] if drivers else None


def _authorized_trip(trip_name, write=False):
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    if not (_roles() & DELIVERY_OPERATOR_ROLES):
        _driver_names()
        if not trip_is_assigned_to_user(
            trip.driver, getattr(trip, "assigned_driver_user", None), frappe.session.user
        ):
            frappe.throw(_("الرحلة غير مسندة إلى حساب السائق الحالي."), frappe.PermissionError)
    trip.check_permission("write" if write else "read")
    return trip


def _assigned_trip(trip_name, write=False):
    """Backward-compatible alias for the secured delivery authorization."""
    return _authorized_trip(trip_name, write=write)


def _sequence_metadata(trips, proof_trip_names, current_time=None):
    """Mark the chronological driver queue without hiding missed evidence work.

    A delivery without proof stops later deliveries until it is documented.  Once
    its planned time is two hours old it remains visible as missed/actionable, but
    no longer blocks the next delivery.
    """
    current_time = current_time or now_datetime()
    blocking_trip = None
    metadata = {}
    total = len(trips)
    for index, trip in enumerate(trips, start=1):
        if trip.name in proof_trip_names:
            metadata[trip.name] = {
                "sequence_state": "completed", "sequence_actionable": False,
                "sequence_index": index, "sequence_total": total,
            }
            continue
        planned = get_datetime(trip.planned_arrival or trip.trip_date)
        unlock_at = planned + timedelta(hours=SEQUENCE_GRACE_HOURS) if planned else None
        overdue = bool(unlock_at and current_time >= unlock_at)
        if blocking_trip is None and overdue:
            metadata[trip.name] = {
                "sequence_state": "missed", "sequence_actionable": True,
                "sequence_index": index, "sequence_total": total,
                "unlock_at": unlock_at,
            }
        elif blocking_trip is None:
            blocking_trip = trip
            metadata[trip.name] = {
                "sequence_state": "active", "sequence_actionable": True,
                "sequence_index": index, "sequence_total": total,
                "unlock_at": unlock_at,
            }
        else:
            metadata[trip.name] = {
                "sequence_state": "locked", "sequence_actionable": False,
                "sequence_index": index, "sequence_total": total,
                "blocked_by": blocking_trip.name,
                "unlock_at": get_datetime(blocking_trip.planned_arrival or blocking_trip.trip_date) + timedelta(hours=SEQUENCE_GRACE_HOURS),
            }
    return metadata


def _driver_queue(user):
    rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"status": ["!=", "ملغية / Cancelled"], "archived_from_board": 0},
        fields=["name", "trip_date", "planned_arrival", "driver", "assigned_driver_user"],
        order_by="planned_arrival asc, creation asc",
        limit_page_length=DRIVER_QUEUE_LIMIT,
    )
    rows = trips_for_user(rows, user)
    proofs = set(frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": ["in", [row.name for row in rows]]},
        pluck="delivery_trip",
        limit_page_length=DRIVER_QUEUE_LIMIT,
    )) if rows else set()
    return rows, proofs, _sequence_metadata(rows, proofs)


def _assert_sequence_actionable(trip):
    if _roles() & DELIVERY_OPERATOR_ROLES:
        return
    rows, proofs, metadata = _driver_queue(frappe.session.user)
    state = metadata.get(trip.name) or {}
    if trip.name in proofs:
        frappe.throw(_("تم توثيق هذه الرحلة مسبقاً."))
    if not state.get("sequence_actionable"):
        frappe.throw(_("هذه الرحلة مقفلة. وثّق الرحلة السابقة أولاً، أو انتظر مرور ساعتين من وقتها المخطط."))


def _same_delivery_run_rows(trip):
    """Return one vehicle departure run for a driver, date and meal.

    A vehicle leaves once for all destinations of the same meal run. Destination
    arrival and proof remain separate, while their departure timestamp is shared.
    """
    filters = {
        "trip_date": trip.trip_date,
        "driver": trip.driver,
        "meal_type": trip.meal_type,
        "status": ["!=", "ملغية / Cancelled"],
        "archived_from_board": 0,
    }
    filters["vehicle"] = trip.vehicle if trip.vehicle else ["is", "not set"]
    rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters=filters,
        fields=[
            "name", "status", "actual_departure", "driver_accepted_on",
            "planned_arrival", "loading_record", "driver", "assigned_driver_user",
        ],
        order_by="planned_arrival asc, creation asc",
        limit_page_length=1000,
    )
    if _roles() & DELIVERY_OPERATOR_ROLES:
        return rows
    user = frappe.session.user
    return [
        row for row in rows
        if trip_is_assigned_to_user(row.driver, row.assigned_driver_user, user)
    ]


def _validated_offline_time(value):
    """Accept a recent device timestamp while rejecting impossible future data."""
    captured = get_datetime(value) if value else now_datetime()
    if getattr(captured, "tzinfo", None):
        captured = captured.astimezone().replace(tzinfo=None)
    current = now_datetime()
    if captured > current + timedelta(minutes=10):
        frappe.throw(_("وقت العملية من الهاتف يقع في المستقبل. صحح وقت الجهاز ثم أعد المزامنة."))
    if captured < current - timedelta(days=30):
        frappe.throw(_("العملية المحفوظة أقدم من 30 يوماً وتحتاج مراجعة المشرف."))
    return captured


def _start_delivery_run(trip, captured_at=None):
    """Start every destination on the same vehicle meal run at one timestamp."""
    rows = _same_delivery_run_rows(trip)
    if not rows:
        rows = [trip]

    existing_times = []
    for row in rows:
        for value in (row.actual_departure, row.driver_accepted_on):
            if value:
                existing_times.append(get_datetime(value))
    requested_time = _validated_offline_time(captured_at) if captured_at else None
    departure_candidates = existing_times + ([requested_time] if requested_time else [])
    departure_time = min(departure_candidates) if departure_candidates else now_datetime()

    startable_statuses = {
        "مخططة / Planned", "تم التحميل / Loaded", "متأخرة / Delayed",
    }
    startable = [row for row in rows if row.status in startable_statuses]

    missing_loading_photos = []
    for row in startable:
        if row.loading_record and not frappe.db.get_value(
            "WAFD Loading Record", row.loading_record, "loading_photo"
        ):
            missing_loading_photos.append(row.name)
    if missing_loading_photos:
        frappe.throw(_("لا يمكن بدء جولة التوصيل قبل توثيق صور التحميل لجميع رحلاتها."))

    updated_names = []
    for row in startable:
        delay_minutes = 0
        on_time_status = "غير محدد / Not Set"
        if row.planned_arrival:
            delay_minutes = max(int(
                (departure_time - get_datetime(row.planned_arrival)).total_seconds() // 60
            ), 0)
            on_time_status = "متأخر / Delayed" if delay_minutes else "في الوقت / On Time"
        frappe.db.set_value(
            "WAFD Delivery Trip",
            row.name,
            {
                "driver_accepted_on": departure_time,
                "actual_departure": departure_time,
                "status": "في الطريق / In Transit",
                "delay_minutes": delay_minutes,
                "on_time_status": on_time_status,
                "transit_duration_minutes": 0,
            },
        )
        if row.loading_record:
            frappe.db.set_value(
                "WAFD Loading Record",
                row.loading_record,
                {"status": "خرجت / Dispatched", "dispatch_time": departure_time},
                update_modified=False,
            )
        frappe.get_doc("WAFD Delivery Trip", row.name).notify_update()
        updated_names.append(row.name)

    if trip.vehicle and frappe.db.exists("WAFD Vehicle", trip.vehicle):
        frappe.db.set_value(
            "WAFD Vehicle", trip.vehicle, "status", "في مهمة / On Trip",
            update_modified=False,
        )
    if trip.driver and frappe.db.exists("WAFD Driver", trip.driver):
        frappe.db.set_value(
            "WAFD Driver", trip.driver, "status", "في مهمة / On Trip",
            update_modified=False,
        )
    return departure_time, updated_names


def _decode_image(data_url):
    value = str(data_url or "").strip()
    match = re.fullmatch(r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\r\n]+)", value)
    if not match:
        frappe.throw(_("صيغة الصورة غير مدعومة. استخدم صورة JPG أو PNG أو WebP."))
    mime = match.group(1).lower()
    if mime not in IMAGE_MIMES:
        frappe.throw(_("نوع الصورة غير مدعوم."))
    try:
        content = base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError):
        frappe.throw(_("تعذر قراءة الصورة المرفوعة."))
    if not content:
        frappe.throw(_("الصورة المرفوعة فارغة."))
    if len(content) > MAX_IMAGE_BYTES:
        frappe.throw(_("حجم الصورة كبير. الحد الأقصى 8 ميجابايت."))
    signatures = (
        content.startswith(b"\xff\xd8\xff"),
        content.startswith(b"\x89PNG\r\n\x1a\n"),
        content.startswith(b"RIFF") and content[8:12] == b"WEBP",
        len(content) > 12 and content[4:12] in {b"ftypheic", b"ftypheix", b"ftyphevc", b"ftyphevx", b"ftypmif1"},
    )
    if not any(signatures):
        frappe.throw(_("محتوى الملف ليس صورة صالحة."))
    return mime, content


def _save_private_image(data_url, prefix, attached_to_doctype, attached_to_name, attached_to_field):
    mime, content = _decode_image(data_url)
    file_name = f"{prefix}-{uuid.uuid4().hex[:10]}{IMAGE_MIMES[mime]}"
    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": attached_to_doctype,
            "attached_to_name": attached_to_name,
            "attached_to_field": attached_to_field,
            "is_private": 1,
            "content": content,
        }
    ).insert(ignore_permissions=True)
    return file_doc.file_url


@frappe.whitelist()
def upload_loading_photo(loading_name, image_data):
    """Upload loading evidence without granting broad File permissions."""
    _assert_loading_operator()
    loading = frappe.get_doc("WAFD Loading Record", loading_name)
    loading.check_permission("write")
    if loading.status == "خرجت / Dispatched" or frappe.db.exists(
        "WAFD Delivery Trip",
        {"loading_record": loading.name, "status": ["!=", "ملغية / Cancelled"]},
    ):
        frappe.throw(_("لا يمكن استبدال صورة التحميل بعد إنشاء الرحلة."))
    file_url = _save_private_image(
        image_data,
        "loading",
        "WAFD Loading Record",
        loading.name,
        "loading_photo",
    )
    loading.loading_photo = file_url
    loading.supervisor = frappe.session.user
    loading.loading_photo_uploaded_by = frappe.session.user
    loading.loading_photo_uploaded_on = now_datetime()
    loading.save()
    return {
        "file_url": file_url,
        "supervisor": loading.supervisor,
        "uploaded_on": loading.loading_photo_uploaded_on,
        "status": loading.status,
    }


def _hotel_names(hotel_names):
    if not hotel_names:
        return {}
    return {
        row.name: row
        for row in frappe.get_all(
            "WAFD Hotel",
            filters={"name": ["in", list(hotel_names)]},
            fields=["name", "hotel_name_ar", "hotel_name_en", "map_url"],
        )
    }


@frappe.whitelist()
def list_my_trips():
    is_manager = bool(_roles() & DELIVERY_OPERATOR_ROLES)
    drivers = [] if is_manager else _driver_names()
    filters = {"status": ["!=", "ملغية / Cancelled"], "archived_from_board": 0}
    if not is_manager:
        repair_trip_assignments(frappe.session.user)
    reconciliation = reconcile_missing_delivery_trips(
        user=None if is_manager else frappe.session.user,
        all_drivers=is_manager,
    )
    trips = frappe.get_all(
        "WAFD Delivery Trip",
        filters=filters,
        fields=[
            "name", "trip_date", "vehicle", "hotel", "quantity", "planned_departure",
            "actual_departure", "planned_arrival", "actual_arrival", "status",
            "delay_minutes", "delay_reason", "notes", "loading_record", "driver",
            "assigned_driver_user", "trip_source", "delivery_kind", "delivery_location",
            "destination_name", "destination_name_en", "destination_map_url",
            "destination_latitude", "destination_longitude", "meal_type", "delivery_schedule_id",
        ],
        order_by="trip_date desc, creation desc" if is_manager else "planned_arrival asc, creation asc",
        # Managers see the operational window directly. Drivers are filtered
        # immediately below before any response is built, so no other driver's
        # row can leave the server.
        limit_page_length=DRIVER_QUEUE_LIMIT if not is_manager else 100,
    )
    if not is_manager:
        trips = trips_for_user(trips, frappe.session.user)
    hotel_map = _hotel_names({row.hotel for row in trips if row.hotel})
    loading_names = [row.loading_record for row in trips if row.loading_record]
    loading_map = {
        row.name: row
        for row in frappe.get_all(
            "WAFD Loading Record",
            filters={"name": ["in", loading_names]},
            fields=[
                "name", "loading_photo", "supervisor", "seal_number", "box_count",
                "hot_cabinet_count", "hot_cabinet_sandwich_total", "temperature_at_loading",
                "loading_photo_uploaded_by", "loading_photo_uploaded_on",
            ],
            limit_page_length=DRIVER_QUEUE_LIMIT,
        )
    } if loading_names else {}
    proof_rows = frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": ["in", [row.name for row in trips]]},
        fields=[
            "name", "delivery_trip", "delivery_time", "receiver_name", "received_quantity",
            "rejected_quantity", "delivery_photo", "status", "notes", "notes_original",
            "notes_language", "notes_translation_ar", "operational_note_code",
            "delivery_photo_uploaded_by", "delivery_photo_uploaded_on",
            "latitude", "longitude",
        ],
        limit_page_length=DRIVER_QUEUE_LIMIT,
    ) if trips else []
    proof_map = {row.delivery_trip: row for row in proof_rows}
    sequence = {}
    hidden_upcoming_count = 0
    if not is_manager:
        sequence = _sequence_metadata(trips, set(proof_map))
        visible_names = []
        rendered_names = []
        locked_seen = 0
        locked_preloaded = 0
        for trip in trips:
            state = sequence.get(trip.name, {}).get("sequence_state")
            if state in {"missed", "active"}:
                visible_names.append(trip.name)
                rendered_names.append(trip.name)
            elif state == "locked":
                if locked_preloaded < OFFLINE_PRELOAD_COUNT:
                    visible_names.append(trip.name)
                    locked_preloaded += 1
                if locked_seen < LOCKED_PREVIEW_COUNT:
                    rendered_names.append(trip.name)
                    locked_seen += 1
                else:
                    hidden_upcoming_count += 1
        visible = set(visible_names)
        rendered = set(rendered_names)
        trips = [trip for trip in trips if trip.name in visible]
    result = []
    for trip in trips:
        hotel = hotel_map.get(trip.hotel) or {}
        loading = loading_map.get(trip.loading_record) or {}
        proof = proof_map.get(trip.name)
        destination_label = trip.destination_name or hotel.get("hotel_name_ar") or trip.hotel or ""
        fallback_map_url = (
            f"https://www.google.com/maps/search/?api=1&query={quote_plus(destination_label)}"
            if destination_label else None
        )
        result.append(
            {
                **trip,
                "hotel_name_ar": hotel.get("hotel_name_ar") or trip.hotel,
                "hotel_name_en": hotel.get("hotel_name_en") or trip.hotel,
                "map_url": trip.destination_map_url or hotel.get("map_url") or fallback_map_url,
                "simple_delivery": trip.trip_source == "خطة مشرف التوصيل / Delivery Supervisor Plan",
                "loading": loading,
                "proof": proof,
                "sequence_visible": is_manager or trip.name in rendered,
                **sequence.get(trip.name, {}),
            }
        )
    blocked = reconciliation["counts"].get("blocked", 0)
    if result:
        empty_reason = None
    elif blocked:
        empty_reason = "trip_creation_blocked"
    elif reconciliation["results"]:
        # Approved loading rows were found but no visible trip survived the
        # secured retrieval.  Keep this distinct from a missing loading.
        empty_reason = "assignment_incomplete"
    else:
        empty_reason = "no_approved_loading"
    return {
        "driver": drivers[0] if drivers else None,
        "drivers": drivers,
        "is_manager": is_manager,
        "trips": result,
        "hidden_upcoming_count": hidden_upcoming_count,
        "sequence_grace_hours": SEQUENCE_GRACE_HOURS,
        "empty_reason": empty_reason,
        "reconciliation": {
            "counts": reconciliation["counts"],
            "blocked": [
                {
                    "loading": row.get("loading"),
                    "reason": row.get("reason"),
                    "message": row.get("message"),
                }
                for row in reconciliation["results"]
                if row.get("state") == "blocked"
            ],
        },
    }


@frappe.whitelist()
def set_my_trip_status(trip_name, action):
    trip = _authorized_trip(trip_name, write=True)
    _assert_sequence_actionable(trip)
    transitions = {
        "start": ({"مخططة / Planned", "تم التحميل / Loaded", "متأخرة / Delayed"}, "في الطريق / In Transit"),
        "arrive": ({"في الطريق / In Transit", "متأخرة / Delayed"}, "وصلت / Arrived"),
    }
    if action not in transitions:
        frappe.throw(_("إجراء الرحلة غير مسموح."))
    allowed_from, target = transitions[action]
    if trip.status not in allowed_from:
        frappe.throw(_("حالة الرحلة الحالية لا تسمح بهذا الإجراء."))
    if action == "start":
        departure_time, updated_names = _start_delivery_run(trip)
        return {
            "name": trip.name,
            "status": "في الطريق / In Transit",
            "departure_time": departure_time,
            "started_trip_names": updated_names,
            "started_count": len(updated_names),
        }
    if action == "arrive":
        if not trip.actual_departure:
            frappe.throw(_("ابدأ الرحلة أولاً قبل تسجيل الوصول / Start the trip before marking arrival."))
        trip.actual_arrival = trip.actual_arrival or now_datetime()
    trip.status = target
    trip.save()
    trip.notify_update()
    return {"name": trip.name, "status": trip.status}


@frappe.whitelist()
def upload_delivery_photo(trip_name, image_data):
    """Secure upload for the standard manager proof form and mobile page."""
    trip = _authorized_trip(trip_name, write=True)
    _assert_sequence_actionable(trip)
    if trip.status not in {"في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed"}:
        frappe.throw(_("ابدأ الرحلة أو سجل الوصول قبل تصوير التسليم."))
    if frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": trip.name}):
        frappe.throw(_("تم حفظ إثبات التسليم بالفعل ولا يمكن استبدال صورته من هنا."))
    file_url = _save_private_image(
        image_data,
        "delivery",
        "WAFD Delivery Trip",
        trip.name,
        "delivery_photo",
    )
    uploaded_on = now_datetime()
    return {
        "file_url": file_url,
        "uploaded_by": frappe.session.user,
        "uploaded_on": uploaded_on,
    }


@frappe.whitelist()
def submit_delivery_proof(
    trip_name,
    receiver_name=None,
    received_quantity=0,
    rejected_quantity=0,
    status="مقبول بالكامل / Fully Accepted",
    receiver_mobile=None,
    signature_data=None,
    image_data=None,
    notes=None,
    notes_language="ar",
    operational_note_code=None,
    latitude=None,
    longitude=None,
    captured_at=None,
):
    trip = _authorized_trip(trip_name, write=True)
    existing = frappe.db.get_value("WAFD Delivery Proof", {"delivery_trip": trip.name}, "name")
    if existing:
        return {"name": existing, "created": False}
    _assert_sequence_actionable(trip)
    if trip.status not in {"في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed"}:
        frappe.throw(_("ابدأ الرحلة وسجل الوصول قبل إثبات التسليم."))
    delivery_time = _validated_offline_time(captured_at) if captured_at else now_datetime()
    valid_statuses = {
        "مقبول بالكامل / Fully Accepted",
        "مقبول جزئياً / Partially Accepted",
        "مرفوض / Rejected",
    }
    if status not in valid_statuses:
        frappe.throw(_("نتيجة الاستلام غير صحيحة."))
    simple_delivery = trip.trip_source == "خطة مشرف التوصيل / Delivery Supervisor Plan"
    receiver_name = (receiver_name or "").strip()
    if simple_delivery and not receiver_name:
        receiver_name = trip.destination_name or "تسليم مصور / Photo Delivery"
    if not receiver_name:
        frappe.throw(_("اسم المستلم مطلوب."))
    received_quantity = cint(received_quantity)
    rejected_quantity = cint(rejected_quantity)
    if min(received_quantity, rejected_quantity) < 0 or (cint(trip.quantity) and received_quantity + rejected_quantity != cint(trip.quantity)):
        frappe.throw(_("يجب أن يساوي مجموع الكمية المستلمة والمرفوضة كمية الرحلة."))
    if status == "مقبول بالكامل / Fully Accepted" and rejected_quantity:
        frappe.throw(_("القبول الكامل لا يسمح بكمية مرفوضة."))
    if status == "مقبول جزئياً / Partially Accepted" and (not received_quantity or not rejected_quantity):
        frappe.throw(_("القبول الجزئي يتطلب كمية مستلمة وكمية مرفوضة."))
    if status == "مرفوض / Rejected" and (received_quantity or rejected_quantity != cint(trip.quantity)):
        frappe.throw(_("عند الرفض يجب أن تكون كامل كمية الرحلة مرفوضة."))
    if not image_data:
        frappe.throw(_("صورة التسليم مطلوبة."))
    if simple_delivery and (latitude in (None, "") or longitude in (None, "")):
        frappe.throw(_("موقع التسليم مطلوب. اسمح بالوصول إلى الموقع من إعدادات الهاتف."))
    if not simple_delivery and status != "مرفوض / Rejected" and not signature_data:
        frappe.throw(_("توقيع المستلم مطلوب."))
    if signature_data:
        _decode_image(signature_data)
    receiver_mobile = _normalize_mobile(receiver_mobile, required=False)
    if notes_language not in ALLOWED_LANGUAGES:
        notes_language = "ar"
    operational_note_code = (operational_note_code or "").strip()
    if operational_note_code and operational_note_code not in QUICK_NOTES_AR:
        frappe.throw(_("الملاحظة التشغيلية غير صحيحة."))
    notes_original = (notes or "").strip()
    quick_note_ar = QUICK_NOTES_AR.get(operational_note_code, "")
    translated_parts = [quick_note_ar]
    if notes_language == "ar" and notes_original:
        translated_parts.append(notes_original)
    translated_ar = "\n".join(part for part in translated_parts if part)
    # Never discard a free-text note. If no Arabic translation is available,
    # the manager still sees the exact original text and its source language.
    display_notes = "\n".join(part for part in (translated_ar, notes_original if notes_language != "ar" else "") if part)

    if trip.status in {"في الطريق / In Transit", "متأخرة / Delayed"}:
        trip.status = "وصلت / Arrived"
        trip.actual_arrival = trip.actual_arrival or delivery_time
        trip.save()

    file_url = _save_private_image(
        image_data,
        "delivery",
        "WAFD Delivery Trip",
        trip.name,
        "delivery_photo",
    )
    proof = frappe.get_doc(
        {
            "doctype": "WAFD Delivery Proof",
            "delivery_trip": trip.name,
            "delivery_time": delivery_time,
            "received_quantity": received_quantity,
            "rejected_quantity": rejected_quantity,
            "receiver_name": receiver_name,
            "receiver_mobile": receiver_mobile,
            "receiver_signature": signature_data,
            "delivery_photo": file_url,
            "delivery_photo_uploaded_by": frappe.session.user,
            "delivery_photo_uploaded_on": delivery_time,
            "latitude": latitude,
            "longitude": longitude,
            "status": status,
            "notes": display_notes,
            "notes_original": notes_original,
            "notes_language": notes_language,
            "notes_translation_ar": translated_ar,
            "operational_note_code": operational_note_code,
        }
    )
    proof.insert(ignore_permissions=True)
    return {
        "name": proof.name,
        "created": True,
        "status": proof.status,
        "trip_status": "تم التسليم / Delivered",
    }


@frappe.whitelist()
def sync_offline_driver_action(trip_name, action, captured_at, payload=None):
    """Replay one driver action captured offline in chronological order.

    Every branch is idempotent so a connection loss after the server commit
    cannot create a second proof or replace the original operational time.
    """
    if action not in {"start", "arrive", "proof"}:
        frappe.throw(_("نوع عملية المزامنة غير صحيح."))
    trip = _authorized_trip(trip_name, write=True)
    captured = _validated_offline_time(captured_at)

    if action == "start":
        if trip.actual_departure:
            return {"name": trip.name, "action": action, "already_synced": True}
        _assert_sequence_actionable(trip)
        departure_time, updated_names = _start_delivery_run(trip, captured)
        return {
            "name": trip.name, "action": action, "departure_time": departure_time,
            "started_trip_names": updated_names,
        }

    if action == "arrive":
        if trip.actual_arrival or frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": trip.name}):
            return {"name": trip.name, "action": action, "already_synced": True}
        _assert_sequence_actionable(trip)
        if not trip.actual_departure:
            frappe.throw(_("تعذر مزامنة الوصول قبل مزامنة بدء الرحلة."))
        trip.actual_arrival = captured
        trip.status = "وصلت / Arrived"
        trip.save()
        trip.notify_update()
        return {"name": trip.name, "action": action, "arrival_time": captured}

    values = frappe.parse_json(payload) if payload else {}
    if not isinstance(values, dict):
        frappe.throw(_("بيانات إثبات التسليم المحفوظة غير صحيحة."))
    allowed = {
        "receiver_name", "received_quantity", "rejected_quantity", "status",
        "receiver_mobile", "signature_data", "image_data", "notes",
        "notes_language", "operational_note_code", "latitude", "longitude",
    }
    proof_values = {key: values.get(key) for key in allowed if key in values}
    return submit_delivery_proof(
        trip_name=trip.name,
        captured_at=captured,
        **proof_values,
    )
