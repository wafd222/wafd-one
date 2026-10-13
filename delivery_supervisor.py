"""Simple delivery planning board for supervisors, management and drivers."""

from __future__ import annotations

from html import escape
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
DELIVERY_BOARD_LIMIT = 10000


def _check_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("هذه الشاشة لمشرف التوصيل والإدارة / Delivery Supervisor access required"), frappe.PermissionError)


def _management_audit(trip, action, reason, details=None):
    reason = (reason or "").strip()
    if not reason:
        frappe.throw(_("سبب التعديل أو الأرشفة مطلوب لحفظ سجل التدقيق / A reason is required for the audit trail"))
    content = f"<b>{escape(action)}</b><br>{escape(reason)}"
    if details:
        content += f"<br><small>{escape(details)}</small>"
    frappe.get_doc({
        "doctype": "Comment", "comment_type": "Info",
        "reference_doctype": "WAFD Delivery Trip", "reference_name": trip.name,
        "content": content,
    }).insert(ignore_permissions=True)


def _disable_tracking_shares(trip_name):
    for share_name in frappe.get_all(
        "WAFD Delivery Tracking Share",
        filters={"delivery_trip": trip_name, "enabled": 1},
        pluck="name",
    ):
        frappe.db.set_value("WAFD Delivery Tracking Share", share_name, "enabled", 0, update_modified=False)


def _active_drivers():
    rows = frappe.get_all(
        "WAFD Driver",
        filters={"status": ["not in", ["إجازة / Leave", "غير نشط / Inactive"]]},
        fields=["name", "driver_name", "system_user", "mobile", "status"],
        order_by="driver_name asc",
        limit_page_length=DELIVERY_BOARD_LIMIT,
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
            "driver", "vehicle", "status", "delay_minutes", "creation", "project", "contract",
            "iftar_project", "iftar_daily_operation", "iftar_link_type",
            "delivery_schedule_id", "schedule_customer", "contracting_entity",
            "safandash_count", "hot_cabinet_count",
        ],
        order_by="trip_date desc, planned_arrival desc, creation desc",
        limit_page_length=DELIVERY_BOARD_LIMIT,
    )
    proofs = frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": ["in", [row.name for row in rows]]},
        fields=[
            "name", "delivery_trip", "delivery_time", "delivery_photo", "receiver_name",
            "received_quantity", "status", "latitude", "longitude", "notes",
            "delivery_photo_uploaded_by", "delivery_photo_uploaded_on",
        ],
        limit_page_length=DELIVERY_BOARD_LIMIT,
    ) if rows else []
    proof_map = {row.delivery_trip: row for row in proofs}
    for row in rows:
        row["proof"] = proof_map.get(row.name)
        row["display_status"] = "تم التسليم / Delivered" if row.proof else row.status
    return rows


def _split_delivery_board(trips):
    """Keep the active board and delivery log mutually exclusive.

    A saved delivery proof is the authoritative completion signal. This keeps
    every missed delivery on the current board, regardless of its date, while
    moving documented deliveries to the log immediately.
    """
    current = []
    delivered = []
    for row in trips:
        (delivered if row.get("proof") else current).append(row)
    return current, delivered


def _group_delivery_board(trips):
    """Return mutually exclusive operational queues for the supervisor board."""
    buckets = {"planned": [], "in_transit": [], "attention": [], "delivered": []}
    transit_statuses = {"تم التحميل / Loaded", "في الطريق / In Transit", "وصلت / Arrived"}
    current_time = now_datetime()
    for row in trips:
        if row.get("proof"):
            buckets["delivered"].append(row)
            continue
        status = row.get("status") or ""
        if status in transit_statuses:
            buckets["in_transit"].append(row)
            continue
        planned_arrival = row.get("planned_arrival")
        overdue = bool(planned_arrival and get_datetime(planned_arrival) < current_time)
        if status == "متأخرة / Delayed" or overdue:
            buckets["attention"].append(row)
        else:
            buckets["planned"].append(row)

    def planned_key(row):
        return get_datetime(row.get("planned_arrival") or row.get("trip_date"))

    buckets["planned"].sort(key=planned_key)
    buckets["in_transit"].sort(key=planned_key)
    buckets["attention"].sort(key=planned_key)
    buckets["delivered"].sort(
        key=lambda row: get_datetime((row.get("proof") or {}).get("delivery_time") or row.get("planned_arrival") or row.get("trip_date")),
        reverse=True,
    )
    return buckets


