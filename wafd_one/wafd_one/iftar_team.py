from __future__ import annotations

import math

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, nowdate


GLOBAL_MANAGEMENT_ROLES = {"System Manager", "WAFD Operations Manager"}
MANAGEMENT_ROLES = GLOBAL_MANAGEMENT_ROLES | {"WAFD Project Manager"}
TEAM_ROLES = MANAGEMENT_ROLES | {
    "WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor",
    "WAFD Delivery Supervisor", "WAFD Iftar Site Manager", "WAFD Iftar Supervisor",
}

PROJECT_TEAM_ROLE_MAP = {
    "project_manager_user": ("WAFD Project Manager",),
    "kitchen_supervisor_user": ("WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor"),
    "delivery_supervisor_user": ("WAFD Delivery Supervisor",),
    "site_manager_user": ("WAFD Iftar Site Manager",),
}


def _roles():
    return set(frappe.get_roles(frappe.session.user))


def _require(*allowed):
    if not (_roles() & set(allowed)):
        frappe.throw(_("غير مصرح بهذه المهمة / Not permitted for this task"), frappe.PermissionError)


def _validate_team_user(fieldname, user):
    user = (user or "").strip()
    if not user:
        return ""
    if not frappe.db.exists("User", {"name": user, "enabled": 1, "user_type": "System User"}):
        frappe.throw(_("اختر حساب موظف نشط / Select an active employee account"))
    user_roles = set(frappe.get_roles(user))
    # Management accounts may temporarily own any core task. This is useful
    # for initial setup and controlled testing, and mirrors their existing
    # server-side permission to execute every Iftar stage. Regular employee
    # accounts must still carry the exact operational role.
    if user_roles & GLOBAL_MANAGEMENT_ROLES:
        return user
    allowed_roles = set(PROJECT_TEAM_ROLE_MAP[fieldname])
    if not (user_roles & allowed_roles):
        labels = " أو ".join(allowed_roles)
        frappe.throw(_("الحساب {0} لا يحمل الدور المطلوب: {1} / User does not have the required role").format(user, labels))
    return user


def backfill_unambiguous_project_team():
    """Fill legacy blank assignments only when one active user owns the role.

    This makes upgrades useful for a single-role test/production account without
    guessing when more than one employee could legitimately own the assignment.
    """
    candidates = {}
    for fieldname, allowed_roles in PROJECT_TEAM_ROLE_MAP.items():
        users = set()
        for role in allowed_roles:
            users.update(frappe.get_all(
                "Has Role",
                filters={"role": role, "parenttype": "User"},
                pluck="parent",
                limit_page_length=1000,
            ))
        active = sorted(
            user for user in users
            if frappe.db.exists("User", {"name": user, "enabled": 1, "user_type": "System User"})
        )
        candidates[fieldname] = active[0] if len(active) == 1 else ""

    updated = 0
    for project in frappe.get_all(
        "WAFD Iftar Project",
        filters={"docstatus": ["<", 2]},
        fields=["name", *PROJECT_TEAM_ROLE_MAP],
        limit_page_length=1000,
    ):
        values = {
            fieldname: user
            for fieldname, user in candidates.items()
            if user and not (project.get(fieldname) or "").strip()
        }
        if values:
            frappe.db.set_value("WAFD Iftar Project", project.name, values, update_modified=False)
            updated += 1
    return {"updated_projects": updated, "unique_role_users": candidates}


def normalize_legacy_iftar_sequence():
    """Map pre-RC301 quantities to valid stages and reject impossible downstream approvals."""
    updated = 0
    rows = frappe.get_all(
        "WAFD Iftar Daily Operation", filters={"docstatus": ["<", 2]},
        fields=[
            "name", "owner", "modified", "modified_by", "produced_meals", "packaged_meals", "loaded_meals",
            "kitchen_started", "kitchen_ready_approved", "kitchen_ready_meals", "delivery_plan_approved",
            "site_receipt_approved", "site_receipt_time", "authority_inspection_approved",
            "site_report_approved", "daily_report_sent", "administration_report_approved", "status",
        ], limit_page_length=5000,
    )
    for row in rows:
        actor = row.modified_by if frappe.db.exists("User", row.modified_by) else "Administrator"
        values = {}
        if cint(row.produced_meals) > 0 and not cint(row.kitchen_started):
            values.update({"kitchen_started": 1, "kitchen_started_by": actor, "kitchen_started_at": row.modified})
        if cint(row.packaged_meals) > 0 and not cint(row.kitchen_ready_approved):
            values.update({
                "kitchen_ready_meals": max(cint(row.kitchen_ready_meals), cint(row.packaged_meals)),
                "kitchen_ready_approved": 1, "kitchen_ready_by": actor, "kitchen_ready_time": row.modified,
            })
        if cint(row.site_receipt_approved) and cint(row.loaded_meals) > 0 and not cint(row.delivery_plan_approved):
            values.update({
                "delivery_plan_approved": 1, "delivery_plan_approved_by": actor,
                "delivery_plan_approved_at": row.site_receipt_time or row.modified,
            })
        # Old test forms allowed inspection before a verified site receipt. Keep
        # the evidence fields, but the invalid approval must be repeated in order.
        if cint(row.authority_inspection_approved) and not cint(row.site_receipt_approved):
            values.update({"authority_inspection_approved": 0, "authority_inspection_approved_by": None})
        if cint(row.daily_report_sent):
            values.update({
                "site_report_approved": 1, "site_report_approved_by": actor, "site_report_approved_at": row.modified,
                "administration_report_approved": 1, "administration_report_approved_by": actor,
                "administration_report_approved_at": row.modified, "authority_report_sent_at": row.modified,
            })
        effective_site = cint(row.site_receipt_approved)
        effective_delivery = cint(row.delivery_plan_approved) or cint(values.get("delivery_plan_approved"))
        effective_ready = cint(row.kitchen_ready_approved) or cint(values.get("kitchen_ready_approved"))
        effective_started = cint(row.kitchen_started) or cint(values.get("kitchen_started"))
        status = (
            "مغلق / Closed" if cint(row.daily_report_sent) else
            "مستلم / Received" if effective_site else
            "في التوزيع / Distributing" if effective_delivery else
            "جاهز للتحميل / Ready to Load" if effective_ready else
            "قيد الإنتاج / In Production" if effective_started else "مخطط / Planned"
        )
        if status != row.status:
            values["status"] = status
        if values:
            frappe.db.set_value("WAFD Iftar Daily Operation", row.name, values, update_modified=False)
            updated += 1
    return {"updated_operations": updated}


