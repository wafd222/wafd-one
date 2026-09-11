"""Simple delivery planning board for supervisors, management and drivers."""

from __future__ import annotations

from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_datetime, getdate, now_datetime, nowdate


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
        filters={"status": ["!=", "ملغية / Cancelled"], "archived_from_board": 0},
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
def create_recurring_delivery_tasks(start_date, end_date, destination_type, destination, meals, driver, vehicle=None):
    """Create several daily meal trips from one simple supervisor entry."""
    _check_access()
    try:
        start, end = getdate(start_date), getdate(end_date)
    except Exception:
        frappe.throw(_("تاريخ البداية أو النهاية غير صحيح / Invalid start or end date"))
    if start < getdate(nowdate()) or end < start:
        frappe.throw(_("اختر مدة صحيحة تبدأ من اليوم أو بعده / Choose a valid date range starting today or later"))
    days = (end - start).days + 1
    if days > 90:
        frappe.throw(_("الحد الأقصى للجدولة الواحدة 90 يوماً / A schedule is limited to 90 days"))
    meal_rows = frappe.parse_json(meals) if isinstance(meals, str) else meals
    if not isinstance(meal_rows, list) or not meal_rows or len(meal_rows) > 4:
        frappe.throw(_("اختر وجبة واحدة على الأقل / Select at least one meal"))
    clean_meals = []
    for row in meal_rows:
        meal_type = (row.get("meal_type") or "").strip()
        if meal_type not in MEAL_TIMES:
            frappe.throw(_("نوع الوجبة غير صحيح / Invalid meal type"))
        delivery_time = (row.get("delivery_time") or MEAL_TIMES[meal_type]).strip()
        try:
            get_datetime(f"{start} {delivery_time}")
        except Exception:
            frappe.throw(_("وقت إحدى الوجبات غير صحيح / One of the meal times is invalid"))
        clean_meals.append({"meal_type": meal_type, "delivery_time": delivery_time, "quantity": max(cint(row.get("quantity")), 0)})
    destination_type, destination, driver = (destination_type or "").strip(), (destination or "").strip(), (driver or "").strip()
    if destination_type not in {"hotel", "location"} or not destination or not driver:
        frappe.throw(_("اختر الوجهة والسائق / Choose destination and driver"))
    created, skipped = [], 0
    service_date = start
    while service_date <= end:
        for meal in clean_meals:
            planned_arrival = get_datetime(f"{service_date} {meal['delivery_time']}")
            duplicate_filters = {
                "planned_arrival": planned_arrival,
                "driver": driver,
                "meal_type": meal["meal_type"],
                "status": ["!=", "ملغية / Cancelled"],
                "hotel" if destination_type == "hotel" else "delivery_location": destination,
            }
            if frappe.db.exists("WAFD Delivery Trip", duplicate_filters):
                skipped += 1
                continue
            result = create_delivery_tasks(service_date, [{
                "destination_type": destination_type,
                "destination": destination,
                "meal_type": meal["meal_type"],
                "delivery_time": meal["delivery_time"],
                "driver": driver,
                "vehicle": (vehicle or "").strip(),
                "quantity": meal["quantity"],
            }])
            created.extend(result["created"])
        service_date = getdate(add_days(service_date, 1))
    return {"created": created, "count": len(created), "skipped_duplicates": skipped, "days": days}


@frappe.whitelist()
def add_delivery_destination(destination_type, name_ar, name_en=None, map_url=None, address=None):
    _check_access()
    name_ar = (name_ar or "").strip()
    name_en = (name_en or name_ar).strip()
    map_url = _validate_map_url(map_url)
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