def _is_iftar_contract(row):
    return any(
        value in ("رمضان / Ramadan", "إفطار صائم / Iftar Saem", "إفطار صائم / Iftar Saim")
        for value in (row.get("project_type"), row.get("contract_type"), row.get("first_meal"), row.get("last_meal"))
    )


def _iftar_contract_options():
    """Return active Iftar/Ramadan contracts without changing the Iftar module."""
    rows = frappe.get_all(
        "WAFD Contract",
        filters={"status": ["not in", ["منتهي / Expired", "ملغي / Cancelled"]]},
        fields=[
            "name", "contract_title", "contract_number", "project", "project_type", "contract_type",
            "first_meal", "last_meal", "start_date", "end_date", "beneficiary_count",
            "delivery_location", "hotel", "default_driver", "default_vehicle", "mission",
        ],
        order_by="start_date desc, modified desc",
        limit_page_length=500,
    )
    rows = [row for row in rows if _is_iftar_contract(row)]
    if not rows:
        return []

    hotel_names = list({row.hotel for row in rows if row.hotel})
    hotel_map = {
        row.name: row
        for row in frappe.get_all(
            "WAFD Hotel",
            filters={"name": ["in", hotel_names]},
            fields=["name", "hotel_name_ar", "hotel_name_en", "map_url"],
        )
    } if hotel_names else {}
    linked_projects = {}
    for project_row in frappe.get_all(
        "WAFD Iftar Project",
        filters={"contract": ["in", [row.name for row in rows]]},
        fields=["name", "contract", "distribution_site", "daily_meals", "start_date", "end_date"],
        order_by="modified desc",
    ):
        # The most recently updated Iftar project is the operational link when
        # historical projects happen to reference the same contract.
        linked_projects.setdefault(project_row.contract, project_row)
    for row in rows:
        hotel = hotel_map.get(row.hotel)
        iftar_project = linked_projects.get(row.name)
        row["iftar_project"] = iftar_project.name if iftar_project else None
        row["daily_meals"] = cint(iftar_project.daily_meals if iftar_project else row.beneficiary_count)
        row["destination_type"] = "hotel" if hotel else "location"
        row["destination"] = row.hotel or None
        row["destination_name"] = (
            (hotel.hotel_name_ar if hotel else None)
            or (iftar_project.distribution_site if iftar_project else None)
            or row.delivery_location
            or ""
        )
        row["destination_name_en"] = (hotel.hotel_name_en if hotel else None) or row.destination_name
        row["destination_map_url"] = (hotel.map_url if hotel else None) or ""
    return rows


@frappe.whitelist()
def get_delivery_board():
    _check_access()
    from wafd_one.delivery_tracking import list_delivery_viewers
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
    current, delivered = _split_delivery_board(trips)
    buckets = _group_delivery_board(trips)
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
        "iftar_contracts": _iftar_contract_options(),
        "delivery_viewers": list_delivery_viewers(),
        "delivery_clients": _delivery_clients(),
        "viewer_scope": "all_employees" if set(frappe.get_roles()) & {"System Manager", "WAFD Operations Manager"} else "approved_only",
        "current": current,
        "planned": buckets["planned"],
        "in_transit": buckets["in_transit"],
        "attention": buckets["attention"],
        "delivered": buckets["delivered"],
        "summary": {
            "current": len(current),
            "planned": len(buckets["planned"]),
            "in_transit": len(buckets["in_transit"]),
            "attention": len(buckets["attention"]),
            "delivered": len(delivered),
        },
    }