@frappe.whitelist()
def assign_project_team(project_name, project_manager_user=None, kitchen_supervisor_user=None,
                        delivery_supervisor_user=None, site_manager_user=None):
    """Compatibility API for the management-only Employee Management board."""
    _require("System Manager", "WAFD Operations Manager")
    project = frappe.get_doc("WAFD Iftar Project", project_name)
    supplied = {
        "project_manager_user": project_manager_user,
        "kitchen_supervisor_user": kitchen_supervisor_user,
        "delivery_supervisor_user": delivery_supervisor_user,
        "site_manager_user": site_manager_user,
    }
    values = {fieldname: _validate_team_user(fieldname, user) for fieldname, user in supplied.items()}
    frappe.db.set_value("WAFD Iftar Project", project.name, values, update_modified=True)
    for user in set(values.values()) - {""}:
        frappe.clear_cache(user=user)
    return {"project": project.name, **values}


@frappe.whitelist()
def approve_project_plan(project_name):
    """Start a legacy draft after its core employees have been assigned.

    Field-supervisor allocations are intentionally not a start-up gate. They can
    be completed during the month and are validated when daily assignments are
    generated at the site.
    """
    _require("System Manager", "WAFD Operations Manager")
    project = frappe.get_doc("WAFD Iftar Project", project_name)
    # بدء المشروع يحتاج مدير المشروع ومشرف المطبخ فقط. مدير المشروع يسجل
    # المشرفين والمساعدين وأصحاب السفر بعد اعتماد الإدارة، وبقية الإسنادات
    # يمكن استكمالها قبل وصول المرحلة الخاصة بها.
    required_at_start = ("project_manager_user", "kitchen_supervisor_user")
    missing = [field for field in required_at_start if not (project.get(field) or "").strip()]
    if missing:
        frappe.throw(_("أسند مدير المشروع ومشرف المطبخ قبل اعتماد المشروع / Assign the project manager and kitchen supervisor first"))
    plans = frappe.get_all(
        "WAFD Iftar Supervisor Plan", filters={"project": project.name},
        fields=["name", "assigned_meals"], limit_page_length=1000,
    )
    assigned = sum(cint(row.assigned_meals) for row in plans)
    if cint(project.docstatus) == 0:
        project.submit()
    elif cint(project.docstatus) != 1:
        frappe.throw(_("المشروع ملغي ولا يمكن تشغيله / Cancelled project cannot be activated"))
    from wafd_one.wafd_one.iftar_pro import generate_daily_operations
    result = generate_daily_operations(project.name, ignore_permissions=True)

    # RC310: publishing means more than submitting the project. Clear every
    # assigned employee cache and push a realtime signal so an already-open
    # employee home can surface the task immediately without logging out.
    published_users = {
        (project.get("project_manager_user") or "").strip(),
        (project.get("kitchen_supervisor_user") or "").strip(),
        (project.get("delivery_supervisor_user") or "").strip(),
        (project.get("site_manager_user") or "").strip(),
    }
    published_users.update(
        (row or "").strip() for row in frappe.get_all(
            "WAFD Iftar Supervisor Plan", filters={"project": project.name},
            pluck="supervisor_user", limit_page_length=1000,
        )
    )
    published_users.discard("")
    for user in sorted(published_users):
        frappe.clear_cache(user=user)
        frappe.publish_realtime(
            "wafd_iftar_task_published",
            {"project": project.name, "date": str(project.start_date or "")},
            user=user,
        )
    return {
        "project": project.name, "operations": result, "supervisors": len(plans),
        "assigned_meals": assigned, "published_users": sorted(published_users),
        "published_count": len(published_users),
    }


def _submitted_operation(operation_name):
    operation = frappe.get_doc("WAFD Iftar Daily Operation", operation_name)
    project = frappe.get_doc("WAFD Iftar Project", operation.project)
    if cint(project.docstatus) != 1:
        frappe.throw(_("يجب اعتماد المشروع قبل التشغيل / Submit the project before operations"))
    return operation, project


def _assigned(project, fieldname):
    assigned_user = (project.get(fieldname) or "").strip()
    if not (_roles() & GLOBAL_MANAGEMENT_ROLES):
        if "WAFD Project Manager" in _roles():
            assigned_user = (project.get("project_manager_user") or "").strip()
        if not assigned_user:
            frappe.throw(_("يجب أن تسند الإدارة هذه المهمة لحساب الموظف أولاً / Management must assign this task to the employee first"), frappe.PermissionError)
        if assigned_user != frappe.session.user:
            frappe.throw(_("هذا المشروع مسند لموظف آخر / This project is assigned to another employee"), frappe.PermissionError)


def _delivery_rows(operation):
    trips = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"iftar_daily_operation": operation.name, "status": ["!=", "ملغية / Cancelled"]},
        fields=["name", "driver", "vehicle", "destination_name", "destination_map_url", "quantity", "planned_arrival", "actual_departure", "actual_arrival", "status", "iftar_cartons", "iftar_bread_quantity", "iftar_carts", "iftar_tablecloths", "iftar_waste_bags", "iftar_gloves", "iftar_masks", "iftar_shoe_covers", "iftar_loading_photo"],
        order_by="creation asc", limit_page_length=500,
    )
    if not trips:
        return []
    proof_map = {
        row.delivery_trip: row for row in frappe.get_all(
            "WAFD Delivery Proof", filters={"delivery_trip": ["in", [x.name for x in trips]]},
            fields=["delivery_trip", "received_quantity", "rejected_quantity", "receiver_name", "delivery_time", "delivery_photo", "status"],
            limit_page_length=500,
        )
    }
    for trip in trips:
        trip["proof"] = proof_map.get(trip.name)
    return trips


