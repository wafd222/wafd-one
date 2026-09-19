from __future__ import annotations

import math
import json

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, getdate, now_datetime

from wafd_one.wafd_one.iftar_pro import generate_daily_operations


GLOBAL_MANAGEMENT_ROLES = {"System Manager", "WAFD Operations Manager"}
PROJECT_MANAGER_ROLE = "WAFD Project Manager"
KITCHEN_ROLE = "WAFD Iftar Kitchen Supervisor"
DELIVERY_ROLE = "WAFD Delivery Supervisor"
SITE_MANAGER_ROLE = "WAFD Iftar Site Manager"
SUPERVISOR_ROLE = "WAFD Iftar Supervisor"
EXTERNAL_VIEWER_ROLE = "WAFD Delivery Viewer"

TEAM_ROLE_BY_FIELD = {
    "project_manager_user": PROJECT_MANAGER_ROLE,
    "kitchen_supervisor_user": KITCHEN_ROLE,
    "delivery_supervisor_user": DELIVERY_ROLE,
    "site_manager_user": SITE_MANAGER_ROLE,
    "external_viewer_user": EXTERNAL_VIEWER_ROLE,
}

STAGE_LABELS = {
    "production": "الإنتاج",
    "packaging": "التغليف",
    "loading": "التحميل",
    "delivery_plan": "خطة التوصيل",
    "in_transit": "في الطريق",
    "delivered": "التسليم",
}


# ---------------------------------------------------------------------------
# Security / visibility
# ---------------------------------------------------------------------------

def _roles(user=None):
    return set(frappe.get_roles(user or frappe.session.user))


def _is_global_manager(roles=None):
    return bool((roles or _roles()) & GLOBAL_MANAGEMENT_ROLES)


def _active_user(user):
    user = (user or "").strip()
    if not user:
        return ""
    if not frappe.db.exists("User", {"name": user, "enabled": 1, "user_type": "System User"}):
        frappe.throw(_("اختر حساب مستخدم نشط / Select an active system user"))
    return user


def _ensure_team_role(user, required_role):
    """Grant only the Iftar assignment role needed by the selected user.

    Team assignment is a management-only action.  We deliberately do not
    remove or replace any existing roles, and global management accounts are
    left untouched because they already have full Iftar access.
    """
    roles = _roles(user)
    if required_role in roles or (roles & GLOBAL_MANAGEMENT_ROLES):
        return
    if not frappe.db.exists("Role", required_role):
        frappe.throw(
            _("الدور المطلوب غير موجود في النظام: {0} / Required role does not exist").format(required_role)
        )

    user_doc = frappe.get_doc("User", user)
    existing = {row.role for row in (user_doc.roles or []) if row.role}
    if required_role not in existing:
        user_doc.append("roles", {"role": required_role})
        user_doc.flags.ignore_permissions = True
        user_doc.save(ignore_permissions=True)
    frappe.clear_cache(user=user)


def _validate_team_user(fieldname, user):
    user = _active_user(user)
    if not user:
        return ""
    required_role = TEAM_ROLE_BY_FIELD[fieldname]
    _ensure_team_role(user, required_role)
    return user


def _project_access(project, roles=None):
    roles = roles or _roles()
    user = frappe.session.user
    if _is_global_manager(roles):
        return {"management"}

    # RC319: the explicit project assignment is the source of truth.
    # Do not hide an assigned task because a User-role cache is stale or the
    # role was added moments earlier by management.  Security is still strict:
    # only the exact User stored on the project receives that duty.
    duties = set()
    if (project.get("project_manager_user") or "").strip() == user:
        duties.add("project_manager")
    if (project.get("kitchen_supervisor_user") or "").strip() == user:
        duties.add("kitchen")
    if (project.get("delivery_supervisor_user") or "").strip() == user:
        duties.add("delivery")
    if (project.get("site_manager_user") or "").strip() == user:
        duties.add("site")
    if frappe.db.exists("WAFD Iftar Supervisor Plan", {"project": project.name, "supervisor_user": user}):
        duties.add("supervisor")
    if (project.get("external_viewer_user") or "").strip() == user:
        duties.add("viewer")
    return duties


def _require_project_duty(project, duty):
    duties = _project_access(project)
    if "management" in duties:
        return
    if duty not in duties:
        frappe.throw(_("هذه المهمة غير مسندة لهذا الحساب / This task is not assigned to this account"), frappe.PermissionError)


def _visible_projects():
    roles = _roles()
    rows = frappe.get_all(
        "WAFD Iftar Project",
        filters={
            "docstatus": ["<", 2],
            "status": ["not in", ["ملغي / Cancelled"]],
        },
        fields=[
            "name", "project_title", "distribution_site", "contracting_entity", "contract",
            "catering_project", "start_date", "end_date", "daily_meals", "number_of_days",
            "total_meals", "meal_template", "include_zamzam", "max_carton_capacity", "status",
            "project_manager_user", "kitchen_supervisor_user", "delivery_supervisor_user",
            "site_manager_user", "external_viewer_user", "distribution_deadline", "modified",
        ],
        order_by="start_date desc, modified desc",
        limit_page_length=250,
    )
    visible = []
    for row in rows:
        duties = _project_access(row, roles)
        if duties:
            row["portal_duties"] = sorted(duties)
            visible.append(row)
    return visible