def _validate_map_url(map_url):
    map_url = (map_url or "").strip()
    if not map_url:
        return ""
    parsed = urlparse(map_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        frappe.throw(_("رابط الموقع غير صحيح / Invalid map URL"))
    return map_url


@frappe.whitelist()
def search_delivery_destinations(query=None, destination_type="all"):
    """Return a compact, supervisor-only destination management list."""
    _check_access()
    query = (query or "").strip()
    like = f"%{query}%"
    rows = []
    if destination_type in {"all", "hotel"}:
        hotels = frappe.get_all(
            "WAFD Hotel",
            filters={} if not query else None,
            or_filters={"hotel_name_ar": ["like", like], "hotel_name_en": ["like", like], "address": ["like", like]} if query else None,
            fields=["name", "hotel_name_ar", "hotel_name_en", "address", "map_url", "status"],
            order_by="modified desc",
            limit_page_length=100,
        )
        for row in hotels:
            row["destination_type"] = "hotel"
            row["name_ar"] = row.pop("hotel_name_ar")
            row["name_en"] = row.pop("hotel_name_en")
            row["trip_count"] = frappe.db.count("WAFD Delivery Trip", {"hotel": row.name})
            rows.append(row)
    if destination_type in {"all", "location"}:
        locations = frappe.get_all(
            "WAFD Delivery Location",
            filters={} if not query else None,
            or_filters={"location_name_ar": ["like", like], "location_name_en": ["like", like], "address": ["like", like]} if query else None,
            fields=["name", "location_name_ar", "location_name_en", "location_type", "address", "map_url", "status"],
            order_by="modified desc",
            limit_page_length=100,
        )
        for row in locations:
            row["destination_type"] = "location"
            row["name_ar"] = row.pop("location_name_ar")
            row["name_en"] = row.pop("location_name_en")
            row["trip_count"] = frappe.db.count("WAFD Delivery Trip", {"delivery_location": row.name})
            rows.append(row)
    return rows[:150]


@frappe.whitelist()
def update_delivery_destination(destination_type, name, name_ar, name_en=None, map_url=None, address=None):
    _check_access()
    name_ar = (name_ar or "").strip()
    name_en = (name_en or name_ar).strip()
    if not name_ar:
        frappe.throw(_("اسم الفندق أو الموقع مطلوب / Destination name is required"))
    map_url = _validate_map_url(map_url)
    if destination_type == "hotel":
        doc = frappe.get_doc("WAFD Hotel", name)
        doc.hotel_name_ar, doc.hotel_name_en = name_ar, name_en
        doc.address, doc.map_url, doc.status = (address or "").strip(), map_url, "نشط / Active"
        doc.save(ignore_permissions=True)
        linked = frappe.get_all("WAFD Delivery Trip", filters={"hotel": name, "status": "مخططة / Planned"}, pluck="name")
    elif destination_type == "location":
        doc = frappe.get_doc("WAFD Delivery Location", name)
        doc.location_name_ar, doc.location_name_en = name_ar, name_en
        doc.address, doc.map_url, doc.status = (address or "").strip(), map_url, "نشط / Active"
        doc.save(ignore_permissions=True)
        linked = frappe.get_all("WAFD Delivery Trip", filters={"delivery_location": name, "status": "مخططة / Planned"}, pluck="name")
    else:
        frappe.throw(_("نوع الوجهة غير صحيح / Invalid destination type"))
    for trip_name in linked:
        frappe.db.set_value("WAFD Delivery Trip", trip_name, {"destination_name": name_ar, "destination_name_en": name_en, "destination_map_url": map_url}, update_modified=False)
    return {"name": doc.name, "updated": True}


@frappe.whitelist()
def remove_delivery_destination(destination_type, name):
    """Remove a destination from choices while retaining linked history."""
    _check_access()
    doctype = "WAFD Hotel" if destination_type == "hotel" else "WAFD Delivery Location" if destination_type == "location" else None
    if not doctype or not frappe.db.exists(doctype, name):
        frappe.throw(_("الفندق أو الموقع غير موجود / Destination not found"))
    frappe.db.set_value(doctype, name, "status", "غير نشط / Inactive")
    return {"name": name, "removed_from_choices": True}


@frappe.whitelist()
def update_planned_trip(trip_name, delivery_date, delivery_time, destination_type, destination, meal_type, driver, vehicle=None, quantity=0):
    _check_access()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    if trip.trip_source != "خطة مشرف التوصيل / Delivery Supervisor Plan" or trip.status != "مخططة / Planned":
        frappe.throw(_("يمكن تعديل الرحلة قبل أن يستلمها السائق فقط / The trip can only be edited before driver acceptance"))
    if meal_type not in MEAL_TIMES:
        frappe.throw(_("اختر نوع الوجبة / Select a meal type"))
    try:
        trip.trip_date = getdate(delivery_date)
        trip.planned_arrival = get_datetime(f"{trip.trip_date} {delivery_time}")
    except Exception:
        frappe.throw(_("التاريخ أو الوقت غير صحيح / Invalid date or time"))
    if trip.trip_date < getdate(nowdate()):
        frappe.throw(_("لا يمكن اختيار تاريخ سابق / A past date is not allowed"))
    trip.hotel = destination if destination_type == "hotel" else None
    trip.delivery_location = destination if destination_type == "location" else None
    if not (trip.hotel or trip.delivery_location):
        frappe.throw(_("اختر الفندق أو الموقع / Choose a hotel or location"))
    trip.delivery_kind = None
    trip.destination_name = trip.destination_name_en = trip.destination_map_url = None
    trip.destination_latitude = trip.destination_longitude = None
    trip.meal_type, trip.driver = meal_type, (driver or "").strip()
    trip.vehicle, trip.quantity = (vehicle or "").strip() or None, max(cint(quantity), 0)
    trip.save(ignore_permissions=True)
    return {"name": trip.name, "updated": True}


@frappe.whitelist()
def archive_delivery_trip(trip_name):
    """Cancel a mistaken plan or hide a completed test while preserving proof."""
    _check_access()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    proof_exists = bool(frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": trip.name}))
    if trip.status == "مخططة / Planned" and not proof_exists:
        trip.status = "ملغية / Cancelled"
        trip.save(ignore_permissions=True)
        return {"name": trip.name, "cancelled": True}
    if proof_exists or trip.status == "تم التسليم / Delivered":
        frappe.db.set_value("WAFD Delivery Trip", trip.name, {"archived_from_board": 1, "archived_on": now_datetime(), "archived_by": frappe.session.user})
        for share_name in frappe.get_all("WAFD Delivery Tracking Share", filters={"delivery_trip": trip.name, "enabled": 1}, pluck="name"):
            frappe.db.set_value("WAFD Delivery Tracking Share", share_name, "enabled", 0, update_modified=False)
        return {"name": trip.name, "archived": True}
    frappe.throw(_("لا يمكن حذف رحلة بدأها السائق قبل إكمالها / An active driver trip cannot be removed before completion"))


@frappe.whitelist()
def cancel_planned_trip(trip_name):
    _check_access()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    if trip.trip_source != "خطة مشرف التوصيل / Delivery Supervisor Plan" or trip.status != "مخططة / Planned":
        frappe.throw(_("يمكن إلغاء الرحلة قبل أن يبدأها السائق فقط / A trip can only be cancelled before the driver starts"))
    trip.status = "ملغية / Cancelled"
    trip.save(ignore_permissions=True)
    return {"name": trip.name, "status": trip.status}