def sync_delivery_schedule(operation_name):
    """Persist the existing driver schedule state on its linked Iftar day.

    Delivery Trip remains the only driver workflow.  This bridge only mirrors
    auditable facts and never creates an Iftar-specific trip.
    """
    operation_state = frappe.db.get_value(
        "WAFD Iftar Daily Operation", operation_name,
        ["loaded_meals", "status", "site_received_meals", "site_receipt_approved"], as_dict=True
    ) if operation_name else None
    if not operation_state:
        return
    trips = frappe.get_all(
        "WAFD Delivery Trip",
        filters={"iftar_daily_operation": operation_name, "status": ["!=", "ملغية / Cancelled"]},
        fields=["name", "driver", "vehicle", "destination_name", "quantity", "actual_departure", "actual_arrival"],
        order_by="creation asc", limit_page_length=500,
    )
    trip_names = [row.name for row in trips]
    proofs = frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": ["in", trip_names]},
        fields=["delivery_trip", "received_quantity", "receiver_name", "delivery_time", "delivery_photo"],
        order_by="delivery_time asc", limit_page_length=500,
    ) if trip_names else []
    scheduled = sum(cint(row.quantity) for row in trips)
    verified = sum(cint(row.received_quantity) for row in proofs)
    arrivals = [row.delivery_time for row in proofs if row.delivery_time] + [row.actual_arrival for row in trips if row.actual_arrival]
    receivers = list(dict.fromkeys((row.receiver_name or "").strip() for row in proofs if (row.receiver_name or "").strip()))
    photos = list(dict.fromkeys(row.delivery_photo for row in proofs if row.delivery_photo))
    summaries = []
    for row in trips:
        parts = [row.driver or "سائق غير محدد", row.vehicle or "مركبة غير محددة"]
        if row.destination_name:
            parts.append(row.destination_name)
        parts.append(f"{cint(row.quantity)} وجبة")
        summaries.append(" — ".join(parts))
    delivered = min(verified, cint(operation_state.loaded_meals))
    values = {
        "delivery_trip_count": len(trips),
        "delivery_scheduled_meals": scheduled,
        "delivery_verified_meals": verified,
        "delivery_proof_count": len(proofs),
        "delivery_last_arrival": max(arrivals) if arrivals else None,
        "delivery_receivers": "، ".join(receivers),
        "delivery_proof_photos": "\n".join(photos),
        "driver_schedule_summary": "\n".join(summaries),
        # A signed/photo/GPS proof is the authoritative arrival at the site.
        "delivered_meals": delivered,
    }
    if operation_state.status not in ("مستلم / Received", "مغلق / Closed"):
        values["status"] = "في التوزيع / Distributing" if delivered else (
            "جاهز للتحميل / Ready to Load" if cint(operation_state.loaded_meals) else operation_state.status
        )
    if cint(operation_state.site_received_meals) > delivered:
        values.update({
            "site_received_meals": delivered, "site_receipt_approved": 0,
            "site_receipt_time": None, "site_received_by": None,
        })
    if len({row.vehicle for row in trips if row.vehicle}) == 1:
        values["vehicle"] = next((row.vehicle for row in trips if row.vehicle), None)
    if trips:
        values["driver_name"] = "، ".join(dict.fromkeys(row.driver for row in trips if row.driver))
    frappe.db.set_value("WAFD Iftar Daily Operation", operation_name, values, update_modified=True)
    return values


def sync_iftar_delivery_trip(doc, method=None):
    if doc.get("iftar_daily_operation"):
        sync_delivery_schedule(doc.iftar_daily_operation)


def sync_iftar_delivery_proof(doc, method=None):
    operation_name = frappe.db.get_value("WAFD Delivery Trip", doc.delivery_trip, "iftar_daily_operation")
    if operation_name:
        sync_delivery_schedule(operation_name)


def _assignment_duties(project, user=None):
    """Return the duties explicitly assigned to *user* on this project.

    RC310 deliberately uses the project assignment fields as the source of
    truth.  A user can legitimately carry several WAFD roles from other
    projects, so role priority must never decide which Iftar project is visible.
    """
    user = (user or frappe.session.user or "").strip()
    duties = []
    mapping = (
        ("project_manager", "project_manager_user"),
        ("kitchen", "kitchen_supervisor_user"),
        ("delivery", "delivery_supervisor_user"),
        ("site", "site_manager_user"),
    )
    for duty, fieldname in mapping:
        if (project.get(fieldname) or "").strip() == user:
            duties.append(duty)
    return duties


def _visible_project_rows(roles, project_name=None):
    fields = [
        "name", "project_title", "season_type", "distribution_site", "contracting_entity",
        "start_date", "end_date", "daily_meals", "number_of_days", "total_meals",
        "total_revenue", "total_project_cost", "expected_profit", "status", "docstatus",
        "modified", "project_manager_user", "kitchen_supervisor_user",
        "delivery_supervisor_user", "site_manager_user",
    ]
    filters = {
        "docstatus": ["<", 2],
        "status": ["not in", ["مكتمل / Completed", "ملغي / Cancelled", "مغلق / Closed"]],
    }
    if project_name:
        filters["name"] = project_name

    if roles & GLOBAL_MANAGEMENT_ROLES:
        rows = frappe.get_list(
            "WAFD Iftar Project", filters=filters, fields=fields,
            order_by="start_date desc", limit_page_length=200,
        )
        for row in rows:
            row["my_duties"] = ["administration"]
        return rows

    # Employee visibility is driven by the explicit project assignment, not by
    # whichever role happens to appear first in frappe.get_roles().  get_all is
    # safe here because we filter the result to the current user's own links
    # before returning anything to the caller.
    filters["docstatus"] = 1
    candidates = frappe.get_all(
        "WAFD Iftar Project", filters=filters, fields=fields,
        order_by="start_date desc", limit_page_length=500,
    )
    supervisor_projects = set(frappe.get_all(
        "WAFD Iftar Supervisor Plan",
        filters={"supervisor_user": frappe.session.user},
        pluck="project", limit_page_length=1000,
    ))
    visible = []
    for row in candidates:
        duties = _assignment_duties(row)
        if row.name in supervisor_projects:
            duties.append("supervisor")
        if duties:
            row["my_duties"] = list(dict.fromkeys(duties))
            visible.append(row)
    return visible


def _fallback_mode_from_roles(roles):
    return (
        "project_manager" if "WAFD Project Manager" in roles else
        "kitchen" if roles & {"WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor"} else
        "delivery" if "WAFD Delivery Supervisor" in roles else
        "site" if "WAFD Iftar Site Manager" in roles else
        "supervisor" if "WAFD Iftar Supervisor" in roles else ""
    )


@frappe.whitelist()
def get_my_iftar_task_summary(date=None):
    """Small server-truth summary used by the employee home screen.

    This makes an approved Iftar assignment visible immediately even when the
    employee browser still has an older client-side role list cached.
    """
    if frappe.session.user in ("Guest", ""):
        return {"count": 0, "tasks": []}
    roles = _roles()
    if roles & GLOBAL_MANAGEMENT_ROLES:
        return {"count": 0, "tasks": []}
    target_date = getdate(date or nowdate())
    projects = _visible_project_rows(roles)
    names = [row.name for row in projects]
    operations = frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": ["in", names], "operation_date": target_date, "docstatus": ["<", 2]} if names else {"name": "__none__"},
        fields=["name", "project", "kitchen_ready_approved", "delivery_plan_approved", "site_receipt_approved", "site_report_approved", "daily_report_sent"],
        limit_page_length=500,
    )
    op_map = {row.project: row for row in operations}
    tasks = []
    for project in projects:
        operation = op_map.get(project.name)
        for duty in project.get("my_duties") or []:
            state = "waiting"
            if duty == "project_manager":
                state = "active"
            elif duty == "kitchen":
                state = "done" if operation and cint(operation.kitchen_ready_approved) else "active"
            elif duty == "delivery":
                state = "done" if operation and cint(operation.delivery_plan_approved) else ("active" if operation and cint(operation.kitchen_ready_approved) else "waiting")
            elif duty == "site":
                state = "done" if operation and cint(operation.site_report_approved) else ("active" if operation and cint(operation.delivery_plan_approved) else "waiting")
            elif duty == "supervisor":
                state = "active" if operation and cint(operation.site_receipt_approved) else "waiting"
            tasks.append({
                "project": project.name,
                "project_title": project.project_title,
                "distribution_site": project.distribution_site,
                "duty": duty,
                "state": state,
                "operation": operation.name if operation else None,
            })
    return {"count": len(tasks), "project_count": len(projects), "date": target_date, "tasks": tasks}