def _mode_from_projects(projects):
    roles = _roles()
    if _is_global_manager(roles):
        return "management"
    duties = set()
    for project in projects:
        duties.update(project.get("portal_duties") or [])
    # Project-manager monitoring intentionally wins over field execution when a
    # user has both roles, because that account is expected to supervise rather
    # than accidentally approve a field stage from the monitoring view.
    if "project_manager" in duties:
        return "project_manager"
    if "kitchen" in duties:
        return "kitchen"
    if "delivery" in duties:
        return "delivery"
    if "site" in duties:
        return "site"
    if "supervisor" in duties:
        return "supervisor"
    if "viewer" in duties:
        return "viewer"
    return "none"


# ---------------------------------------------------------------------------
# Data shaping
# ---------------------------------------------------------------------------

def _cartons(meals, capacity):
    meals = max(cint(meals), 0)
    capacity = max(cint(capacity), 1)
    return int(math.ceil(meals / capacity)) if meals else 0


def _component_rows(project_name):
    rows = frappe.get_all(
        "WAFD Iftar Component",
        filters={"parent": project_name, "parenttype": "WAFD Iftar Project"},
        fields=["ingredient", "component_group", "is_mandatory", "quantity_per_meal", "uom", "notes"],
        order_by="idx asc",
        limit_page_length=200,
    )
    ingredient_ids = [row.ingredient for row in rows if row.ingredient]
    names = {}
    if ingredient_ids:
        names = {
            row.name: (row.ingredient_name or row.name)
            for row in frappe.get_all(
                "WAFD Ingredient",
                filters={"name": ["in", ingredient_ids]},
                fields=["name", "ingredient_name"],
                limit_page_length=500,
            )
        }
    components = []
    additions = []
    for row in rows:
        item = {
            "name": names.get(row.ingredient, row.ingredient or ""),
            "quantity_per_meal": row.quantity_per_meal,
            "uom": row.uom or "",
            "notes": row.notes or "",
            "mandatory": cint(row.is_mandatory),
        }
        if row.component_group == "إضافة / Add-on" and not cint(row.is_mandatory):
            additions.append(item)
        else:
            components.append(item)
    return components, additions


def _operations(project):
    # Keep the restored RC144 engine as the source of daily rows. This helper is
    # idempotent and creates only missing Iftar daily-operation records.
    generate_daily_operations(project.name, ignore_permissions=True)
    return frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": project.name, "docstatus": ["<", 2]},
        fields=[
            "name", "operation_date", "status", "planned_meals", "produced_meals",
            "packaged_meals", "loaded_meals", "delivered_meals", "received_meals",
            "delivery_plan_approved", "delivery_plan_approved_by", "delivery_plan_approved_at",
            "delivery_scheduled_meals", "delivery_verified_meals", "delivery_proof_count",
            "delivery_last_arrival", "production_approved_by", "production_approved_at",
            "packaging_approved_by", "packaging_approved_at", "loading_approved_by",
            "loading_approved_at", "workflow_notes", "notes", "site_receipt_approved",
            "site_receipt_time", "site_received_meals", "site_received_by",
            "authority_inspection_approved", "authority_inspection_time", "authority_supervisor_name",
            "site_report_approved", "site_report_approved_at", "daily_report_sent", "authority_report_sent_at",
        ],
        order_by="operation_date asc, creation asc",
        limit_page_length=400,
    )


def _delivery_rows(operation_name):
    trips = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"iftar_daily_operation": operation_name, "status": ["!=", "ملغية / Cancelled"]},
        fields=[
            "name", "vehicle", "driver", "quantity", "status", "planned_arrival",
            "actual_departure", "actual_arrival", "destination_name", "notes",
        ],
        order_by="creation asc",
        limit_page_length=100,
    )
    if not trips:
        return []
    vehicle_ids = [x.vehicle for x in trips if x.vehicle]
    driver_ids = [x.driver for x in trips if x.driver]
    vehicle_map = {
        x.name: (x.plate_number or x.name)
        for x in frappe.get_all("WAFD Vehicle", filters={"name": ["in", vehicle_ids]}, fields=["name", "plate_number"], limit_page_length=200)
    } if vehicle_ids else {}
    driver_map = {
        x.name: (x.driver_name or x.name)
        for x in frappe.get_all("WAFD Driver", filters={"name": ["in", driver_ids]}, fields=["name", "driver_name"], limit_page_length=200)
    } if driver_ids else {}
    proof_map = {
        x.delivery_trip: x
        for x in frappe.get_all(
            "WAFD Delivery Proof",
            filters={"delivery_trip": ["in", [row.name for row in trips]]},
            fields=["delivery_trip", "received_quantity", "receiver_name", "delivery_time", "delivery_photo", "notes"],
            limit_page_length=200,
        )
    }
    for row in trips:
        row["vehicle_label"] = vehicle_map.get(row.vehicle, row.vehicle or "")
        row["driver_label"] = driver_map.get(row.driver, row.driver or "")
        proof = proof_map.get(row.name)
        row["proof"] = proof or None
    return trips


