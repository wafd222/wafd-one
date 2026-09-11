"""Simple delivery planning board for supervisors, management and drivers."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, getdate, nowdate


ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"}
MEAL_TIMES = {
    "إفطار / Breakfast": "04:00",
    "غداء / Lunch": "10:00",
    "عشاء / Dinner": "17:00",
    "إفطار صائم / Iftar Saim": "12:00",
}


def _check_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("هذه الشاشة لمشرف التوصيل والإدارة / Delivery Supervisor access required"), frappe.PermissionError)


def _active_drivers():
    rows = frappe.get_all(
        "WAFD Driver",
        filters={"status": ["not in", ["إجازة / Leave", "غير نشط / Inactive"]]},
        fields=["name", "driver_name", "system_user", "mobile", "status"],
        order_by="driver_name asc",
        limit_page_length=300,
    )
    user_names = [row.system_user for row in rows if row.system_user]
    user_map = {
        row.name: row.full_name
        for row in frappe.get_all("User", filters={"name": ["in", user_names]}, fields=["name", "full_name"])
    } if user_names else {}
    for row in rows:
        row["display_name"] = row.driver_name or user_map.get(row.system_user) or row.name
    return rows


def _trip_rows():
    rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"status": ["!=", "ملغية / Cancelled"]},
        fields=[
            "name", "trip_date", "trip_source", "delivery_kind", "delivery_location",
            "destination_name", "destination_name_en", "destination_map_url", "hotel",
            "meal_type", "quantity", "planned_arrival", "actual_departure", "actual_arrival",
            "driver", "vehicle", "status", "delay_minutes", "creation",
        ],
        order_by="trip_date desc, planned_arrival desc, creation desc",
        limit_page_length=300,
    )
    proofs = frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": ["in", [row.name for row in rows]]},
        fields=[
            "name", "delivery_trip", "delivery_time", "delivery_photo", "receiver_name",
            "received_quantity", "status", "latitude", "longitude", "notes",
            "delivery_photo_uploaded_by", "delivery_photo_uploaded_on",
        ],
        limit_page_length=300,
    ) if rows else []
    proof_map = {row.delivery_trip: row for row in proofs}
    for row in rows:
        row["proof"] = proof_map.get(row.name)
        row["display_status"] = "تم التسليم / Delivered" if row.proof else row.status
    return rows


@frappe.whitelist()
def get_delivery_board():
    _check_access()
    hotels = frappe.get_all(
        "WAFD Hotel",
        filters={"status": "نشط / Active"},
        fields=["name", "hotel_name_ar", "hotel_name_en", "district", "map_url", "latitude", "longitude"],
        order_by="hotel_name_ar asc",
        limit_page_length=1200,
    )
    locations = frappe.get_all(
        "WAFD Delivery Location",
        filters={"status": "نشط / Active"},
        fields=["name", "location_name_ar", "location_name_en", "location_type", "address", "map_url", "latitude", "longitude"],
        order_by="location_type asc, location_name_ar asc",
        limit_page_length=500,
    )
    trips = _trip_rows()
    current = [row for row in trips if not row.proof]
    delivered = [row for row in trips if row.proof]
    return {
        "today": nowdate(),
        "meal_times": MEAL_TIMES,
        "hotels": hotels,
        "locations": locations,
        "drivers": _active_drivers(),
        "vehicles": frappe.get_all(
            "WAFD Vehicle",
            filters={"status": ["not in", ["صيانة / Maintenance", "غير نشطة / Inactive"]]},
            fields=["name", "plate_number", "vehicle_type", "status"],
            order_by="plate_number asc",
            limit_page_length=200,
        ),
        "current": current,
        "delivered": delivered,
        "summary": {"current": len(current), "delivered": len(delivered)},
    }


@frappe.whitelist()
def create_delivery_tasks(delivery_date, tasks):
    _check_access()
    if not delivery_date:
        frappe.throw(_("تاريخ التوصيل مطلوب / Delivery date is required"))
    try:
        delivery_date = getdate(delivery_date)
    except Exception:
        frappe.throw(_("تاريخ التوصيل غير صحيح / Invalid delivery date"))
    if delivery_date < getdate(nowdate()):
        frappe.throw(_("لا يمكن جدولة توصيل بتاريخ سابق / Delivery cannot be scheduled in the past"))
    rows = frappe.parse_json(tasks) if isinstance(tasks, str) else tasks
    if not isinstance(rows, list) or not rows:
        frappe.throw(_("أضف موقع توصيل واحداً على الأقل / Add at least one destination"))
    if len(rows) > 30:
        frappe.throw(_("الحد الأقصى 30 موقعاً في المرة الواحدة / Maximum 30 destinations at a time"))
    created = []
    for row in rows:
        kind = (row.get("destination_type") or "").strip()
        meal_type = (row.get("meal_type") or "").strip()
        if meal_type not in MEAL_TIMES:
            frappe.throw(_("اختر نوع الوجبة / Select a meal type"))
        delivery_time = (row.get("delivery_time") or MEAL_TIMES[meal_type]).strip()
        try:
            planned_arrival = get_datetime(f"{delivery_date.isoformat()} {delivery_time}")
        except Exception:
            frappe.throw(_("وقت التوصيل غير صحيح / Invalid delivery time"))
        values = {
            "doctype": "WAFD Delivery Trip",
            "trip_source": "خطة مشرف التوصيل / Delivery Supervisor Plan",
            "trip_date": delivery_date,
            "meal_type": meal_type,
            "planned_arrival": planned_arrival,
            "driver": (row.get("driver") or "").strip(),
            "vehicle": (row.get("vehicle") or "").strip() or None,
            "quantity": max(cint(row.get("quantity")), 0),
            "status": "مخططة / Planned",
            "notes": (row.get("notes") or "").strip(),
        }
        if kind == "hotel":
            values["hotel"] = (row.get("destination") or "").strip()
            values["delivery_kind"] = "فندق / Hotel"
        elif kind == "location":
            values["delivery_location"] = (row.get("destination") or "").strip()
        else:
            frappe.throw(_("اختر فندقاً أو موقعاً / Choose a hotel or location"))
        doc = frappe.get_doc(values).insert(ignore_permissions=True)
        created.append(doc.name)
    return {"created": created, "count": len(created)}


@frappe.whitelist()
def add_delivery_destination(destination_type, name_ar, name_en=None, map_url=None, address=None):
    _check_access()
    name_ar = (name_ar or "").strip()
    name_en = (name_en or name_ar).strip()
    if not name_ar:
        frappe.throw(_("اسم الموقع مطلوب / Location name is required"))
    if destination_type == "hotel":
        existing = frappe.db.get_value("WAFD Hotel", {"hotel_name_ar": name_ar}, "name")
        if existing:
            return {"name": existing, "type": "hotel", "created": False}
        doc = frappe.get_doc({
            "doctype": "WAFD Hotel", "hotel_name": name_ar,
            "hotel_name_ar": name_ar, "hotel_name_en": name_en,
            "address": (address or "").strip(), "map_url": (map_url or "").strip(),
            "city": "المدينة المنورة", "status": "نشط / Active",
            "verification_status": "يحتاج مراجعة / Needs Review",
        }).insert(ignore_permissions=True)
        return {"name": doc.name, "type": "hotel", "created": True}
    valid_types = {
        "mosque": "مسجد أو حرم / Mosque or Haram",
        "iftar": "موقع إفطار صائم / Iftar Site",
        "entity": "جهة أو شركة / Entity or Company",
        "other": "موقع آخر / Other Location",
    }
    if destination_type not in valid_types:
        frappe.throw(_("نوع الموقع غير صحيح / Invalid location type"))
    existing = frappe.db.get_value("WAFD Delivery Location", {"location_name_ar": name_ar}, "name")
    if existing:
        return {"name": existing, "type": "location", "created": False}
    doc = frappe.get_doc({
        "doctype": "WAFD Delivery Location", "location_name_ar": name_ar,
        "location_name_en": name_en, "location_type": valid_types[destination_type],
        "address": (address or "").strip(), "map_url": (map_url or "").strip(),
        "status": "نشط / Active",
    }).insert(ignore_permissions=True)
    return {"name": doc.name, "type": "location", "created": True}


@frappe.whitelist()
def cancel_planned_trip(trip_name):
    _check_access()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    if trip.trip_source != "خطة مشرف التوصيل / Delivery Supervisor Plan" or trip.status != "مخططة / Planned":
        frappe.throw(_("يمكن إلغاء الرحلة قبل أن يبدأها السائق فقط / A trip can only be cancelled before the driver starts"))
    trip.status = "ملغية / Cancelled"
    trip.save(ignore_permissions=True)
    return {"name": trip.name, "status": trip.status}