@frappe.whitelist()
def get_team_dashboard(date=None, project=None):
    roles = _roles()
    if not (roles & TEAM_ROLES):
        # The project link itself is authoritative in RC310. This fallback lets
        # a newly assigned employee open the task screen before the browser has
        # refreshed its cached role array, while still returning only their own
        # explicitly assigned projects below.
        has_assignment = bool(_visible_project_rows(roles, project_name=project))
        if not has_assignment:
            frappe.throw(_("لا توجد مهمة إفطار صائم مسندة لهذا الحساب / No Iftar task is assigned"), frappe.PermissionError)

    target_date = getdate(date or nowdate())
    projects = _visible_project_rows(roles, project_name=project)
    duty_modes = []
    for item in projects:
        duty_modes.extend(item.get("my_duties") or [])
    duty_modes = list(dict.fromkeys(duty_modes))
    if roles & GLOBAL_MANAGEMENT_ROLES:
        mode = "administration"
    elif len(duty_modes) == 1:
        mode = duty_modes[0]
    elif len(duty_modes) > 1:
        mode = "multi"
    else:
        mode = _fallback_mode_from_roles(roles)

    project_names = [row.name for row in projects]
    for item in projects:
        plans = frappe.get_all(
            "WAFD Iftar Supervisor Plan", filters={"project": item.name},
            fields=["assigned_meals", "table_owners_count", "assistants_count"], limit_page_length=1000,
        )
        item["supervisors_count"] = len(plans)
        item["table_owners_count"] = sum(cint(x.table_owners_count) for x in plans)
        item["assistants_count"] = sum(cint(x.assistants_count) for x in plans)
        item["assigned_meals"] = sum(cint(x.assigned_meals) for x in plans)

    operations = frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": ["in", project_names], "operation_date": target_date, "docstatus": ["<", 2]} if project_names else {"name": "__none__"},
        fields=["name", "project", "operation_date", "status", "planned_meals", "produced_meals", "packaged_meals", "loaded_meals", "delivered_meals", "received_meals", "completion_percent", "kitchen_started", "kitchen_started_by", "kitchen_started_at", "kitchen_ready_meals", "kitchen_ready_approved", "kitchen_ready_by", "kitchen_ready_time", "kitchen_shortage_reported", "kitchen_shortage_notes", "delivery_plan_approved", "delivery_plan_approved_by", "delivery_plan_approved_at", "authority_inspection_approved", "authority_inspection_approved_by", "authority_inspection_time", "delivery_trip_count", "delivery_scheduled_meals", "delivery_verified_meals", "delivery_proof_count", "delivery_last_arrival", "site_received_meals", "site_receipt_approved", "site_receipt_time", "site_received_by", "site_report_approved", "site_report_approved_by", "site_report_approved_at", "administration_report_approved", "administration_report_approved_by", "administration_report_approved_at", "daily_report_sent", "authority_report_recipient", "authority_report_sent_at"],
        order_by="project asc", limit_page_length=500,
    )
    project_map = {row.name: row for row in projects}
    for operation in operations:
        meta = project_map.get(operation.project) or {}
        operation["project_title"] = meta.get("project_title") or operation.project
        operation["distribution_site"] = meta.get("distribution_site") or ""
        operation["my_duties"] = meta.get("my_duties") or []
        operation["cartons"] = (cint(operation.planned_meals) + 24) // 25
        operation["deliveries"] = _delivery_rows(operation)
        stages = [
            ("الخطة", 1, meta.get("modified")),
            ("بدء المطبخ", operation.kitchen_started, operation.kitchen_started_at),
            ("جاهزية المطبخ", operation.kitchen_ready_approved, operation.kitchen_ready_time),
            ("اعتماد التوصيل", operation.delivery_plan_approved, operation.delivery_plan_approved_at),
            ("استلام الموقع", operation.site_receipt_approved, operation.site_receipt_time),
            ("فحص الجهة", operation.authority_inspection_approved, operation.authority_inspection_time),
            ("تقرير الموقع", operation.site_report_approved, operation.site_report_approved_at),
            ("إرسال الإدارة", operation.daily_report_sent, operation.authority_report_sent_at),
        ]
        operation["stages"] = [{"label": label, "done": cint(done), "time": when if cint(done) else None} for label, done, when in stages]

    # Fetch reports only when one of the user's actual assignments requires them.
    duty_set = set(duty_modes)
    reports = []
    if mode == "administration" or duty_set & {"project_manager", "site", "supervisor"}:
        report_filters = {"operation_date": target_date}
        if project_names:
            report_filters["project"] = ["in", project_names]
        else:
            report_filters["name"] = "__none__"
        if duty_set == {"supervisor"}:
            report_filters["supervisor_user"] = frappe.session.user
        reports = frappe.get_all(
            "WAFD Iftar Supervisor Daily Report", filters=report_filters,
            fields=["name", "project", "daily_operation", "supervisor_name", "supervisor_user", "planned_meals", "cartons", "received_meals", "received_at", "handover_photo", "distributed_meals", "surplus_meals", "preservation_meals", "waste_meals", "tables_spread_completed", "distribution_completed", "cleanup_completed", "distribution_photo", "closeout_photo", "report_submitted", "submitted_by", "manager_approved", "submitted_at", "approved_at"],
            order_by="supervisor_name asc", limit_page_length=1000,
        )
        for report in reports:
            report["owners"] = frappe.get_all(
                "WAFD Iftar Supervisor Daily Owner",
                filters={"parent": report.name, "parenttype": "WAFD Iftar Supervisor Daily Report"},
                fields=["name", "table_owner_name", "mobile_no", "distribution_point", "planned_meals", "delivered_meals", "delivery_time", "owner_confirmed"],
                order_by="idx asc", limit_page_length=500,
            )
            report["assistants"] = frappe.get_all(
                "WAFD Iftar Assistant Attendance",
                filters={"parent": report.name, "parenttype": "WAFD Iftar Supervisor Daily Report"},
                fields=["name", "assistant_name", "mobile_no", "attendance_status", "check_in_time", "check_out_time"],
                order_by="idx asc", limit_page_length=500,
            )
    return {
        "date": target_date, "roles": sorted(roles & TEAM_ROLES), "projects": projects,
        "operations": operations, "reports": reports, "mode": mode, "duty_modes": duty_modes,
    }


@frappe.whitelist()
def start_kitchen(operation_name):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "kitchen_supervisor_user")
    if cint(operation.kitchen_ready_approved):
        frappe.throw(_("تم اعتماد جاهزية المطبخ مسبقاً / Kitchen readiness is already approved"))
    values = {"kitchen_started": 1, "kitchen_started_by": frappe.session.user, "kitchen_started_at": now_datetime(), "status": "قيد الإنتاج / In Production"}
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    return values