def _stage_state(operation, trips=None):
    planned = cint(operation.planned_meals)
    produced = cint(operation.produced_meals)
    packaged = cint(operation.packaged_meals)
    loaded = cint(operation.loaded_meals)
    delivered = cint(operation.delivered_meals)
    trips = trips if trips is not None else _delivery_rows(operation.name)

    production_done = bool(planned and produced >= planned)
    packaging_done = bool(production_done and packaged >= planned)
    loading_done = bool(packaging_done and loaded >= planned)
    dispatch_done = bool(cint(operation.delivery_plan_approved))
    in_transit = any(
        row.status in ("في الطريق / In Transit", "وصلت / Arrived", "تم التسليم / Delivered", "متأخرة / Delayed")
        or row.actual_departure
        for row in trips
    )
    delivery_done = bool(loaded and delivered >= loaded)
    if trips and all((row.get("proof") and cint(row.proof.received_quantity) >= 0) or row.status == "تم التسليم / Delivered" for row in trips):
        delivery_done = delivery_done or all(row.status == "تم التسليم / Delivered" or row.get("proof") for row in trips)

    stages = [
        {"key": "production", "label": STAGE_LABELS["production"], "done": production_done, "time": operation.production_approved_at},
        {"key": "packaging", "label": STAGE_LABELS["packaging"], "done": packaging_done, "time": operation.packaging_approved_at},
        {"key": "loading", "label": STAGE_LABELS["loading"], "done": loading_done, "time": operation.loading_approved_at},
        {"key": "delivery_plan", "label": STAGE_LABELS["delivery_plan"], "done": dispatch_done, "time": operation.delivery_plan_approved_at},
        {"key": "in_transit", "label": STAGE_LABELS["in_transit"], "done": bool(in_transit), "time": next((row.actual_departure for row in trips if row.actual_departure), None)},
        {"key": "delivered", "label": STAGE_LABELS["delivered"], "done": delivery_done, "time": operation.delivery_last_arrival},
    ]
    current = next((stage["key"] for stage in stages if not stage["done"]), "complete")
    done_count = sum(1 for stage in stages if stage["done"])
    return {
        "stages": stages,
        "current_stage": current,
        "progress_percent": round(done_count / len(stages) * 100) if stages else 0,
        "delivery_done": delivery_done,
    }


def _operation_payload(project, operation, index, total, include_trips=True):
    capacity = max(cint(project.max_carton_capacity), 1)
    trips = _delivery_rows(operation.name) if include_trips else []
    stage = _stage_state(operation, trips)
    notes = (operation.workflow_notes or "").strip()
    if not notes and (operation.notes or "").strip():
        notes = (operation.notes or "").strip()
    return {
        **dict(operation),
        "day_index": index,
        "day_total": total,
        "cartons": _cartons(operation.planned_meals, capacity),
        "trips": trips,
        "display_notes": notes,
        **stage,
    }


def _project_payload(project, include_all_operations=False, include_trips=True):
    components, additions = _component_rows(project.name)
    operations = _operations(project)
    total = len(operations)
    shaped = [
        _operation_payload(project, operation, idx + 1, total, include_trips=include_trips)
        for idx, operation in enumerate(operations)
    ]
    current = next((row for row in shaped if not row["delivery_done"]), shaped[-1] if shaped else None)
    return {
        **dict(project),
        "cartons_per_day": _cartons(project.daily_meals, project.max_carton_capacity or 25),
        "components": components,
        "additions": additions,
        "current_operation": current,
        "operations": shaped if include_all_operations else [],
    }


def _kitchen_payload(project):
    payload = _project_payload(project, include_all_operations=True, include_trips=False)
    task = next(
        (
            op for op in payload["operations"]
            if cint(op.get("loaded_meals")) < cint(op.get("planned_meals"))
        ),
        None,
    )
    payload["task"] = task
    payload.pop("operations", None)
    return payload


def _delivery_payload(project):
    payload = _project_payload(project, include_all_operations=True, include_trips=True)
    pending = [
        op for op in payload["operations"]
        if cint(op.get("loaded_meals")) > 0 and not cint(op.get("delivery_plan_approved"))
    ]
    tracking = [
        op for op in payload["operations"]
        if cint(op.get("delivery_plan_approved")) and not op.get("delivery_done")
    ]
    payload["pending_tasks"] = pending
    payload["tracking"] = tracking
    payload.pop("operations", None)
    return payload


def _team_options():
    result = {}
    for fieldname, role in TEAM_ROLE_BY_FIELD.items():
        users = frappe.get_all(
            "Has Role",
            filters={"role": role, "parenttype": "User"},
            pluck="parent",
            limit_page_length=1000,
        )
        users = sorted(set(users))
        rows = frappe.get_all(
            "User",
            filters={"name": ["in", users], "enabled": 1, "user_type": "System User"},
            fields=["name", "full_name"],
            order_by="full_name asc",
            limit_page_length=1000,
        ) if users else []
        result[fieldname] = [
            {"value": row.name, "label": f"{row.full_name or row.name} — {row.name}"}
            for row in rows
        ]
    return result


def _delivery_options():
    drivers = frappe.get_all(
        "WAFD Driver",
        filters={"status": ["not in", ["إجازة / Leave", "غير نشط / Inactive"]]},
        fields=["name", "driver_name", "mobile", "status"],
        order_by="driver_name asc",
        limit_page_length=300,
    )
    vehicles = frappe.get_all(
        "WAFD Vehicle",
        filters={"status": ["not in", ["صيانة / Maintenance", "غير نشطة / Inactive"]]},
        fields=["name", "plate_number", "vehicle_type", "capacity_meals", "status"],
        order_by="plate_number asc",
        limit_page_length=300,
    )
    return {"drivers": drivers, "vehicles": vehicles}


