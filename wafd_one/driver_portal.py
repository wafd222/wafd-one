"""Secure mobile delivery workflow for assigned WAFD drivers."""

from __future__ import annotations

import base64
import binascii
import re
import uuid

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from wafd_one.employee_team import _normalize_mobile


DRIVER_ROLE = "WAFD Driver"
LOADING_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"}
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


def _roles(user=None):
    return set(frappe.get_roles(user or frappe.session.user))


def _assert_loading_operator():
    if not (_roles() & LOADING_ROLES):
        frappe.throw(_("غير مصرح لك برفع صورة التحميل."), frappe.PermissionError)


def _driver_name(required=True):
    user = frappe.session.user
    if DRIVER_ROLE not in _roles(user):
        frappe.throw(_("هذه الصفحة مخصصة للسائقين."), frappe.PermissionError)
    driver = frappe.db.get_value("WAFD Driver", {"system_user": user}, "name")
    if required and not driver:
        frappe.throw(_("حساب السائق غير مرتبط بسجل سائق. راجع مدير النظام."))
    return driver


def _assigned_trip(trip_name, write=False):
    driver = _driver_name()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    if trip.driver != driver:
        frappe.throw(_("الرحلة غير مسندة إلى حساب السائق الحالي."), frappe.PermissionError)
    trip.check_permission("write" if write else "read")
    return trip


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
    driver = _driver_name()
    trips = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"driver": driver, "status": ["!=", "ملغية / Cancelled"]},
        fields=[
            "name", "trip_date", "vehicle", "hotel", "quantity", "planned_departure",
            "actual_departure", "planned_arrival", "actual_arrival", "status",
            "delay_minutes", "delay_reason", "notes", "loading_record",
        ],
        order_by="trip_date desc, creation desc",
        limit_page_length=100,
    )
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
        ],
    ) if trips else []
    proof_map = {row.delivery_trip: row for row in proof_rows}
    result = []
    for trip in trips:
        hotel = hotel_map.get(trip.hotel) or {}
        loading = loading_map.get(trip.loading_record) or {}
        proof = proof_map.get(trip.name)
        result.append(
            {
                **trip,
                "hotel_name_ar": hotel.get("hotel_name_ar") or trip.hotel,
                "hotel_name_en": hotel.get("hotel_name_en") or trip.hotel,
                "map_url": hotel.get("map_url"),
                "loading": loading,
                "proof": proof,
            }
        )
    return {"driver": driver, "trips": result}


@frappe.whitelist()
def set_my_trip_status(trip_name, action):
    trip = _assigned_trip(trip_name, write=True)
    transitions = {
        "start": ({"مخططة / Planned", "تم التحميل / Loaded"}, "في الطريق / In Transit"),
        "arrive": ({"في الطريق / In Transit", "متأخرة / Delayed"}, "وصلت / Arrived"),
    }
    if action not in transitions:
        frappe.throw(_("إجراء الرحلة غير مسموح."))
    allowed_from, target = transitions[action]
    if trip.status not in allowed_from:
        frappe.throw(_("حالة الرحلة الحالية لا تسمح بهذا الإجراء."))
    if action == "start":
        loading_photo = frappe.db.get_value("WAFD Loading Record", trip.loading_record, "loading_photo")
        if not loading_photo:
            frappe.throw(_("لا يمكن بدء الرحلة قبل توثيق صورة التحميل."))
        trip.actual_departure = trip.actual_departure or now_datetime()
    if action == "arrive":
        trip.actual_arrival = trip.actual_arrival or now_datetime()
    trip.status = target
    trip.save()
    return {"name": trip.name, "status": trip.status}


@frappe.whitelist()
def submit_delivery_proof(
    trip_name,
    receiver_name,
    received_quantity,
    rejected_quantity=0,
    status="مقبول بالكامل / Fully Accepted",
    receiver_mobile=None,
    signature_data=None,
    image_data=None,
    notes=None,
    notes_language="ar",
    operational_note_code=None,
):
    trip = _assigned_trip(trip_name, write=True)
    if trip.status not in {"في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed"}:
        frappe.throw(_("ابدأ الرحلة وسجل الوصول قبل إثبات التسليم."))
    existing = frappe.db.get_value("WAFD Delivery Proof", {"delivery_trip": trip.name}, "name")
    if existing:
        return {"name": existing, "created": False}
    valid_statuses = {
        "مقبول بالكامل / Fully Accepted",
        "مقبول جزئياً / Partially Accepted",
        "مرفوض / Rejected",
    }
    if status not in valid_statuses:
        frappe.throw(_("نتيجة الاستلام غير صحيحة."))
    receiver_name = (receiver_name or "").strip()
    if not receiver_name:
        frappe.throw(_("اسم المستلم مطلوب."))
    received_quantity = cint(received_quantity)
    rejected_quantity = cint(rejected_quantity)
    if min(received_quantity, rejected_quantity) < 0 or received_quantity + rejected_quantity != cint(trip.quantity):
        frappe.throw(_("يجب أن يساوي مجموع الكمية المستلمة والمرفوضة كمية الرحلة."))
    if status == "مقبول بالكامل / Fully Accepted" and rejected_quantity:
        frappe.throw(_("القبول الكامل لا يسمح بكمية مرفوضة."))
    if status == "مقبول جزئياً / Partially Accepted" and (not received_quantity or not rejected_quantity):
        frappe.throw(_("القبول الجزئي يتطلب كمية مستلمة وكمية مرفوضة."))
    if status == "مرفوض / Rejected" and (received_quantity or rejected_quantity != cint(trip.quantity)):
        frappe.throw(_("عند الرفض يجب أن تكون كامل كمية الرحلة مرفوضة."))
    if not image_data:
        frappe.throw(_("صورة التسليم مطلوبة."))
    if status != "مرفوض / Rejected" and not signature_data:
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
        trip.actual_arrival = trip.actual_arrival or now_datetime()
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
            "delivery_time": now_datetime(),
            "received_quantity": received_quantity,
            "rejected_quantity": rejected_quantity,
            "receiver_name": receiver_name,
            "receiver_mobile": receiver_mobile,
            "receiver_signature": signature_data,
            "delivery_photo": file_url,
            "delivery_photo_uploaded_by": frappe.session.user,
            "delivery_photo_uploaded_on": now_datetime(),
            "status": status,
            "notes": display_notes,
            "notes_original": notes_original,
            "notes_language": notes_language,
            "notes_translation_ar": translated_ar,
            "operational_note_code": operational_note_code,
        }
    )
    proof.insert(ignore_permissions=True)
    return {"name": proof.name, "created": True, "status": proof.status}
