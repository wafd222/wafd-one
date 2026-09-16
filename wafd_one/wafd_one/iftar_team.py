from __future__ import annotations

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
    allowed_roles = set(PROJECT_TEAM_ROLE_MAP[fieldname])
    if not (set(frappe.get_roles(user)) & allowed_roles):
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
    """Assign the permanent core team, including on an already-submitted project."""
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager")
    project = frappe.get_doc("WAFD Iftar Project", project_name)
    if not (_roles() & GLOBAL_MANAGEMENT_ROLES):
        if project.project_manager_user and project.project_manager_user != frappe.session.user:
            frappe.throw(_("هذا المشروع مسند لمدير مشروع آخر / Project is assigned to another manager"), frappe.PermissionError)
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
    missing = [field for field in PROJECT_TEAM_ROLE_MAP if not (project.get(field) or "").strip()]
    if missing:
        frappe.throw(_("أكمل إسناد مدير المشروع ومشرف المطبخ ومشرف التوصيل ومدير الموقع قبل اعتماد الخطة / Assign the complete core team first"))
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
    return {"project": project.name, "operations": result, "supervisors": len(plans), "assigned_meals": assigned}


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
        fields=["name", "driver", "vehicle", "destination_name", "destination_map_url", "quantity", "planned_arrival", "actual_departure", "actual_arrival", "status", "iftar_bread_quantity", "iftar_tablecloths", "iftar_waste_bags", "iftar_gloves", "iftar_shoe_covers", "iftar_loading_photo"],
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


def _project_filters(roles):
    filters = {"docstatus": ["<", 2], "status": ["not in", ["مكتمل / Completed", "ملغي / Cancelled", "مغلق / Closed"]]}
    if roles & GLOBAL_MANAGEMENT_ROLES:
        return filters
    filters["docstatus"] = 1
    field = None
    if "WAFD Project Manager" in roles:
        field = "project_manager_user"
    elif roles & {"WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor"}:
        field = "kitchen_supervisor_user"
    elif "WAFD Delivery Supervisor" in roles:
        field = "delivery_supervisor_user"
    elif "WAFD Iftar Site Manager" in roles:
        field = "site_manager_user"
    if field:
        filters[field] = frappe.session.user
    return filters