@frappe.whitelist()
def get_portal_data():
    if frappe.session.user in ("Guest", ""):
        frappe.throw(_("يجب تسجيل الدخول / Login required"), frappe.PermissionError)

    projects = _visible_projects()
    mode = _mode_from_projects(projects)
    if mode == "none":
        allowed = GLOBAL_MANAGEMENT_ROLES | {PROJECT_MANAGER_ROLE, KITCHEN_ROLE, DELIVERY_ROLE, SITE_MANAGER_ROLE, SUPERVISOR_ROLE, EXTERNAL_VIEWER_ROLE}
        if not (_roles() & allowed):
            frappe.throw(_("غير مصرح بمتابعة إفطار الصائم / Not permitted"), frappe.PermissionError)

    if mode == "kitchen":
        project_rows = [_kitchen_payload(project) for project in projects if "kitchen" in (project.get("portal_duties") or [])]
    elif mode == "delivery":
        project_rows = [_delivery_payload(project) for project in projects if "delivery" in (project.get("portal_duties") or [])]
    else:
        project_rows = [_project_payload(project, include_all_operations=False, include_trips=True) for project in projects]

    response = {
        "mode": mode,
        "user": frappe.session.user,
        "full_name": frappe.utils.get_fullname(frappe.session.user) or frappe.session.user,
        "projects": project_rows,
        "can_manage_team": mode == "management",
    }
    if mode == "management":
        response["team_options"] = _team_options()
    if mode == "delivery":
        response.update(_delivery_options())
    return response


# ---------------------------------------------------------------------------
# Management setup
# ---------------------------------------------------------------------------

@frappe.whitelist()
def save_project_team(project_name, project_manager_user=None, kitchen_supervisor_user=None,
                      delivery_supervisor_user=None, site_manager_user=None, external_viewer_user=None):
    if not _is_global_manager():
        frappe.throw(_("الإدارة فقط يمكنها إسناد فريق المشروع / Management only"), frappe.PermissionError)
    if not frappe.db.exists("WAFD Iftar Project", project_name):
        frappe.throw(_("مشروع إفطار الصائم غير موجود / Iftar project not found"))

    values = {}
    for fieldname, raw in {
        "project_manager_user": project_manager_user,
        "kitchen_supervisor_user": kitchen_supervisor_user,
        "delivery_supervisor_user": delivery_supervisor_user,
        "site_manager_user": site_manager_user,
        "external_viewer_user": external_viewer_user,
    }.items():
        values[fieldname] = _validate_team_user(fieldname, raw)

    frappe.db.set_value("WAFD Iftar Project", project_name, values, update_modified=True)
    for user in {value for value in values.values() if value}:
        frappe.clear_cache(user=user)
        frappe.publish_realtime("wafd_iftar_stage_assignment", {"project": project_name}, user=user)
    return {"project": project_name, **values}


# ---------------------------------------------------------------------------
# Kitchen stages
# ---------------------------------------------------------------------------

def _append_workflow_note(operation_name, stage_label, note):
    note = " ".join((note or "").split()).strip()
    if not note:
        return frappe.db.get_value("WAFD Iftar Daily Operation", operation_name, "workflow_notes") or ""
    current = frappe.db.get_value("WAFD Iftar Daily Operation", operation_name, "workflow_notes") or ""
    actor = frappe.utils.get_fullname(frappe.session.user) or frappe.session.user
    stamp = now_datetime().strftime("%Y-%m-%d %H:%M")
    line = f"[{stamp}] {stage_label} — {actor}: {note}"
    merged = (current.rstrip() + "\n" + line).strip() if current.strip() else line
    frappe.db.set_value("WAFD Iftar Daily Operation", operation_name, "workflow_notes", merged, update_modified=False)
    return merged


@frappe.whitelist()
def approve_kitchen_stage(operation_name, stage, note=None):
    if stage not in ("production", "packaging", "loading"):
        frappe.throw(_("مرحلة مطبخ غير صحيحة / Invalid kitchen stage"))
    operation = frappe.get_doc("WAFD Iftar Daily Operation", operation_name)
    project = frappe.get_doc("WAFD Iftar Project", operation.project)
    _require_project_duty(project, "kitchen")

    planned = cint(operation.planned_meals)
    if planned <= 0:
        frappe.throw(_("عدد الوجبات اليومية غير صحيح / Invalid daily meal quantity"))
    now = now_datetime()
    updates = {}

    if stage == "production":
        if cint(operation.produced_meals) < planned:
            updates.update({
                "produced_meals": planned,
                "kitchen_started": 1,
                "kitchen_started_by": operation.kitchen_started_by or frappe.session.user,
                "kitchen_started_at": operation.kitchen_started_at or now,
                "production_approved_by": frappe.session.user,
                "production_approved_at": now,
                "status": "قيد الإنتاج / In Production",
            })
    elif stage == "packaging":
        if cint(operation.produced_meals) < planned:
            frappe.throw(_("اعتمد الإنتاج أولاً / Approve production first"))
        if cint(operation.packaged_meals) < planned:
            updates.update({
                "packaged_meals": planned,
                "kitchen_ready_meals": planned,
                "kitchen_ready_approved": 1,
                "kitchen_ready_by": frappe.session.user,
                "kitchen_ready_time": now,
                "packaging_approved_by": frappe.session.user,
                "packaging_approved_at": now,
                "status": "جاهز للتحميل / Ready to Load",
            })
    else:
        if cint(operation.packaged_meals) < planned:
            frappe.throw(_("اعتمد التغليف أولاً / Approve packaging first"))
        if cint(operation.loaded_meals) < planned:
            updates.update({
                "loaded_meals": planned,
                "loading_approved_by": frappe.session.user,
                "loading_approved_at": now,
                "status": "جاهز للتحميل / Ready to Load",
            })

    if updates:
        frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, updates, update_modified=True)
    notes = _append_workflow_note(operation.name, STAGE_LABELS[stage], note)

    next_operation = None
    if stage == "loading":
        rows = frappe.get_all(
            "WAFD Iftar Daily Operation",
            filters={"project": project.name, "operation_date": [">", operation.operation_date], "docstatus": ["<", 2]},
            fields=["name", "operation_date"],
            order_by="operation_date asc",
            limit_page_length=1,
        )
        next_operation = rows[0] if rows else None
        delivery_user = (project.delivery_supervisor_user or "").strip()
        if delivery_user:
            frappe.publish_realtime(
                "wafd_iftar_delivery_ready",
                {"project": project.name, "operation": operation.name, "operation_date": str(operation.operation_date)},
                user=delivery_user,
            )

    return {
        "operation": operation.name,
        "stage": stage,
        "updated": bool(updates),
        "workflow_notes": notes,
        "next_operation": next_operation,
    }