@frappe.whitelist()
def update_kitchen(operation_name, ready_meals, shortage_reported=0, shortage_notes=None, approve=0):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "kitchen_supervisor_user")
    if cint(operation.kitchen_ready_approved):
        frappe.throw(_("تم اعتماد الجاهزية ولا يمكن تعديلها / Approved readiness cannot be changed"))
    ready = cint(ready_meals)
    if ready < 0 or ready > cint(operation.planned_meals):
        frappe.throw(_("العدد الجاهز يجب أن يكون بين صفر والعدد المخطط / Ready meals must be within the planned quantity"))
    if cint(approve) and ready <= 0:
        frappe.throw(_("سجل العدد الجاهز قبل اعتماد الجاهزية / Enter ready meals before approval"))
    shortage = cint(shortage_reported)
    if shortage and not (shortage_notes or "").strip():
        frappe.throw(_("اكتب بيان المواد الناقصة لإرساله للإدارة / Describe the material shortage"))
    values = {
        "kitchen_started": 1,
        "kitchen_started_by": operation.kitchen_started_by or frappe.session.user,
        "kitchen_started_at": operation.kitchen_started_at or now_datetime(),
        "kitchen_ready_meals": ready, "kitchen_ready_approved": cint(approve),
        "kitchen_ready_time": now_datetime() if cint(approve) else None,
        "kitchen_ready_by": frappe.session.user if cint(approve) else None,
        "kitchen_shortage_reported": shortage, "kitchen_shortage_notes": (shortage_notes or "").strip(),
        "produced_meals": ready,
    }
    if cint(approve):
        values["packaged_meals"] = ready
        values["status"] = "جاهز للتحميل / Ready to Load"
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    return values


@frappe.whitelist()
def update_delivery_allocation(trip_name, bread_quantity=0, carts=0, tablecloths=0, waste_bags=0, gloves=0, masks=0, shoe_covers=0, loading_photo=None, notes=None):
    """Add Iftar quantities to an existing driver trip; never create a second trip."""
    _require("System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor")
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    if not trip.iftar_daily_operation:
        frappe.throw(_("هذه ليست عملية توصيل مرتبطة بإفطار الصائم / Trip is not linked to an Iftar operation"))
    operation, project = _submitted_operation(trip.iftar_daily_operation)
    _assigned(project, "delivery_supervisor_user")
    if not cint(operation.kitchen_ready_approved):
        frappe.throw(_("بانتظار اعتماد جاهزية المطبخ / Kitchen readiness approval is required"))
    values = {
        "iftar_cartons": int(math.ceil(cint(trip.quantity) / max(cint(project.max_carton_capacity or 25), 1))),
        "iftar_bread_quantity": cint(bread_quantity), "iftar_carts": cint(carts), "iftar_tablecloths": cint(tablecloths),
        "iftar_waste_bags": cint(waste_bags), "iftar_gloves": cint(gloves),
        "iftar_masks": cint(masks),
        "iftar_shoe_covers": cint(shoe_covers), "iftar_loading_photo": loading_photo,
        "iftar_dispatch_notes": (notes or "").strip(),
    }
    frappe.db.set_value("WAFD Delivery Trip", trip.name, values, update_modified=True)
    sync_delivery_schedule(operation.name)
    return {"trip": trip.name, **values}


@frappe.whitelist()
def approve_delivery_dispatch(operation_name):
    _require("System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "delivery_supervisor_user")
    if not cint(operation.kitchen_ready_approved):
        frappe.throw(_("لا يبدأ التوصيل قبل اعتماد جاهزية المطبخ / Kitchen readiness must be approved first"))
    trips = _delivery_rows(operation)
    if not trips:
        frappe.throw(_("اربط عمليات جدول التوصيل الحالية بهذا التشغيل؛ لن ينشئ النظام رحلة جديدة / Link the existing delivery schedule; no duplicate trip will be created"))
    incomplete = [row.name for row in trips if not row.driver or not row.vehicle or not row.destination_name or cint(row.quantity) <= 0 or cint(row.iftar_bread_quantity) <= 0 or not row.iftar_loading_photo]
    if incomplete:
        frappe.throw(_("أكمل السائق والمركبة والموقع والوجبات والخبز وصورة التحميل للعمليات: {0} / Complete trip allocation").format("، ".join(incomplete)))
    scheduled = sum(cint(row.quantity) for row in trips)
    if scheduled != cint(operation.kitchen_ready_meals):
        frappe.throw(_("إجمالي السيارات ({0}) يجب أن يساوي الجاهز من المطبخ ({1}) / Vehicle quantities must equal kitchen-ready meals").format(scheduled, cint(operation.kitchen_ready_meals)))
    values = {"delivery_plan_approved": 1, "delivery_plan_approved_by": frappe.session.user, "delivery_plan_approved_at": now_datetime(), "loaded_meals": scheduled, "status": "في التوزيع / Distributing"}
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    sync_delivery_schedule(operation.name)
    return {"operation": operation.name, "trips": len(trips), "loaded_meals": scheduled}


@frappe.whitelist()
def approve_site_receipt(operation_name, received_meals):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "site_manager_user")
    if not cint(operation.delivery_plan_approved):
        frappe.throw(_("يجب اعتماد مشرف التوصيل لتوزيع السيارات أولاً / Delivery supervisor approval is required first"))
    quantity = cint(received_meals)
    verified = cint(operation.delivery_verified_meals)
    if quantity <= 0 or quantity > verified or quantity > cint(operation.loaded_meals):
        frappe.throw(_("الاستلام يجب أن يكون أكبر من صفر وألا يتجاوز وصول السائق المثبت / Site receipt must not exceed verified driver arrivals"))
    values = {
        "site_received_meals": quantity, "site_receipt_approved": 1,
        "site_receipt_time": now_datetime(), "site_received_by": frappe.utils.get_fullname(frappe.session.user) or frappe.session.user,
    }
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    return values


@frappe.whitelist()
def approve_authority_inspection(operation_name, supervisor_name, photo, signature, notes=None, yogurt_checked=0, bread_checked=0, dates_checked=0, expiry_checked=0):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Site Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "site_manager_user")
    if not cint(operation.site_receipt_approved):
        frappe.throw(_("يجب اعتماد استلام مدير الموقع أولاً / Site receipt must be approved first"))
    if not (supervisor_name or "").strip() or not photo or not signature:
        frappe.throw(_("اسم مفتش الجودة والتغذية وصورة الفحص والتوقيع مطلوبة / Inspector name, photo and signature are required"))
    if not all(cint(x) for x in (yogurt_checked, bread_checked, dates_checked, expiry_checked)):
        frappe.throw(_("أكمل فحص الزبادي والخبز والتمر وتواريخ الصلاحية / Complete all food checks"))
    values = {
        "authority_supervisor_name": supervisor_name.strip(), "authority_inspection_photo": photo,
        "authority_inspector_signature": signature,
        "authority_inspection_notes": (notes or "").strip(), "yogurt_checked": 1, "bread_checked": 1,
        "dates_checked": 1, "expiry_checked": 1, "authority_inspection_approved": 1,
        "authority_inspection_approved_by": frappe.session.user, "authority_inspection_time": now_datetime(),
    }
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    return values