@frappe.whitelist()
def get_team_dashboard(date=None, project=None):
    roles = _roles()
    if not (roles & TEAM_ROLES):
        frappe.throw(_("لا توجد مهمة إفطار صائم مسندة لهذا الحساب / No Iftar task is assigned"), frappe.PermissionError)
    target_date = getdate(date or nowdate())
    mode = (
        "administration" if roles & GLOBAL_MANAGEMENT_ROLES else
        "project_manager" if "WAFD Project Manager" in roles else
        "kitchen" if roles & {"WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor"} else
        "delivery" if "WAFD Delivery Supervisor" in roles else
        "site" if "WAFD Iftar Site Manager" in roles else "supervisor"
    )
    project_filters = _project_filters(roles)
    assigned_projects = None
    if "WAFD Iftar Supervisor" in roles and not (roles & MANAGEMENT_ROLES):
        assigned_projects = frappe.get_all(
            "WAFD Iftar Supervisor Plan", filters={"supervisor_user": frappe.session.user},
            pluck="project", limit_page_length=500,
        )
        project_filters["name"] = ["in", assigned_projects] if assigned_projects else "__none__"
    if project:
        project_filters["name"] = project if assigned_projects is None or project in assigned_projects else "__none__"
    projects = frappe.get_list(
        "WAFD Iftar Project", filters=project_filters,
        fields=["name", "project_title", "season_type", "distribution_site", "contracting_entity", "start_date", "end_date", "daily_meals", "number_of_days", "total_meals", "total_revenue", "total_project_cost", "expected_profit", "status", "docstatus", "modified", "project_manager_user", "kitchen_supervisor_user", "delivery_supervisor_user", "site_manager_user"],
        order_by="start_date desc", limit_page_length=200,
    )
    project_names = [row.name for row in projects]
    for item in projects:
        plans = frappe.get_all("WAFD Iftar Supervisor Plan", filters={"project": item.name}, fields=["assigned_meals", "table_owners_count", "assistants_count"], limit_page_length=1000)
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

    # Kitchen and delivery staff do not need supervisor reports. Avoid touching
    # that DocType entirely so least-privilege accounts never trigger a permission dialog.
    reports = []
    if mode in {"administration", "project_manager", "site", "supervisor"}:
        report_filters = {"operation_date": target_date}
        if project_names:
            report_filters["project"] = ["in", project_names]
        else:
            report_filters["name"] = "__none__"
        if mode == "supervisor":
            report_filters["supervisor_user"] = frappe.session.user
        reports = frappe.get_list(
            "WAFD Iftar Supervisor Daily Report", filters=report_filters,
            fields=["name", "project", "daily_operation", "supervisor_name", "supervisor_user", "planned_meals", "cartons", "received_meals", "received_at", "handover_photo", "distributed_meals", "surplus_meals", "preservation_meals", "waste_meals", "tables_spread_completed", "distribution_completed", "cleanup_completed", "distribution_photo", "closeout_photo", "report_submitted", "submitted_by", "manager_approved", "submitted_at", "approved_at"],
            order_by="supervisor_name asc", limit_page_length=1000,
        )
        for report in reports:
            report["owners"] = frappe.get_all("WAFD Iftar Supervisor Daily Owner", filters={"parent": report.name, "parenttype": "WAFD Iftar Supervisor Daily Report"}, fields=["name", "table_owner_name", "mobile_no", "distribution_point", "planned_meals", "delivered_meals", "delivery_time", "owner_confirmed"], order_by="idx asc", limit_page_length=500)
            report["assistants"] = frappe.get_all("WAFD Iftar Assistant Attendance", filters={"parent": report.name, "parenttype": "WAFD Iftar Supervisor Daily Report"}, fields=["name", "assistant_name", "mobile_no", "attendance_status", "check_in_time", "check_out_time"], order_by="idx asc", limit_page_length=500)
    return {
        "date": target_date, "roles": sorted(roles & TEAM_ROLES), "projects": projects,
        "operations": operations, "reports": reports,
        "mode": mode,
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
    if not cint(operation.kitchen_started):
        frappe.throw(_("اضغط بدء عمل المطبخ أولاً / Start the kitchen stage first"))
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
def update_delivery_allocation(trip_name, bread_quantity=0, tablecloths=0, waste_bags=0, gloves=0, shoe_covers=0, loading_photo=None, notes=None):
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
        "iftar_bread_quantity": cint(bread_quantity), "iftar_tablecloths": cint(tablecloths),
        "iftar_waste_bags": cint(waste_bags), "iftar_gloves": cint(gloves),
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
def approve_authority_inspection(operation_name, supervisor_name, photo, notes=None, yogurt_checked=0, bread_checked=0, dates_checked=0, expiry_checked=0):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Site Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "site_manager_user")
    if not cint(operation.site_receipt_approved):
        frappe.throw(_("يجب اعتماد استلام مدير الموقع أولاً / Site receipt must be approved first"))
    if not (supervisor_name or "").strip() or not photo:
        frappe.throw(_("اسم مفتش التغذية وصورة الفحص مطلوبان / Inspector name and inspection photo are required"))
    if not all(cint(x) for x in (yogurt_checked, bread_checked, dates_checked, expiry_checked)):
        frappe.throw(_("أكمل فحص الزبادي والخبز والتمر وتواريخ الصلاحية / Complete all food checks"))
    values = {
        "authority_supervisor_name": supervisor_name.strip(), "authority_inspection_photo": photo,
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
    if not cint(operation.authority_inspection_approved):
        frappe.throw(_("يجب اعتماد فحص الجهة قبل تجهيز تكليفات المشرفين / Authority inspection is required before supervisor assignments"))
    created, skipped = [], []
    plans = frappe.get_all("WAFD Iftar Supervisor Plan", filters={"project": project.name}, pluck="name", order_by="creation asc", limit_page_length=500)
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
        })
        for owner in plan.table_owners or []:
            report.append("table_owners", {"table_owner_name": owner.table_owner_name, "mobile_no": owner.mobile_no, "distribution_point": owner.distribution_point or owner.delivery_location, "planned_meals": owner.meal_quantity})
        for assistant in plan.assistants or []:
            if cint(assistant.active):
                report.append("assistants_attendance", {"assistant_name": assistant.assistant_name, "mobile_no": assistant.mobile_no, "attendance_status": "لم يسجل / Not Marked"})
        report.insert(ignore_permissions=True)
        created.append(report.name)
    if not created and skipped:
        frappe.throw(_("اربط حسابات المستخدمين للمشرفين: {0} / Link supervisor user accounts").format("، ".join(skipped)))
    return {"created": created, "skipped_without_user": skipped, "total_plans": len(plans)}


@frappe.whitelist()
def receive_for_supervisor(report_name, received_meals, tablecloths=0, bread_bags=0, waste_bags=0, gloves=0, shoe_covers=0, handover_photo=None):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    report = frappe.get_doc("WAFD Iftar Supervisor Daily Report", report_name)
    project = frappe.get_doc("WAFD Iftar Project", report.project)
    _assigned(project, "site_manager_user")
    operation = frappe.get_doc("WAFD Iftar Daily Operation", report.daily_operation)
    if not cint(operation.site_receipt_approved):
        frappe.throw(_("يجب اعتماد استلام مدير الموقع أولاً / Site manager receipt must be approved first"))
    if not cint(operation.authority_inspection_approved):
        frappe.throw(_("يجب اعتماد فحص الجهة قبل تسليم الوجبات للمشرفين / Authority inspection is required before supervisor handover"))
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
    report.received_meals = quantity
    report.received_at = now_datetime()
    report.handover_photo = handover_photo
    for field in ("tablecloths", "bread_bags", "waste_bags", "gloves", "shoe_covers"):
        report.set(field, cint(locals()[field]))
    report.save(ignore_permissions=True)
    return {"name": report.name, "received_meals": report.received_meals, "received_at": report.received_at}