# ---------------------------------------------------------------------------
# Delivery allocation: creates only linked Iftar trips; no delivery module code
# is modified and the existing driver workflow remains authoritative.
# ---------------------------------------------------------------------------

@frappe.whitelist()
def approve_delivery_plan(operation_name, allocations, note=None):
    operation = frappe.get_doc("WAFD Iftar Daily Operation", operation_name)
    project = frappe.get_doc("WAFD Iftar Project", operation.project)
    _require_project_duty(project, "delivery")

    if cint(operation.delivery_plan_approved):
        frappe.throw(_("تم اعتماد خطة التوصيل مسبقاً / Delivery plan is already approved"))
    if cint(operation.loaded_meals) <= 0 or cint(operation.loaded_meals) < cint(operation.planned_meals):
        frappe.throw(_("بانتظار اعتماد تحميل المطبخ / Kitchen loading approval is required first"))

    rows = frappe.parse_json(allocations) if isinstance(allocations, str) else allocations
    rows = list(rows or [])
    if not rows:
        frappe.throw(_("أضف سيارة واحدة على الأقل / Add at least one vehicle allocation"))
    if len(rows) > 30:
        frappe.throw(_("الحد الأقصى 30 سيارة في خطة اليوم / Maximum 30 vehicles per day"))

    total = 0
    seen_vehicles = set()
    seen_drivers = set()
    normalized = []
    for index, row in enumerate(rows, 1):
        vehicle = (row.get("vehicle") or "").strip()
        driver = (row.get("driver") or "").strip()
        quantity = cint(row.get("quantity"))
        row_note = " ".join((row.get("note") or "").split()).strip()
        if not vehicle or not driver or quantity <= 0:
            frappe.throw(_("أكمل السيارة والسائق والكمية في الصف {0} / Complete row {0}").format(index))
        if vehicle in seen_vehicles:
            frappe.throw(_("لا يمكن تكرار نفس السيارة في خطة اليوم / A vehicle can appear only once"))
        if driver in seen_drivers:
            frappe.throw(_("لا يمكن تكرار نفس السائق في خطة اليوم / A driver can appear only once"))
        seen_vehicles.add(vehicle)
        seen_drivers.add(driver)
        capacity = cint(frappe.db.get_value("WAFD Vehicle", vehicle, "capacity_meals") or 0)
        if capacity and quantity > capacity:
            plate = frappe.db.get_value("WAFD Vehicle", vehicle, "plate_number") or vehicle
            frappe.throw(_("كمية السيارة {0} تتجاوز سعتها ({1}) / Vehicle capacity exceeded").format(plate, capacity))
        total += quantity
        normalized.append({"vehicle": vehicle, "driver": driver, "quantity": quantity, "note": row_note})

    expected = cint(operation.loaded_meals)
    if total != expected:
        frappe.throw(_("إجمالي توزيع السيارات ({0}) يجب أن يساوي عدد الوجبات المحملة ({1}) / Allocation total must equal loaded meals").format(total, expected))

    existing = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"iftar_daily_operation": operation.name, "status": ["!=", "ملغية / Cancelled"]},
        pluck="name",
        limit_page_length=100,
    )
    if existing:
        frappe.throw(_("توجد رحلات مرتبطة بهذا اليوم بالفعل. راجعها قبل إنشاء خطة جديدة / Existing linked trips must be reviewed first"))

    combined_notes = _append_workflow_note(operation.name, STAGE_LABELS["delivery_plan"], note)
    from wafd_one.delivery_supervisor import _ensure_delivery_location

    delivery_location = _ensure_delivery_location(project.distribution_site)
    planned_arrival = get_datetime(f"{getdate(operation.operation_date).isoformat()} 12:00:00")
    created = []
    capacity = max(cint(project.max_carton_capacity), 1)
    for row in normalized:
        trip_note_parts = [part for part in [combined_notes, row["note"]] if part]
        trip = frappe.get_doc({
            "doctype": "WAFD Delivery Trip",
            "trip_source": "خطة مشرف التوصيل / Delivery Supervisor Plan",
            "trip_date": operation.operation_date,
            "meal_type": "إفطار صائم / Iftar Saim",
            "planned_arrival": planned_arrival,
            "driver": row["driver"],
            "vehicle": row["vehicle"],
            "quantity": row["quantity"],
            "status": "تم التحميل / Loaded",
            "delivery_kind": "موقع إفطار صائم / Iftar Site",
            "delivery_location": delivery_location,
            "contracting_entity": project.contracting_entity,
            "contract": project.contract or None,
            "project": project.catering_project or None,
            "iftar_project": project.name,
            "iftar_daily_operation": operation.name,
            "iftar_link_type": "مرتبط بعقد / Contract Linked" if project.contract else "بدون عقد / No Contract",
            "notes": "\n".join(trip_note_parts),
            "iftar_dispatch_notes": "\n".join(trip_note_parts),
        }).insert(ignore_permissions=True)
        created.append({
            "name": trip.name,
            "vehicle": trip.vehicle,
            "driver": trip.driver,
            "quantity": cint(trip.quantity),
            "cartons": _cartons(trip.quantity, capacity),
        })

    now = now_datetime()
    frappe.db.set_value(
        "WAFD Iftar Daily Operation",
        operation.name,
        {
            "delivery_plan_approved": 1,
            "delivery_plan_approved_by": frappe.session.user,
            "delivery_plan_approved_at": now,
            "delivery_trip_count": len(created),
            "delivery_scheduled_meals": total,
            "status": "في التوزيع / Distributing",
        },
        update_modified=True,
    )

    return {"operation": operation.name, "trips": created, "total_meals": total}