def _delivery_clients():
    if not frappe.db.exists("DocType", "WAFD Delivery Client"):
        return []
    return frappe.get_all(
        "WAFD Delivery Client",
        filters={"status": "نشط / Active"},
        fields=["name", "client_name", "client_type", "contact_person", "mobile"],
        order_by="client_name asc",
        limit_page_length=1000,
    )


@frappe.whitelist()
def add_delivery_client(client_name, client_type="شركة / Company", contact_person=None, mobile=None):
    """Create a reusable contracting company/mission/entity for schedules and reports."""
    _check_access()
    client_name = (client_name or "").strip()
    if not client_name:
        frappe.throw(_("اسم الشركة أو البعثة أو الجهة مطلوب / Name is required"))
    existing = frappe.db.get_value("WAFD Delivery Client", {"client_name": client_name}, "name")
    if existing:
        frappe.db.set_value("WAFD Delivery Client", existing, "status", "نشط / Active")
        return frappe.db.get_value("WAFD Delivery Client", existing, ["name", "client_name", "client_type"], as_dict=True)
    valid_types = {"شركة / Company", "بعثة / Mission", "جهة / Entity", "عميل آخر / Other Client"}
    doc = frappe.get_doc({
        "doctype": "WAFD Delivery Client",
        "client_name": client_name,
        "client_type": client_type if client_type in valid_types else "شركة / Company",
        "contact_person": (contact_person or "").strip(),
        "mobile": (mobile or "").strip(),
        "status": "نشط / Active",
    }).insert(ignore_permissions=True)
    return {"name": doc.name, "client_name": doc.client_name, "client_type": doc.client_type}


def _ensure_delivery_location(name):
    name = (name or "").strip()
    if not name:
        frappe.throw(_("موقع التسليم غير موجود في العقد / Contract delivery location is missing"))
    existing = frappe.db.get_value("WAFD Delivery Location", {"location_name_ar": name}, "name")
    if not existing:
        existing = frappe.db.get_value("WAFD Delivery Location", {"location_name_en": name}, "name")
    if existing:
        return existing
    return frappe.get_doc({
        "doctype": "WAFD Delivery Location",
        "location_name_ar": name,
        "location_name_en": name,
        "location_type": "موقع إفطار صائم / Iftar Site",
        "status": "نشط / Active",
    }).insert(ignore_permissions=True).name


def _iftar_operation(iftar_project, delivery_date):
    if not iftar_project:
        return None
    project = frappe.db.get_value(
        "WAFD Iftar Project", iftar_project,
        ["name", "start_date", "end_date", "contract", "catering_project"], as_dict=True,
    )
    if not project:
        frappe.throw(_("مشروع إفطار صائم غير موجود / Iftar project not found"))
    if (project.start_date and delivery_date < getdate(project.start_date)) or (
        project.end_date and delivery_date > getdate(project.end_date)
    ):
        frappe.throw(_("تاريخ الرحلة خارج مدة مشروع إفطار صائم / Delivery date is outside the Iftar project period"))
    operation = frappe.db.get_value(
        "WAFD Iftar Daily Operation",
        {"project": project.name, "operation_date": delivery_date, "docstatus": ["<", 2]},
        "name",
    )
    if not operation:
        from wafd_one.wafd_one.iftar_pro import generate_daily_operations
        generate_daily_operations(project.name, ignore_permissions=True)
        operation = frappe.db.get_value(
            "WAFD Iftar Daily Operation",
            {"project": project.name, "operation_date": delivery_date, "docstatus": ["<", 2]},
            "name",
        )
    return frappe._dict(project=project, operation=operation)