def _supervisor_report(report_name):
    report = frappe.get_doc("WAFD Iftar Supervisor Daily Report", report_name)
    project = frappe.get_doc("WAFD Iftar Project", report.project)
    if not (_roles() & GLOBAL_MANAGEMENT_ROLES) and report.supervisor_user != frappe.session.user:
        frappe.throw(_("هذا التقرير مسند لمشرف آخر / Report is assigned to another supervisor"), frappe.PermissionError)
    return report, project


@frappe.whitelist()
def confirm_owner_handover(report_name, owner_row_name, delivered_meals, notes=None):
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
    row.delivered_meals = quantity
    row.owner_confirmed = 1
    row.delivery_time = now_datetime().time()
    row.notes = (notes or "").strip()
    report.save(ignore_permissions=True)
    return {"report": report.name, "owner": row.table_owner_name, "delivered_meals": quantity, "delivery_time": row.delivery_time}


@frappe.whitelist()
def mark_assistant_attendance(report_name, assistant_row_name, status):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Supervisor")
    report, project = _supervisor_report(report_name)
    allowed = {"حاضر / Present", "غائب / Absent"}
    if status not in allowed:
        frappe.throw(_("اختر حاضر أو غائب / Select Present or Absent"))
    row = next((item for item in report.assistants_attendance if item.name == assistant_row_name), None)
    if not row:
        frappe.throw(_("المساعد غير موجود في هذا التكليف / Assistant is not assigned to this report"))
    row.attendance_status = status
    if status == "حاضر / Present" and not row.check_in_time:
        row.check_in_time = now_datetime().time()
    report.save(ignore_permissions=True)
    return {"report": report.name, "assistant": row.assistant_name, "status": status}


@frappe.whitelist()
def submit_supervisor_report(report_name, distributed_meals, surplus_meals=0, preservation_meals=0, waste_meals=0, tables_spread_completed=0, distribution_completed=0, cleanup_completed=0, distribution_photo=None, closeout_photo=None, media_links=None):
    _require("System Manager", "WAFD Operations Manager", "WAFD Iftar Supervisor")
    report, project = _supervisor_report(report_name)
    if not cint(report.received_meals):
        frappe.throw(_("لم تستلم الوجبات من مدير الموقع بعد / Meals have not been handed over yet"))
    pending_owners = [row.table_owner_name for row in report.table_owners if not cint(row.owner_confirmed)]
    if pending_owners:
        frappe.throw(_("اعتمد التسليم لأصحاب السفر أولاً: {0} / Confirm every table-owner handover first").format("، ".join(pending_owners)))
    values = [cint(distributed_meals), cint(surplus_meals), cint(preservation_meals), cint(waste_meals)]
    if any(value < 0 for value in values) or sum(values) != cint(report.received_meals):
        frappe.throw(_("الموزع والفائض وحفظ النعمة والتالف يجب أن يساوي المستلم ({0}) / Closeout quantities must equal received meals").format(cint(report.received_meals)))
    if not all(cint(x) for x in (tables_spread_completed, distribution_completed, cleanup_completed)):
        frappe.throw(_("أكمل فرش السفر والتوزيع ورفع السفر قبل إرسال التقرير / Complete all field closeout steps"))
    if not distribution_photo or not closeout_photo:
        frappe.throw(_("صورتا التوزيع ورفع السفر مطلوبتان / Distribution and closeout photos are required"))
    report.update({
        "distributed_meals": values[0], "surplus_meals": values[1], "preservation_meals": values[2], "waste_meals": values[3],
        "tables_spread_completed": 1, "distribution_completed": 1, "cleanup_completed": 1,
        "distribution_photo": distribution_photo, "closeout_photo": closeout_photo,
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
    return {"name": report.name, "pending_reports": pending}


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
def send_authority_report(operation_name, recipient):
    """Final administration approval and recorded dispatch to the contracting authority."""
    _require("System Manager", "WAFD Operations Manager")
    operation, project = _submitted_operation(operation_name)
    if not cint(operation.site_report_approved):
        frappe.throw(_("بانتظار اعتماد مدير الموقع للتقرير المجمع / Site manager report approval is required"))
    if not (recipient or "").strip():
        frappe.throw(_("حدد رئاسة شؤون الحرمين أو الجهة المتعاقدة المستلمة / Select the report recipient"))
    timestamp = now_datetime()
    values = {
        "administration_report_approved": 1, "administration_report_approved_by": frappe.session.user,
        "administration_report_approved_at": timestamp, "authority_report_recipient": recipient.strip(),
        "authority_report_sent_at": timestamp, "daily_report_sent": 1, "status": "مغلق / Closed",
        "completion_percent": 100 if cint(operation.planned_meals) and cint(operation.received_meals) >= cint(operation.planned_meals) else operation.completion_percent,
    }
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    return {"operation": operation.name, "recipient": recipient.strip(), "sent_at": timestamp}