@frappe.whitelist()
def save_iftar_camera_photo(image_data, filename=None):
    """Save camera-captured image evidence for the Iftar field workflow.

    The client sends only a fresh camera data URL.  The endpoint is restricted
    to Iftar operational roles and stores the image privately; callers receive
    only the resulting File URL.
    """
    roles = _roles()
    allowed = {
        "System Manager", "WAFD Operations Manager", "WAFD Project Manager",
        "WAFD Iftar Site Manager", "WAFD Iftar Supervisor",
    }
    if not (roles & allowed):
        frappe.throw(_("لا تملك صلاحية رفع صور إفطار الصائم / Not permitted to upload Iftar evidence"), frappe.PermissionError)
    import base64
    import binascii
    import re
    from frappe.utils.file_manager import save_file

    value = (image_data or "").strip()
    match = re.match(r"^data:(image/(?:jpeg|jpg|png|webp));base64,(.+)$", value, re.I | re.S)
    if not match:
        frappe.throw(_("الصورة يجب أن تكون ملتقطة من الكاميرا / Camera image is required"))
    mime = match.group(1).lower().replace("image/jpg", "image/jpeg")
    try:
        content = base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError):
        frappe.throw(_("تعذر قراءة صورة الكاميرا / Could not read camera image"))
    if not content:
        frappe.throw(_("صورة الكاميرا فارغة / Empty camera image"))
    if len(content) > 10 * 1024 * 1024:
        frappe.throw(_("حجم الصورة كبير جداً. التقط صورة بدقة أقل / Camera image is too large"))
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[mime]
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", (filename or "iftar-camera").strip())[:80].strip("-.") or "iftar-camera"
    if not safe.lower().endswith("." + ext):
        safe += "." + ext
    file_doc = save_file(safe, content, None, None, is_private=1)
    return {"name": file_doc.name, "file_url": file_doc.file_url}

# ---------------------------------------------------------------------------
# RC323 dedicated Site Manager / Iftar Supervisor portals
# ---------------------------------------------------------------------------

def _current_site_operation(project):
    operations = _operations(project)
    shaped = [
        _operation_payload(project, operation, idx + 1, len(operations), include_trips=True)
        for idx, operation in enumerate(operations)
    ]
    # Prefer a day that has reached delivery and still needs site closeout.
    return next((op for op in shaped if cint(op.get("delivery_plan_approved")) and not cint(op.get("site_report_approved"))), None) \
        or next((op for op in shaped if not cint(op.get("daily_report_sent"))), None) \
        or (shaped[-1] if shaped else None)


def _site_reports(operation_name):
    if not operation_name:
        return []
    rows = frappe.get_all(
        "WAFD Iftar Supervisor Daily Report",
        filters={"daily_operation": operation_name},
        fields=[
            "name", "supervisor_name", "supervisor_user", "planned_meals", "received_meals",
            "received_at", "report_submitted", "submitted_at", "manager_approved", "approved_at",
            "distributed_meals", "surplus_meals", "preservation_meals", "waste_meals",
        ],
        order_by="supervisor_name asc",
        limit_page_length=500,
    )
    return [dict(row) for row in rows]


def _supervisor_plans_payload(project_name):
    names = frappe.get_all(
        "WAFD Iftar Supervisor Plan",
        filters={"project": project_name},
        pluck="name",
        order_by="creation asc",
        limit_page_length=200,
    )
    rows = []
    for name in names:
        plan = frappe.get_doc("WAFD Iftar Supervisor Plan", name)
        rows.append({
            "name": plan.name,
            "supervisor_user": plan.supervisor_user or "",
            "supervisor_name": plan.supervisor_name or "",
            "supervisor_mobile": plan.supervisor_mobile or "",
            "assigned_meals": cint(plan.assigned_meals),
            "table_owners": [
                {
                    "table_owner_name": r.table_owner_name or "",
                    "mobile_no": r.mobile_no or "",
                    "distribution_point": r.distribution_point or "",
                    "delivery_location": r.delivery_location or "",
                    "meal_quantity": cint(r.meal_quantity),
                    "notes": r.notes or "",
                }
                for r in (plan.table_owners or [])
            ],
            "assistants": [
                {
                    "assistant_name": r.assistant_name or "",
                    "mobile_no": r.mobile_no or "",
                    "active": cint(r.active),
                    "notes": r.notes or "",
                }
                for r in (plan.assistants or [])
            ],
        })
    return rows