@frappe.whitelist()
def create_iftar_delivery_task(delivery_date, driver, delivery_time="12:00", vehicle=None,
                               contract=None, destination_type=None, destination=None,
                               quantity=0, notes=None, contracting_entity=None,
                               safandash_count=0, hot_cabinet_count=0):
    """Create either a contract-linked or explicitly standalone Iftar delivery."""
    _check_access()
    try:
        delivery_date = getdate(delivery_date)
        planned_arrival = get_datetime(f"{delivery_date.isoformat()} {(delivery_time or '12:00').strip()}")
    except Exception:
        frappe.throw(_("تاريخ أو وقت التوصيل غير صحيح / Invalid delivery date or time"))
    if delivery_date < getdate(nowdate()):
        frappe.throw(_("لا يمكن جدولة توصيل بتاريخ سابق / Delivery cannot be scheduled in the past"))
    driver = (driver or "").strip()
    if not driver:
        frappe.throw(_("اختر السائق / Choose a driver"))

    values = {
        "doctype": "WAFD Delivery Trip",
        "trip_source": "خطة مشرف التوصيل / Delivery Supervisor Plan",
        "trip_date": delivery_date,
        "meal_type": "إفطار صائم / Iftar Saim",
        "planned_arrival": planned_arrival,
        "driver": driver,
        "vehicle": (vehicle or "").strip() or None,
        "status": "مخططة / Planned",
        "notes": (notes or "").strip(),
        "contracting_entity": (contracting_entity or "").strip() or None,
        "safandash_count": max(cint(safandash_count), 0),
        "hot_cabinet_count": max(cint(hot_cabinet_count), 0),
    }

    if contract:
        contract_row = frappe.db.get_value(
            "WAFD Contract", contract,
            ["name", "status", "project", "project_type", "contract_type", "first_meal", "last_meal",
             "start_date", "end_date", "beneficiary_count", "delivery_location", "hotel",
             "mission", "contract_title"], as_dict=True,
        )
        if not contract_row or contract_row.status in ("منتهي / Expired", "ملغي / Cancelled") or not _is_iftar_contract(contract_row):
            frappe.throw(_("اختر عقد إفطار صائم صالحاً / Select a valid Iftar contract"))
        if (contract_row.start_date and delivery_date < getdate(contract_row.start_date)) or (
            contract_row.end_date and delivery_date > getdate(contract_row.end_date)
        ):
            frappe.throw(_("تاريخ الرحلة خارج مدة العقد / Delivery date is outside the contract period"))
        iftar_project = frappe.db.get_value("WAFD Iftar Project", {"contract": contract_row.name}, "name", order_by="modified desc")
        operation = _iftar_operation(iftar_project, delivery_date) if iftar_project else None
        values.update({
            "contract": contract_row.name,
            "project": contract_row.project or (operation.project.catering_project if operation else None),
            "iftar_project": iftar_project,
            "iftar_daily_operation": operation.operation if operation else None,
            "iftar_link_type": "مرتبط بعقد / Contract Linked",
            "quantity": cint(quantity) or cint(
                frappe.db.get_value("WAFD Iftar Project", iftar_project, "daily_meals") if iftar_project else 0
            ) or cint(contract_row.beneficiary_count),
            "contracting_entity": values.get("contracting_entity") or contract_row.mission or contract_row.contract_title,
        })
        if contract_row.hotel:
            values["hotel"] = contract_row.hotel
            values["delivery_kind"] = "فندق / Hotel"
        else:
            site = (operation and frappe.db.get_value("WAFD Iftar Project", iftar_project, "distribution_site")) or contract_row.delivery_location
            values["delivery_location"] = _ensure_delivery_location(site)
            values["delivery_kind"] = "موقع إفطار صائم / Iftar Site"
    else:
        destination_type = (destination_type or "").strip()
        destination = (destination or "").strip()
        if destination_type == "hotel" and destination:
            values["hotel"] = destination
            values["delivery_kind"] = "فندق / Hotel"
        elif destination_type == "location" and destination:
            values["delivery_location"] = destination
            values["delivery_kind"] = "موقع إفطار صائم / Iftar Site"
        else:
            frappe.throw(_("اختر موقع التوصيل / Choose a delivery destination"))
        values["quantity"] = max(cint(quantity), 0)
        values["iftar_link_type"] = "بدون عقد / No Contract"

    doc = frappe.get_doc(values).insert(ignore_permissions=True)
    return {"name": doc.name, "count": 1, "iftar_link_type": doc.iftar_link_type}


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
            "delivery_schedule_id": (row.get("delivery_schedule_id") or "").strip() or None,
            "schedule_customer": (row.get("schedule_customer") or "").strip() or None,
            "contracting_entity": (row.get("contracting_entity") or row.get("schedule_customer") or "").strip() or None,
            "safandash_count": max(cint(row.get("safandash_count")), 0),
            "hot_cabinet_count": max(cint(row.get("hot_cabinet_count")), 0),
        }
        if values.get("meal_type") == "إفطار صائم / Iftar Saim":
            values["iftar_link_type"] = "بدون عقد / No Contract"
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
def create_recurring_delivery_tasks(start_date, end_date, destination_type=None, destination=None,
                                    meals=None, driver=None, vehicle=None, destinations=None,
                                    customer_name=None, viewers=None):
    """Create one tracked schedule across multiple destinations, days and meals."""
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
    driver = (driver or "").strip()
    destination_rows = frappe.parse_json(destinations) if isinstance(destinations, str) else destinations
    if not destination_rows:
        destination_rows = [{"destination_type": destination_type, "destination": destination}]
    if not isinstance(destination_rows, list) or len(destination_rows) > 30:
        frappe.throw(_("اختر من وجهة واحدة إلى 30 وجهة / Choose between one and 30 destinations"))
    cleaned_destinations = []
    seen_destinations = set()
    for row in destination_rows:
        kind = (row.get("destination_type") or "").strip()
        name = (row.get("destination") or "").strip()
        if kind not in {"hotel", "location"} or not name:
            frappe.throw(_("اختر الفنادق أو الجهات / Choose hotels or destinations"))
        key = (kind, name)
        if key not in seen_destinations:
            cleaned_destinations.append({
                "destination_type": kind,
                "destination": name,
                "safandash_count": max(cint(row.get("safandash_count")), 0),
                "hot_cabinet_count": max(cint(row.get("hot_cabinet_count")), 0),
            })
            seen_destinations.add(key)
    if not cleaned_destinations or not driver:
        frappe.throw(_("اختر وجهة واحدة على الأقل والسائق / Choose at least one destination and the driver"))
    viewer_users = frappe.parse_json(viewers) if isinstance(viewers, str) else viewers
    if not isinstance(viewer_users, list) or not viewer_users:
        frappe.throw(_("اختر مستفيداً أو متابعاً واحداً على الأقل / Choose at least one beneficiary or follower"))
    customer_name = (customer_name or "").strip()
    if not customer_name:
        frappe.throw(_("أدخل اسم العميل أو الشركة / Enter the customer or company name"))
    if not frappe.db.exists("WAFD Delivery Client", {"client_name": customer_name}):
        add_delivery_client(customer_name)
    schedule_id = f"WAFD-SCH-{start.strftime('%Y%m%d')}-{frappe.generate_hash(length=10)}"
    created, skipped = [], 0
    service_date = start
    while service_date <= end:
        for destination_row in cleaned_destinations:
            for meal in clean_meals:
                planned_arrival = get_datetime(f"{service_date} {meal['delivery_time']}")
                duplicate_filters = {
                    "planned_arrival": planned_arrival,
                    "driver": driver,
                    "meal_type": meal["meal_type"],
                    "status": ["!=", "ملغية / Cancelled"],
                    "hotel" if destination_row["destination_type"] == "hotel" else "delivery_location": destination_row["destination"],
                }
                if frappe.db.exists("WAFD Delivery Trip", duplicate_filters):
                    skipped += 1
                    continue
                result = create_delivery_tasks(service_date, [{
                    **destination_row,
                    "meal_type": meal["meal_type"],
                    "delivery_time": meal["delivery_time"],
                    "driver": driver,
                    "vehicle": (vehicle or "").strip(),
                    "quantity": meal["quantity"],
                    "delivery_schedule_id": schedule_id,
                    "schedule_customer": customer_name,
                    "contracting_entity": customer_name,
                    "safandash_count": destination_row["safandash_count"],
                    "hot_cabinet_count": destination_row["hot_cabinet_count"],
                }])
                created.extend(result["created"])
        service_date = getdate(add_days(service_date, 1))
    if not created:
        frappe.throw(_("لم تُنشأ رحلات جديدة لأن جميع الرحلات مكررة / No new trips were created because all entries already exist"))
    from wafd_one.delivery_tracking import assign_schedule_viewers
    assignments = assign_schedule_viewers(created, viewer_users)
    return {"created": created, "count": len(created), "skipped_duplicates": skipped, "days": days,
            "destinations": len(cleaned_destinations), "delivery_schedule_id": schedule_id,
            "viewer_count": len(set(viewer_users)), "assignments": assignments}


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
def update_planned_trip(trip_name, delivery_date, delivery_time, destination_type, destination, meal_type, driver,
                        vehicle=None, quantity=0, contracting_entity=None, safandash_count=0, hot_cabinet_count=0,
                        change_reason=None):
    _check_access()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    _management_audit(trip, "تعديل رحلة التوصيل / Delivery correction", change_reason)
    if meal_type not in MEAL_TIMES:
        frappe.throw(_("اختر نوع الوجبة / Select a meal type"))
    try:
        trip.trip_date = getdate(delivery_date)
        trip.planned_arrival = get_datetime(f"{trip.trip_date} {delivery_time}")
    except Exception:
        frappe.throw(_("التاريخ أو الوقت غير صحيح / Invalid date or time"))
    trip.hotel = destination if destination_type == "hotel" else None
    trip.delivery_location = destination if destination_type == "location" else None
    if not (trip.hotel or trip.delivery_location):
        frappe.throw(_("اختر الفندق أو الموقع / Choose a hotel or location"))
    trip.delivery_kind = None
    trip.destination_name = trip.destination_name_en = trip.destination_map_url = None
    trip.destination_latitude = trip.destination_longitude = None
    trip.meal_type, trip.driver = meal_type, (driver or "").strip()
    trip.vehicle, trip.quantity = (vehicle or "").strip() or None, max(cint(quantity), 0)
    trip.contracting_entity = (contracting_entity or "").strip() or None
    trip.safandash_count = max(cint(safandash_count), 0)
    trip.hot_cabinet_count = max(cint(hot_cabinet_count), 0)
    trip.save(ignore_permissions=True)
    return {"name": trip.name, "updated": True, "proof_preserved": bool(frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": trip.name}))}


@frappe.whitelist()
def archive_delivery_trip(trip_name, reason=None):
    """Remove a trip from operations while preserving evidence and its audit trail."""
    _check_access()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    _management_audit(trip, "أرشفة رحلة التوصيل / Delivery archived", reason)
    proof_exists = bool(frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": trip.name}))
    if not proof_exists:
        trip.status = "ملغية / Cancelled"
        trip.save(ignore_permissions=True)
        _disable_tracking_shares(trip.name)
        return {"name": trip.name, "cancelled": True}
    frappe.db.set_value("WAFD Delivery Trip", trip.name, {"archived_from_board": 1, "archived_on": now_datetime(), "archived_by": frappe.session.user})
    _disable_tracking_shares(trip.name)
    return {"name": trip.name, "archived": True, "proof_preserved": proof_exists}


@frappe.whitelist()
def get_delivery_schedule(schedule_id):
    _check_access()
    schedule_id = (schedule_id or "").strip()
    rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"delivery_schedule_id": schedule_id, "status": ["!=", "ملغية / Cancelled"], "archived_from_board": 0},
        fields=["name", "trip_date", "planned_arrival", "driver", "vehicle", "schedule_customer", "contracting_entity", "status"],
        order_by="planned_arrival asc, creation asc",
        limit_page_length=12000,
    )
    if not rows:
        frappe.throw(_("جدول التوصيل غير موجود / Delivery schedule not found"))
    return {
        "delivery_schedule_id": schedule_id, "count": len(rows),
        "start_date": rows[0].trip_date, "end_date": rows[-1].trip_date,
        "driver": rows[0].driver, "vehicle": rows[0].vehicle,
        "contracting_entity": rows[0].contracting_entity or rows[0].schedule_customer,
    }


@frappe.whitelist()
def update_delivery_schedule(schedule_id, driver, vehicle=None, contracting_entity=None,
                             new_start_date=None, change_reason=None):
    """Correct a whole project while retaining completed proofs and relative timing."""
    _check_access()
    schedule_id = (schedule_id or "").strip()
    names = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"delivery_schedule_id": schedule_id, "status": ["!=", "ملغية / Cancelled"], "archived_from_board": 0},
        pluck="name", order_by="planned_arrival asc, creation asc", limit_page_length=12000,
    )
    if not names:
        frappe.throw(_("جدول التوصيل غير موجود / Delivery schedule not found"))
    first = frappe.get_doc("WAFD Delivery Trip", names[0])
    reason = (change_reason or "").strip()
    if not reason:
        frappe.throw(_("سبب التعديل مطلوب / Change reason is required"))
    shift_days = 0
    if new_start_date:
        shift_days = (getdate(new_start_date) - getdate(first.trip_date)).days
    updated = 0
    for name in names:
        trip = frappe.get_doc("WAFD Delivery Trip", name)
        _management_audit(trip, "تعديل جدول التوصيل / Delivery schedule correction", reason, schedule_id)
        trip.driver = (driver or "").strip()
        trip.vehicle = (vehicle or "").strip() or None
        entity = (contracting_entity or "").strip() or None
        trip.contracting_entity = entity
        trip.schedule_customer = entity
        if shift_days:
            trip.trip_date = getdate(add_days(trip.trip_date, shift_days))
            if trip.planned_arrival:
                trip.planned_arrival = get_datetime(add_days(trip.planned_arrival, shift_days))
            if trip.planned_departure:
                trip.planned_departure = get_datetime(add_days(trip.planned_departure, shift_days))
        trip.save(ignore_permissions=True)
        updated += 1
    return {"delivery_schedule_id": schedule_id, "updated": updated, "date_shift_days": shift_days}