@frappe.whitelist()
def ensure_supervisor_reports(operation_name):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "site_manager_user")
    if not cint(operation.site_receipt_approved):
        frappe.throw(_("يجب اعتماد استلام مدير الموقع قبل تجهيز تكليفات المشرفين / Site receipt is required before supervisor assignments"))
    created, skipped = [], []
    plans = frappe.get_all("WAFD Iftar Supervisor Plan", filters={"project": project.name, "active": 1}, pluck="name", order_by="creation asc", limit_page_length=500)
    if not plans:
        frappe.throw(_("لم تُسجل خطة المشرفين لهذا المشروع. تطلب الإدارة إضافة المشرفين وأصحاب السفر أولاً / Add the project supervisor plan first"))
    for name in plans:
        plan = frappe.get_doc("WAFD Iftar Supervisor Plan", name)
        if not plan.supervisor_user:
            skipped.append(plan.supervisor_name)
            continue
        existing = frappe.db.get_value("WAFD Iftar Supervisor Daily Report", {"daily_operation": operation.name, "supervisor_plan": plan.name}, "name")
        if existing:
            continue
        report = frappe.get_doc({
            "doctype": "WAFD Iftar Supervisor Daily Report", "project": project.name,
            "daily_operation": operation.name, "operation_date": operation.operation_date,
            "supervisor_plan": plan.name, "supervisor_user": plan.supervisor_user,
            "supervisor_name": plan.supervisor_name, "supervisor_mobile": plan.supervisor_mobile,
            "site_manager_user": project.site_manager_user, "planned_meals": plan.assigned_meals,
            "cartons": int(math.ceil(cint(plan.assigned_meals) / max(cint(project.max_carton_capacity or 25), 1))),
        })
        for owner in plan.table_owners or []:
            report.append("table_owners", {"table_owner_name": owner.table_owner_name, "mobile_no": owner.mobile_no, "distribution_point": owner.distribution_point or owner.delivery_location, "planned_meals": owner.meal_quantity, "planned_bread": owner.bread_quantity, "planned_tablecloths": owner.tablecloths_quantity})
        for assistant in plan.assistants or []:
            if cint(assistant.active):
                report.append("assistants_attendance", {"assistant_name": assistant.assistant_name, "mobile_no": assistant.mobile_no, "attendance_status": "لم يسجل / Not Marked"})
        report.insert(ignore_permissions=True)
        created.append(report.name)
    if not created and skipped:
        frappe.throw(_("اربط حسابات المستخدمين للمشرفين: {0} / Link supervisor user accounts").format("، ".join(skipped)))
    return {"created": created, "skipped_without_user": skipped, "total_plans": len(plans)}


@frappe.whitelist()
def receive_for_supervisor(report_name, received_meals, tablecloths=0, bread_bags=0, carts=0, waste_bags=0, gloves=0, masks=0, shoe_covers=0, handover_photo=None):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    report = frappe.get_doc("WAFD Iftar Supervisor Daily Report", report_name)
    project = frappe.get_doc("WAFD Iftar Project", report.project)
    _assigned(project, "site_manager_user")
    operation = frappe.get_doc("WAFD Iftar Daily Operation", report.daily_operation)
    if not cint(operation.site_receipt_approved):
        frappe.throw(_("يجب اعتماد استلام مدير الموقع أولاً / Site manager receipt must be approved first"))
    if not handover_photo:
        frappe.throw(_("صورة تسليم الوجبات والعهدة للمشرف مطلوبة / Supervisor handover photo is required"))
    quantity = cint(received_meals)
    if quantity < 0 or quantity > cint(report.planned_meals):
        frappe.throw(_("كمية المشرف يجب أن تكون ضمن الكمية المسندة / Supervisor quantity must be within the assigned amount"))
    other_received = sum(cint(row.received_meals) for row in frappe.get_all(
        "WAFD Iftar Supervisor Daily Report",
        filters={"daily_operation": report.daily_operation, "name": ["!=", report.name]},
        fields=["received_meals"], limit_page_length=1000,
    ))
    if other_received + quantity > cint(operation.site_received_meals):
        frappe.throw(_("إجمالي التسليم للمشرفين يتجاوز الوصول المثبت من السائقين / Supervisor handovers exceed verified driver arrivals"))
    supply_map = {
        "bread_bags": "iftar_bread_quantity", "carts": "iftar_carts",
        "tablecloths": "iftar_tablecloths", "waste_bags": "iftar_waste_bags",
        "gloves": "iftar_gloves", "masks": "iftar_masks", "shoe_covers": "iftar_shoe_covers",
    }
    requested_supplies = {
        "bread_bags": cint(bread_bags), "carts": cint(carts), "tablecloths": cint(tablecloths),
        "waste_bags": cint(waste_bags), "gloves": cint(gloves), "masks": cint(masks),
        "shoe_covers": cint(shoe_covers),
    }
    other_reports = frappe.get_all(
        "WAFD Iftar Supervisor Daily Report",
        filters={"daily_operation": report.daily_operation, "name": ["!=", report.name]},
        fields=list(supply_map), limit_page_length=1000,
    )
    trips = _delivery_rows(operation)
    for report_field, trip_field in supply_map.items():
        inbound = sum(cint(row.get(trip_field)) for row in trips)
        allocated = sum(cint(row.get(report_field)) for row in other_reports) + requested_supplies[report_field]
        # Legacy trips may not contain detailed supply quantities.  Enforce the
        # vehicle plan whenever a positive inbound quantity was recorded.
        if inbound and allocated > inbound:
            frappe.throw(_("توزيع عهدة المشرفين يتجاوز الكمية المحملة في السيارات ({0}) / Supervisor supplies exceed vehicle allocation").format(report_field))
    received_at = now_datetime()
    # These fields belong to the Site Manager handover step.  Update only them
    # directly so the Site Manager never re-saves supervisor-owned child rows
    # or report evidence, which is intentionally protected by the report
    # controller.
    values = {
        "received_meals": quantity, "received_at": received_at,
        "handover_photo": handover_photo, "site_manager_user": frappe.session.user,
        "tablecloths": cint(tablecloths), "bread_bags": cint(bread_bags), "carts": cint(carts),
        "waste_bags": cint(waste_bags), "gloves": cint(gloves),
        "masks": cint(masks), "shoe_covers": cint(shoe_covers),
    }
    frappe.db.set_value("WAFD Iftar Supervisor Daily Report", report.name, values, update_modified=True)
    frappe.clear_cache(user=report.supervisor_user)
    return {"name": report.name, "received_meals": quantity, "received_at": received_at}