@frappe.whitelist()
def get_supervisor_user_options():
    if frappe.session.user in ("Guest", ""):
        frappe.throw(_("يجب تسجيل الدخول / Login required"), frappe.PermissionError)
    rows = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name", "mobile_no"],
        order_by="full_name asc, name asc",
        limit_page_length=500,
    )
    return [{"value": r.name, "label": r.full_name or r.name, "mobile_no": r.mobile_no or ""} for r in rows]


@frappe.whitelist()
def save_quick_supervisor_setup(project_name, plans_json):
    """Mobile-first one-screen setup for supervisors and table owners.

    RC326: run the entire supervisor-plan write as a trusted project-scoped
    operation. WAFD Iftar Distribution Recipient is a child table and must
    inherit permission from WAFD Iftar Project; on some Frappe v16 builds the
    nested child sync could otherwise be permission-checked as a standalone
    DocType for non-System-Manager site staff.
    """
    if frappe.session.user in ("Guest", ""):
        frappe.throw(_("يجب تسجيل الدخول / Login required"), frappe.PermissionError)
    project = frappe.get_doc("WAFD Iftar Project", project_name)
    duties = _project_access(project)
    if "management" not in duties and not ({"site", "project_manager"} & duties):
        frappe.throw(_("لا تملك صلاحية إعداد المشرفين لهذا المشروع / Not allowed to configure this project"), frappe.PermissionError)

    try:
        plans = json.loads(plans_json) if isinstance(plans_json, str) else (plans_json or [])
    except Exception:
        frappe.throw(_("بيانات المشرفين غير صالحة / Invalid supervisor setup data"))
    if not isinstance(plans, list) or not plans:
        frappe.throw(_("أضف مشرفاً واحداً على الأقل / Add at least one supervisor"))

    existing_reports = frappe.db.exists("WAFD Iftar Supervisor Daily Report", {"project": project.name})
    existing_names = frappe.get_all("WAFD Iftar Supervisor Plan", filters={"project": project.name}, pluck="name")
    if existing_reports and existing_names:
        frappe.throw(_("بدأ تشغيل تقارير المشرفين لهذا المشروع. عدّل الخطة من سجلها الحالي للحفاظ على السجل التشغيلي / Supervisor reports already started; edit the existing plan record to preserve history"))

    normalized = []
    total_meals = 0
    seen_users = set()
    for idx, raw in enumerate(plans, 1):
        raw = raw or {}
        user = _active_user(raw.get("supervisor_user"))
        if not user:
            frappe.throw(_("اختر حساب المشرف رقم {0} / Select the supervisor account").format(idx))
        if user in seen_users:
            frappe.throw(_("لا تكرر نفس حساب المشرف / Do not duplicate the same supervisor account"))
        seen_users.add(user)
        _ensure_team_role(user, SUPERVISOR_ROLE)
        name = (raw.get("supervisor_name") or frappe.utils.get_fullname(user) or user).strip()
        mobile = (raw.get("supervisor_mobile") or "").strip()
        owners = []
        for owner in raw.get("table_owners") or []:
            owner = owner or {}
            owner_name = (owner.get("table_owner_name") or "").strip()
            qty = cint(owner.get("meal_quantity"))
            if not owner_name and not qty:
                continue
            if not owner_name:
                frappe.throw(_("أدخل اسم صاحب السفرة للمشرف {0} / Enter the table-owner name").format(name))
            if qty <= 0:
                frappe.throw(_("أدخل عدد الوجبات لصاحب السفرة {0} / Enter a positive meal quantity").format(owner_name))
            owners.append({
                "table_owner_name": owner_name,
                "mobile_no": (owner.get("mobile_no") or "").strip(),
                "distribution_point": (owner.get("distribution_point") or project.distribution_site or "").strip(),
                "delivery_location": (owner.get("delivery_location") or "").strip(),
                "meal_quantity": qty,
                "notes": (owner.get("notes") or "").strip(),
            })
            total_meals += qty
        if not owners:
            frappe.throw(_("أضف صاحب سفرة واحداً على الأقل للمشرف {0} / Add at least one table owner").format(name))
        assistants = []
        for a in raw.get("assistants") or []:
            a = a or {}
            aname = (a.get("assistant_name") or "").strip()
            if aname:
                assistants.append({
                    "assistant_name": aname,
                    "mobile_no": (a.get("mobile_no") or "").strip(),
                    "active": 1 if cint(a.get("active", 1)) else 0,
                    "notes": (a.get("notes") or "").strip(),
                })
        normalized.append({"supervisor_user": user, "supervisor_name": name, "supervisor_mobile": mobile, "table_owners": owners, "assistants": assistants})

    if total_meals != cint(project.daily_meals):
        frappe.throw(_("إجمالي وجبات أصحاب السفر ({0}) يجب أن يساوي الوجبات اليومية للمشروع ({1}) / Allocated meals must equal project daily meals").format(total_meals, cint(project.daily_meals)))

    old_ignore = getattr(frappe.flags, "ignore_permissions", False)
    frappe.flags.ignore_permissions = True
    try:
        # Safe because destructive replacement is blocked once daily reports exist.
        for plan_name in existing_names:
            frappe.delete_doc("WAFD Iftar Supervisor Plan", plan_name, ignore_permissions=True, force=True)

        created = []
        manager_name = frappe.utils.get_fullname(frappe.session.user) or frappe.session.user
        for item in normalized:
            plan = frappe.get_doc({
                "doctype": "WAFD Iftar Supervisor Plan",
                "project": project.name,
                "manager_name": manager_name,
                "supervisor_user": item["supervisor_user"],
                "supervisor_name": item["supervisor_name"],
                "supervisor_mobile": item["supervisor_mobile"],
            })
            for owner in item["table_owners"]:
                plan.append("table_owners", owner)
            for assistant in item["assistants"]:
                plan.append("assistants", assistant)
            plan.flags.ignore_permissions = True
            plan.insert(ignore_permissions=True)
            created.append(plan.name)
            frappe.clear_cache(user=item["supervisor_user"])

        # Create today's task immediately once the site inspection is approved.
        generated = []
        operation = _current_site_operation(project)
        if operation and cint(operation.get("authority_inspection_approved")):
            from wafd_one.wafd_one.iftar_team import ensure_supervisor_reports
            result = ensure_supervisor_reports(operation.get("name")) or {}
            generated = result.get("created") or []

        return {
            "project": project.name,
            "created": created,
            "supervisors": len(created),
            "allocated_meals": total_meals,
            "generated_reports": generated,
            "plans": _supervisor_plans_payload(project.name),
        }
    finally:
        frappe.flags.ignore_permissions = old_ignore