@frappe.whitelist()
def archive_delivery_schedule(schedule_id, reason=None):
    """Archive/cancel every row in a multi-day project without deleting evidence."""
    _check_access()
    schedule_id = (schedule_id or "").strip()
    names = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"delivery_schedule_id": schedule_id, "status": ["!=", "ملغية / Cancelled"], "archived_from_board": 0},
        pluck="name", limit_page_length=12000,
    )
    if not names:
        frappe.throw(_("جدول التوصيل غير موجود / Delivery schedule not found"))
    cancelled = archived = 0
    for name in names:
        result = archive_delivery_trip(name, reason=reason)
        cancelled += int(bool(result.get("cancelled")))
        archived += int(bool(result.get("archived")))
    return {"delivery_schedule_id": schedule_id, "cancelled": cancelled, "archived": archived, "total": len(names)}


@frappe.whitelist()
def cancel_planned_trip(trip_name):
    _check_access()
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    if trip.trip_source != "خطة مشرف التوصيل / Delivery Supervisor Plan" or trip.status != "مخططة / Planned":
        frappe.throw(_("يمكن إلغاء الرحلة قبل أن يبدأها السائق فقط / A trip can only be cancelled before the driver starts"))
    trip.status = "ملغية / Cancelled"
    trip.save(ignore_permissions=True)
    return {"name": trip.name, "status": trip.status}
