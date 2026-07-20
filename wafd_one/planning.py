import hashlib

import frappe
from frappe.utils import add_to_date, cint, flt, get_datetime, now_datetime, nowdate


def _settings():
    defaults = {
        "daily_production_capacity": 10000,
        "capacity_warning_percent": 85,
        "enforce_capacity_limit": 0,
        "default_production_lead_hours": 8,
        "shortage_warning_hours": 24,
        "auto_generate_alerts": 1,
    }
    try:
        doc = frappe.get_single("WAFD Operations Settings")
    except Exception:
        return frappe._dict(defaults)
    for key, value in defaults.items():
        if doc.get(key) is None:
            doc.set(key, value)
    return doc


def get_daily_capacity(service_date, exclude_meal_plan=None):
    filters = {"service_date": service_date, "status": ["!=", "ملغي / Cancelled"]}
    plans = frappe.get_all("WAFD Meal Plan", filters=filters, fields=["name", "quantity"])
    planned = sum(cint(row.quantity) for row in plans if row.name != exclude_meal_plan)
    settings = _settings()
    capacity = cint(settings.daily_production_capacity)
    utilization = (flt(planned) / flt(capacity) * 100) if capacity else 0
    return frappe._dict({"planned_quantity": planned, "capacity": capacity, "utilization_percent": utilization})


def validate_meal_plan_capacity(doc):
    if not doc.service_date or doc.status == "ملغي / Cancelled":
        return
    data = get_daily_capacity(doc.service_date, doc.name)
    total = cint(data.planned_quantity) + cint(doc.quantity)
    capacity = cint(data.capacity)
    doc.daily_planned_quantity = total
    doc.capacity_utilization_percent = (flt(total) / flt(capacity) * 100) if capacity else 0
    settings = _settings()
    if capacity and total > capacity and cint(settings.enforce_capacity_limit):
        frappe.throw(
            f"الطاقة الإنتاجية اليومية ستتجاوز الحد ({total} من {capacity}) / Daily capacity would be exceeded ({total} of {capacity})"
        )


def _alert_key(alert_type, reference_doctype, reference_name, suffix=""):
    raw = "|".join([alert_type or "", reference_doctype or "", reference_name or "", suffix or ""])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def upsert_alert(alert_type, severity, message, project=None, reference_doctype=None, reference_name=None, recommended_action=None, suffix=""):
    key = _alert_key(alert_type, reference_doctype, reference_name, suffix)
    existing = frappe.db.get_value("WAFD Operations Alert", {"deduplication_key": key}, "name")
    values = {
        "alert_type": alert_type, "severity": severity, "status": "مفتوح / Open",
        "alert_date": now_datetime(), "project": project, "reference_doctype": reference_doctype,
        "reference_name": reference_name, "message": message,
        "recommended_action": recommended_action, "deduplication_key": key,
    }
    if existing:
        doc = frappe.get_doc("WAFD Operations Alert", existing)
        if doc.status != "مغلق / Closed":
            doc.update(values)
            doc.save(ignore_permissions=True)
        return doc.name
    doc = frappe.get_doc({"doctype": "WAFD Operations Alert", **values})
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def refresh_operations_alerts(project=None, service_date=None):
    settings = _settings()
    if not cint(settings.auto_generate_alerts):
        return {"created_or_updated": 0, "alerts": []}
    service_date = service_date or nowdate()
    alerts = []
    capacity = get_daily_capacity(service_date)
    warning_at = flt(settings.capacity_warning_percent)
    if capacity.capacity and capacity.utilization_percent >= warning_at:
        exceeded = capacity.utilization_percent > 100
        alerts.append(upsert_alert(
            "تجاوز الطاقة / Capacity Exceeded" if exceeded else "اقتراب الطاقة / Capacity Warning",
            "حرج / Critical" if exceeded else "مرتفع / High",
            f"إجمالي الوجبات المخططة {capacity.planned_quantity} والطاقة {capacity.capacity} ({capacity.utilization_percent:.1f}%).",
            reference_doctype="WAFD Operations Settings", reference_name="WAFD Operations Settings",
            recommended_action="إعادة توزيع الإنتاج أو زيادة الطاقة قبل اعتماد الخطط.", suffix=str(service_date),
        ))
    batch_filters = {"batch_date": service_date}
    if project:
        batch_filters["project"] = project
    for row in frappe.get_all("WAFD Production Batch", filters=batch_filters, fields=["name","project","materials_status","quality_status","status","planned_quantity","produced_quantity"]):
        if row.materials_status == "عجز / Shortage":
            alerts.append(upsert_alert("عجز مخزون / Stock Shortage", "حرج / Critical", "دفعة الإنتاج تحتوي على عجز في المواد.", row.project, "WAFD Production Batch", row.name, "استكمال التوريد أو نقل المخزون قبل بدء الإنتاج."))
        if row.quality_status == "مرفوض / Rejected":
            alerts.append(upsert_alert("فشل جودة / Quality Failure", "حرج / Critical", "تم رفض فحص جودة دفعة الإنتاج.", row.project, "WAFD Production Batch", row.name, "تنفيذ الإجراء التصحيحي وإعادة الفحص قبل التغليف."))
        if row.status not in ("جاهز / Ready", "مكتمل / Completed") and cint(row.produced_quantity) < cint(row.planned_quantity) and str(service_date) < str(nowdate()):
            alerts.append(upsert_alert("تأخر إنتاج / Production Delay", "مرتفع / High", "دفعة الإنتاج لم تكتمل في تاريخها المخطط.", row.project, "WAFD Production Batch", row.name, "تحديد سبب التأخير وخطة التعويض."))
    return {"created_or_updated": len(set(alerts)), "alerts": list(dict.fromkeys(alerts))}