def _supervisor_report(report_name):
    report = frappe.get_doc("WAFD Iftar Supervisor Daily Report", report_name)
    project = frappe.get_doc("WAFD Iftar Project", report.project)
    if not (_roles() & GLOBAL_MANAGEMENT_ROLES) and report.supervisor_user != frappe.session.user:
        frappe.throw(_("هذا التقرير مسند لمشرف آخر / Report is assigned to another supervisor"), frappe.PermissionError)
    return report, project


@frappe.whitelist()
def confirm_owner_handover(report_name, owner_row_name, delivered_meals, delivered_bread=0, delivered_tablecloths=0, delivery_photo=None, recipient_signature=None, notes=None):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Supervisor")
    report, project = _supervisor_report(report_name)
    if not cint(report.received_meals):
        frappe.throw(_("يجب استلام الوجبات والعهدة من مدير الموقع أولاً / Receive the handover from the site manager first"))
    row = next((item for item in report.table_owners if item.name == owner_row_name), None)
    if not row:
        frappe.throw(_("صاحب السفرة غير موجود في هذا التكليف / Table owner is not part of this assignment"))
    quantity = cint(delivered_meals)
    if quantity < 0 or quantity > cint(row.planned_meals):
        frappe.throw(_("كمية التسليم لا تتجاوز الكمية المخططة لصاحب السفرة / Delivered quantity exceeds owner allocation"))
    bread = cint(delivered_bread)
    tablecloths = cint(delivered_tablecloths)
    if bread < 0 or bread > cint(row.planned_bread) or tablecloths < 0 or tablecloths > cint(row.planned_tablecloths):
        frappe.throw(_("الخبز والسفر المسلمة لا تتجاوز الكمية المخططة / Bread and tablecloths must not exceed the allocation"))
    if not delivery_photo or not recipient_signature:
        frappe.throw(_("صورة التسليم وتوقيع صاحب السفرة مطلوبان / Delivery photo and table-owner signature are required"))
    row.delivered_meals = quantity
    row.delivered_bread = bread
    row.delivered_tablecloths = tablecloths
    row.delivery_photo = delivery_photo
    row.recipient_signature = recipient_signature
    row.owner_confirmed = 1
    row.delivery_time = now_datetime().time()
    row.delivered_at = now_datetime()
    row.notes = (notes or "").strip()
    report.save(ignore_permissions=True)
    return {"report": report.name, "owner": row.table_owner_name, "delivered_meals": quantity, "delivery_time": row.delivery_time}


@frappe.whitelist()
def mark_assistant_attendance(report_name, assistant_row_name, status, absence_reason=None):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Supervisor")
    report, project = _supervisor_report(report_name)
    allowed = {"حاضر / Present", "غائب / Absent"}
    if status not in allowed:
        frappe.throw(_("اختر حاضر أو غائب / Select Present or Absent"))
    row = next((item for item in report.assistants_attendance if item.name == assistant_row_name), None)
    if not row:
        frappe.throw(_("المساعد غير موجود في هذا التكليف / Assistant is not assigned to this report"))
    row.attendance_status = status
    row.marked_at = now_datetime()
    row.absence_reason = (absence_reason or "").strip()
    if status == "غائب / Absent" and not row.absence_reason:
        frappe.throw(_("أدخل سبب الغياب / Enter the absence reason"))
    if status == "حاضر / Present" and not row.check_in_time:
        row.check_in_time = now_datetime().time()
    report.save(ignore_permissions=True)
    return {"report": report.name, "assistant": row.assistant_name, "status": status}


@frappe.whitelist()
def submit_supervisor_report(report_name, distributed_meals, surplus_meals=0, preservation_meals=0, waste_meals=0, tables_spread_completed=0, distribution_completed=0, cleanup_completed=0, distribution_photo=None, closeout_photo=None, preservation_receipt_photo=None, preservation_receiver_signature=None, supervisor_notes=None, media_links=None):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Supervisor")
    report, project = _supervisor_report(report_name)
    if not cint(report.received_meals):
        frappe.throw(_("لم تستلم الوجبات من مدير الموقع بعد / Meals have not been handed over yet"))
    pending_owners = [row.table_owner_name for row in report.table_owners if not cint(row.owner_confirmed)]
    if pending_owners:
        frappe.throw(_("اعتمد التسليم لأصحاب السفر أولاً: {0} / Confirm every table-owner handover first").format("، ".join(pending_owners)))
    owner_delivered = sum(cint(row.delivered_meals) for row in report.table_owners)
    if owner_delivered != cint(report.received_meals):
        frappe.throw(_("إجمالي تسليم أصحاب السفر يجب أن يساوي الكمية المستلمة من الموقع ({0}) / Table-owner handovers must equal received meals").format(cint(report.received_meals)))
    values = [cint(distributed_meals), cint(surplus_meals), cint(preservation_meals), cint(waste_meals)]
    if any(value < 0 for value in values) or sum(values) != cint(report.received_meals):
        frappe.throw(_("الموزع والفائض وحفظ النعمة والتالف يجب أن يساوي المستلم ({0}) / Closeout quantities must equal received meals").format(cint(report.received_meals)))
    if not all(cint(x) for x in (tables_spread_completed, distribution_completed, cleanup_completed)):
        frappe.throw(_("أكمل فرش السفر والتوزيع ورفع السفر قبل إرسال التقرير / Complete all field closeout steps"))
    if not distribution_photo or not closeout_photo:
        frappe.throw(_("صورتا التوزيع ورفع السفر مطلوبتان / Distribution and closeout photos are required"))
    if values[2] and (not preservation_receipt_photo or not preservation_receiver_signature):
        frappe.throw(_("صورة وتوقيع استلام جمعية حفظ النعمة مطلوبان عند تسجيل كمية / Preservation receipt photo and signature are required"))
    report.update({
        "distributed_meals": values[0], "surplus_meals": values[1], "preservation_meals": values[2], "waste_meals": values[3],
        "tables_spread_completed": 1, "distribution_completed": 1, "cleanup_completed": 1,
        "distribution_photo": distribution_photo, "closeout_photo": closeout_photo,
        "closeout_at": now_datetime(), "preservation_receipt_photo": preservation_receipt_photo,
        "preservation_receiver_signature": preservation_receiver_signature, "supervisor_notes": (supervisor_notes or "").strip(),
        "media_links": (media_links or "").strip(), "report_submitted": 1,
        "submitted_by": frappe.session.user, "submitted_at": now_datetime(),
    })
    report.save(ignore_permissions=True)
    return {"report": report.name, "submitted_at": report.submitted_at}


