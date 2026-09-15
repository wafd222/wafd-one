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


def _roles():
    return set(frappe.get_roles(frappe.session.user))


def _require(*allowed):
    if not (_roles() & set(allowed)):
        frappe.throw(_("غير مصرح بهذه المهمة / Not permitted for this task"), frappe.PermissionError)


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
        fields=["name", "driver", "vehicle", "destination_name", "destination_map_url", "quantity", "planned_arrival", "actual_departure", "actual_arrival", "status"],
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
    filters = {"docstatus": 1, "status": ["not in", ["مغلق / Closed", "ملغي / Cancelled"]]}
    if roles & GLOBAL_MANAGEMENT_ROLES:
        return filters
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
        fields=["name", "project_title", "season_type", "distribution_site", "contracting_entity", "start_date", "end_date", "daily_meals", "total_meals", "status", "project_manager_user", "kitchen_supervisor_user", "delivery_supervisor_user", "site_manager_user"],
        order_by="start_date desc", limit_page_length=200,
    )
    project_names = [row.name for row in projects]
    operations = frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": ["in", project_names], "operation_date": target_date, "docstatus": ["<", 2]} if project_names else {"name": "__none__"},
        fields=["name", "project", "operation_date", "status", "planned_meals", "produced_meals", "packaged_meals", "loaded_meals", "delivered_meals", "received_meals", "completion_percent", "kitchen_ready_meals", "kitchen_ready_approved", "kitchen_shortage_reported", "kitchen_shortage_notes", "authority_inspection_approved", "delivery_trip_count", "delivery_scheduled_meals", "delivery_verified_meals", "delivery_proof_count", "delivery_last_arrival", "site_received_meals", "site_receipt_approved", "site_receipt_time", "site_received_by"],
        order_by="project asc", limit_page_length=500,
    )
    project_map = {row.name: row for row in projects}
    for operation in operations:
        meta = project_map.get(operation.project) or {}
        operation["project_title"] = meta.get("project_title") or operation.project
        operation["distribution_site"] = meta.get("distribution_site") or ""
        operation["cartons"] = (cint(operation.planned_meals) + 24) // 25
        operation["deliveries"] = _delivery_rows(operation)

    report_filters = {"operation_date": target_date}
    if project_names:
        report_filters["project"] = ["in", project_names]
    else:
        report_filters["name"] = "__none__"
    if "WAFD Iftar Supervisor" in roles and not (roles & MANAGEMENT_ROLES):
        report_filters["supervisor_user"] = frappe.session.user
    reports = frappe.get_list(
        "WAFD Iftar Supervisor Daily Report", filters=report_filters,
        fields=["name", "project", "daily_operation", "supervisor_name", "supervisor_user", "planned_meals", "cartons", "received_meals", "distributed_meals", "surplus_meals", "preservation_meals", "waste_meals", "report_submitted", "manager_approved", "submitted_at", "approved_at"],
        order_by="supervisor_name asc", limit_page_length=1000,
    )
    return {
        "date": target_date, "roles": sorted(roles & TEAM_ROLES), "projects": projects,
        "operations": operations, "reports": reports,
        "mode": (
            "management" if roles & MANAGEMENT_ROLES else
            "kitchen" if roles & {"WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor"} else
            "delivery" if "WAFD Delivery Supervisor" in roles else
            "site" if "WAFD Iftar Site Manager" in roles else "supervisor"
        ),
    }


@frappe.whitelist()
def update_kitchen(operation_name, ready_meals, shortage_reported=0, shortage_notes=None, approve=0):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "kitchen_supervisor_user")
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
        "kitchen_shortage_reported": shortage, "kitchen_shortage_notes": (shortage_notes or "").strip(),
        "produced_meals": ready,
    }
    if cint(approve):
        values["packaged_meals"] = ready
        values["status"] = "جاهز للتحميل / Ready to Load"
    frappe.db.set_value("WAFD Iftar Daily Operation", operation.name, values, update_modified=True)
    return values


@frappe.whitelist()
def approve_site_receipt(operation_name, received_meals):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "site_manager_user")
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
def ensure_supervisor_reports(operation_name):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    operation, project = _submitted_operation(operation_name)
    _assigned(project, "site_manager_user")
    created, skipped = [], []
    plans = frappe.get_all("WAFD Iftar Supervisor Plan", filters={"project": project.name}, pluck="name", order_by="creation asc", limit_page_length=500)
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
    return {"created": created, "skipped_without_user": skipped, "total_plans": len(plans)}


@frappe.whitelist()
def receive_for_supervisor(report_name, received_meals, tablecloths=0, bread_bags=0, waste_bags=0, gloves=0, shoe_covers=0):
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
    report = frappe.get_doc("WAFD Iftar Supervisor Daily Report", report_name)
    project = frappe.get_doc("WAFD Iftar Project", report.project)
    _assigned(project, "site_manager_user")
    operation = frappe.get_doc("WAFD Iftar Daily Operation", report.daily_operation)
    if not cint(operation.site_receipt_approved):
        frappe.throw(_("يجب اعتماد استلام مدير الموقع أولاً / Site manager receipt must be approved first"))
    if not cint(operation.authority_inspection_approved):
        frappe.throw(_("يجب اعتماد فحص الجهة قبل تسليم الوجبات للمشرفين / Authority inspection is required before supervisor handover"))
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
    for field in ("tablecloths", "bread_bags", "waste_bags", "gloves", "shoe_covers"):
        report.set(field, cint(locals()[field]))
    report.save(ignore_permissions=True)
    return {"name": report.name, "received_meals": report.received_meals, "received_at": report.received_at}


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
    """Consolidate all approved supervisor reports into the authority daily report."""
    _require("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Iftar Site Manager")
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
        "cleanup_completed": int(all(cint(r.cleanup_completed) for r in reports)), "daily_report_sent": 1,
        "completion_percent": min(100, received / cint(operation.planned_meals) * 100) if cint(operation.planned_meals) else 0,
        "status": "مغلق / Closed" if received >= cint(operation.planned_meals) else "مستلم / Received",
        "notes": ((operation.notes or "") + f"\nالتوزيع الفعلي: {distributed}").strip(),
    }, update_modified=True)
    return {"operation": operation.name, "received": received, "distributed": distributed, "surplus": surplus, "preservation": preservation, "waste": waste}