@frappe.whitelist()
def build_project_operations_plan(project_name):
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("write")
    created = []
    existing = []
    skipped = []
    for plan_name in frappe.get_all("WAFD Meal Plan", filters={"project": project.name, "status": ["in", ["مسودة / Draft", "معتمد / Approved"]]}, pluck="name"):
        plan = frappe.get_doc("WAFD Meal Plan", plan_name)
        if not plan.recipe:
            skipped.append({"meal_plan": plan.name, "reason": "missing_recipe"})
            continue
        batch_name = frappe.db.get_value("WAFD Production Batch", {"meal_plan": plan.name}, "name")
        if batch_name:
            existing.append(batch_name)
            continue
        batch = frappe.get_doc({
            "doctype": "WAFD Production Batch", "project": plan.project, "meal_plan": plan.name,
            "recipe": plan.recipe, "batch_date": plan.service_date, "planned_quantity": plan.quantity,
            "source_warehouse": project.default_warehouse, "status": "مخطط / Planned",
        })
        batch.insert()
        plan.db_set("status", "معتمد / Approved", update_modified=False)
        created.append(batch.name)
    alert_result = refresh_operations_alerts(project=project.name)
    return {"created_batches": created, "existing_batches": existing, "skipped": skipped, "alerts": alert_result}


@frappe.whitelist()
def get_daily_operations_control(service_date=None, project=None):
    service_date = service_date or nowdate()
    plan_filters = {"service_date": service_date, "status": ["!=", "ملغي / Cancelled"]}
    batch_filters = {"batch_date": service_date}
    trip_filters = {"trip_date": service_date}
    if project:
        plan_filters["project"] = project
        batch_filters["project"] = project
        trip_filters["project"] = project
    plans = frappe.get_all("WAFD Meal Plan", filters=plan_filters, fields=["quantity","status"])
    batches = frappe.get_all("WAFD Production Batch", filters=batch_filters, fields=["planned_quantity","produced_quantity","packed_quantity","rejected_quantity","materials_status","quality_status","status"])
    trips = frappe.get_all("WAFD Delivery Trip", filters=trip_filters, fields=["quantity","status"])
    capacity = get_daily_capacity(service_date)
    return {
        "service_date": service_date,
        "meal_plans": len(plans),
        "planned_meals": sum(cint(x.quantity) for x in plans),
        "production_batches": len(batches),
        "produced_meals": sum(cint(x.produced_quantity) for x in batches),
        "packed_meals": sum(cint(x.packed_quantity) for x in batches),
        "rejected_meals": sum(cint(x.rejected_quantity) for x in batches),
        "material_shortages": sum(1 for x in batches if x.materials_status == "عجز / Shortage"),
        "quality_failures": sum(1 for x in batches if x.quality_status == "مرفوض / Rejected"),
        "delivery_trips": len(trips),
        "delivered_meals": sum(cint(x.quantity) for x in trips if x.status == "تم التسليم / Delivered"),
        "delayed_trips": sum(1 for x in trips if x.status == "متأخرة / Delayed"),
        "daily_capacity": capacity.capacity,
        "capacity_utilization_percent": capacity.utilization_percent,
        "open_alerts": frappe.db.count("WAFD Operations Alert", {"status": ["!=", "مغلق / Closed"], **({"project": project} if project else {})}),
    }