@frappe.whitelist()
def approve_supervisor_report(report_name, notes=None):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    report = frappe.get_doc("WAFD Iftar Supervisor Daily Report", report_name)
    project = frappe.get_doc("WAFD Iftar Project", report.project)
    _assigned(project, "site_manager_user")
    if not cint(report.report_submitted):
        frappe.throw(_("يجب أن يرسل المشرف تقريره أولاً / Supervisor must submit the report first"))
    report.db_set({"manager_approved": 1, "approved_by": frappe.session.user, "approved_at": now_datetime(), "manager_notes": (notes or "").strip()}, update_modified=True)
    pending = frappe.db.count("WAFD Iftar Supervisor Daily Report", {"daily_operation": report.daily_operation, "manager_approved": 0})
    finalized = False
    # One approval action is enough: when the last supervisor report is
    # approved, consolidate the operation immediately and place it in the
    # administration inbox.  Previously a second, easy-to-miss button was
    # required, so the supervisor saw "approved" while management saw nothing.
    if not pending:
        operation = frappe.get_doc("WAFD Iftar Daily Operation", report.daily_operation)
        if not cint(operation.site_report_approved):
            finalize_daily_report(report.daily_operation)
            finalized = True
    return {"name": report.name, "pending_reports": pending, "site_report_finalized": finalized}


@frappe.whitelist()
def finalize_daily_report(operation_name):
    """Site manager consolidates approved supervisor reports for administration."""
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Site Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "site_manager_user")
    names = frappe.get_all("WAFD Iftar Supervisor Daily Report", filters={"daily_operation": operation.name}, pluck="name", limit_page_length=1000)
    if not names:
        frappe.throw(_("أنشئ تقارير المشرفين أولاً / Create supervisor reports first"))
    reports = [frappe.get_doc("WAFD Iftar Supervisor Daily Report", name) for name in names]
    pending = [report.supervisor_name for report in reports if not cint(report.manager_approved)]
    if pending:
        frappe.throw(_("لم تعتمد تقارير المشرفين: {0} / Supervisor reports are pending").format("، ".join(pending)))
    distributed = sum(cint(report.distributed_meals) for report in reports)
    surplus = sum(cint(report.surplus_meals) for report in reports)
    preservation = sum(cint(report.preservation_meals) for report in reports)
    waste = sum(cint(report.waste_meals) for report in reports)
    received = sum(cint(report.received_meals) for report in reports)
    if received != cint(operation.site_received_meals):
        frappe.throw(_("إجمالي استلام المشرفين ({0}) لا يساوي استلام مدير الموقع ({1}) / Supervisor receipts must match site-manager receipt").format(received, cint(operation.site_received_meals)))

    existing_photos = set(frappe.get_all(
        "WAFD Iftar Daily Photo", filters={"parent": operation.name, "parenttype": "WAFD Iftar Daily Operation"}, pluck="photo"
    ))
    next_idx = frappe.db.count("WAFD Iftar Daily Photo", {"parent": operation.name, "parenttype": "WAFD Iftar Daily Operation"})
    for report in reports:
        evidence = [
            (report.handover_photo, f"تسليم العهدة للمشرف {report.supervisor_name}"),
            (report.distribution_photo, f"توزيع المشرف {report.supervisor_name}"),
            (report.closeout_photo, f"رفع السفر للمشرف {report.supervisor_name}"),
        ]
        for photo_path, caption in evidence:
            if not photo_path or photo_path in existing_photos:
                continue
            next_idx += 1
            frappe.get_doc({
                "doctype": "WAFD Iftar Daily Photo", "parent": operation.name,
                "parenttype": "WAFD Iftar Daily Operation", "parentfield": "daily_photos", "idx": next_idx,
                "photo": photo_path, "caption": caption, "site_label": project.distribution_site,
                "uploaded_by": report.supervisor_user, "uploaded_at": report.submitted_at or report.received_at,
                "include_in_report": 1,
            }).db_insert()
            existing_photos.add(photo_path)
        for photo in report.daily_photos or []:
            if not photo.photo or photo.photo in existing_photos:
                continue
            next_idx += 1
            frappe.get_doc({
                "doctype": "WAFD Iftar Daily Photo", "parent": operation.name,
                "parenttype": "WAFD Iftar Daily Operation", "parentfield": "daily_photos", "idx": next_idx,
                "photo": photo.photo, "caption": photo.caption or f"تقرير المشرف {report.supervisor_name}",
                "site_label": photo.site_label or project.distribution_site,
                "table_owner_name": photo.table_owner_name, "uploaded_by": photo.uploaded_by or report.supervisor_user,
                "uploaded_at": photo.uploaded_at or report.submitted_at, "include_in_report": 1,
            }).db_insert()
            existing_photos.add(photo.photo)
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, {
        "received_meals": received, "surplus_meals": surplus, "preservation_society_quantity": preservation,
        "waste_meals": waste, "tables_spread_completed": int(all(cint(r.tables_spread_completed) for r in reports)),
        "cleanup_completed": int(all(cint(r.cleanup_completed) for r in reports)),
        "site_report_approved": 1, "site_report_approved_by": frappe.session.user, "site_report_approved_at": now_datetime(),
        "completion_percent": min(100, received / cint(operation.planned_meals) * 100) if cint(operation.planned_meals) else 0,
        "status": "مستلم / Received",
        "notes": ((operation.notes or "") + f"\nالتوزيع الفعلي: {distributed}").strip(),
    }, update_modified=True)
    return {"operation": operation.name, "received": received, "distributed": distributed, "surplus": surplus, "preservation": preservation, "waste": waste}


@frappe.whitelist()
def send_authority_report(operation_name, recipient, administration_signature=None, administration_stamp=None, administration_notes=None):
    """Final Project Manager approval and recorded dispatch to the authority."""
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "project_manager_user")
    if not cint(operation.site_report_approved):
        frappe.throw(_("بانتظار اعتماد مدير الموقع للتقرير المجمع / Site manager report approval is required"))
    if not cint(operation.authority_inspection_approved):
        frappe.throw(_("سجّل موافقة مفتش الجودة والتغذية وتوقيعه قبل الإرسال النهائي للجهة / Record the quality inspector approval and signature before final dispatch"))
    if not (recipient or "").strip():
        frappe.throw(_("حدد رئاسة شؤون الحرمين أو الجهة المتعاقدة المستلمة / Select the report recipient"))
    if not administration_signature or not administration_stamp:
        frappe.throw(_("توقيع مدير المشروع وختم الشركة مطلوبان قبل إرسال التقرير / Project Manager signature and company stamp are required"))
    timestamp = now_datetime()
    values = {
        "administration_report_approved": 1, "administration_report_approved_by": frappe.session.user,
        "administration_report_approved_at": timestamp, "authority_report_recipient": recipient.strip(),
        "authority_report_sent_at": timestamp, "daily_report_sent": 1, "status": "مغلق / Closed",
        "administration_signature": administration_signature, "administration_stamp": administration_stamp,
        "administration_notes": (administration_notes or "").strip(),
        "completion_percent": 100 if cint(operation.planned_meals) and cint(operation.received_meals) >= cint(operation.planned_meals) else operation.completion_percent,
    }
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    return {"operation": operation.name, "recipient": recipient.strip(), "sent_at": timestamp}