@frappe.whitelist()
def get_site_portal_data():
    if frappe.session.user in ("Guest", ""):
        frappe.throw(_("يجب تسجيل الدخول / Login required"), frappe.PermissionError)
    projects = []
    for project in _visible_projects():
        duties = set(project.get("portal_duties") or [])
        if "site" not in duties and "management" not in duties:
            continue
        payload = _project_payload(project, include_all_operations=False, include_trips=True)
        operation = _current_site_operation(project)
        payload["site_operation"] = operation
        payload["supervisor_reports"] = _site_reports(operation.get("name") if operation else None)
        payload["supervisor_plans"] = _supervisor_plans_payload(project.name)
        payload["supervisor_setup_meals"] = sum(cint(x.get("assigned_meals")) for x in payload["supervisor_plans"])
        projects.append(payload)
    return {
        "mode": "site",
        "user": frappe.session.user,
        "full_name": frappe.utils.get_fullname(frappe.session.user) or frappe.session.user,
        "projects": projects,
    }


def _supervisor_report_payload(report_name):
    report = frappe.get_doc("WAFD Iftar Supervisor Daily Report", report_name)
    project = frappe.get_doc("WAFD Iftar Project", report.project)
    operation = frappe.get_doc("WAFD Iftar Daily Operation", report.daily_operation)
    return {
        "name": report.name,
        "project": report.project,
        "project_title": project.project_title or project.distribution_site or project.name,
        "distribution_site": project.distribution_site,
        "contracting_entity": project.contracting_entity,
        "operation_date": report.operation_date,
        "daily_operation": report.daily_operation,
        "supervisor_name": report.supervisor_name,
        "planned_meals": cint(report.planned_meals),
        "cartons": cint(report.cartons),
        "received_meals": cint(report.received_meals),
        "received_at": report.received_at,
        "report_submitted": cint(report.report_submitted),
        "manager_approved": cint(report.manager_approved),
        "site_received": cint(operation.site_receipt_approved),
        "table_owners": [
            {
                "name": row.name,
                "table_owner_name": row.table_owner_name,
                "mobile_no": row.mobile_no,
                "distribution_point": row.distribution_point,
                "planned_meals": cint(row.planned_meals),
                "delivered_meals": cint(row.delivered_meals),
                "owner_confirmed": cint(row.owner_confirmed),
                "delivery_time": row.delivery_time,
                "notes": row.notes,
            }
            for row in (report.table_owners or [])
        ],
        "assistants": [
            {
                "name": row.name,
                "assistant_name": row.assistant_name,
                "mobile_no": row.mobile_no,
                "attendance_status": row.attendance_status,
                "check_in_time": row.check_in_time,
            }
            for row in (report.assistants_attendance or [])
        ],
    }


@frappe.whitelist()
def get_supervisor_portal_data():
    if frappe.session.user in ("Guest", ""):
        frappe.throw(_("يجب تسجيل الدخول / Login required"), frappe.PermissionError)
    roles = _roles()
    filters = {"supervisor_user": frappe.session.user}
    if _is_global_manager(roles):
        filters = {}
    names = frappe.get_all(
        "WAFD Iftar Supervisor Daily Report",
        filters=filters,
        pluck="name",
        order_by="operation_date desc, creation desc",
        limit_page_length=200,
    )
    reports = [_supervisor_report_payload(name) for name in names]
    pending_plans = []
    plan_filters = {"supervisor_user": frappe.session.user}
    if _is_global_manager(roles):
        plan_filters = {}
    for plan_name in frappe.get_all("WAFD Iftar Supervisor Plan", filters=plan_filters, pluck="name", order_by="creation desc", limit_page_length=200):
        plan = frappe.get_doc("WAFD Iftar Supervisor Plan", plan_name)
        project = frappe.get_doc("WAFD Iftar Project", plan.project)
        pending_plans.append({
            "name": plan.name,
            "project": plan.project,
            "project_title": project.project_title or project.distribution_site or project.name,
            "distribution_site": project.distribution_site,
            "contracting_entity": project.contracting_entity,
            "supervisor_name": plan.supervisor_name,
            "assigned_meals": cint(plan.assigned_meals),
            "table_owners_count": cint(plan.table_owners_count),
        })
    return {
        "mode": "supervisor",
        "user": frappe.session.user,
        "full_name": frappe.utils.get_fullname(frappe.session.user) or frappe.session.user,
        "reports": reports,
        "plans": pending_plans,
    }
