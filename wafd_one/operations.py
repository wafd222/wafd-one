import frappe
from frappe.utils import cint, now_datetime, nowdate


def _get_or_create(doctype, filters, values):
    existing = frappe.db.get_value(doctype, filters, "name")
    if existing:
        return {"name": existing, "created": False}
    doc = frappe.get_doc({"doctype": doctype, **values})
    doc.insert()
    return {"name": doc.name, "created": True}


@frappe.whitelist()
def create_packaging_record(batch_name):
    """Open a correctly populated packaging draft, or return the existing record."""
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("write")
    if batch.quality_status != "ناجح / Passed":
        frappe.throw("يجب نجاح فحص الجودة قبل إنشاء سجل التغليف / Quality inspection must pass first")

    quantity = cint(batch.produced_quantity) or cint(batch.planned_quantity)
    if quantity <= 0:
        frappe.throw("أدخل الكمية المنتجة قبل إنشاء سجل التغليف / Enter produced quantity before packaging")

    existing = frappe.db.get_value(
        "WAFD Packaging Record", {"production_batch": batch.name}, "name"
    )
    if existing:
        return {"name": existing, "created": False}

    packed = cint(batch.packed_quantity) or quantity
    return {
        "created": True,
        "values": {
            "project": batch.project,
            "production_batch": batch.name,
            "meal_plan": batch.meal_plan,
            "packaging_date": batch.batch_date or nowdate(),
            "planned_quantity": quantity,
            "packed_quantity": packed,
            "rejected_quantity": max(quantity - packed, 0),
            "box_count": cint(batch.box_count),
            "units_per_box": cint(batch.units_per_box),
            "supervisor": batch.packaging_supervisor,
            "status": "مخطط / Planned",
        },
    }


@frappe.whitelist()
def create_loading_record(packaging_name):
    packaging = frappe.get_doc("WAFD Packaging Record", packaging_name)
    packaging.check_permission("write")
    if packaging.status != "مكتمل / Completed":
        frappe.throw("يجب إكمال سجل التغليف أولاً / Complete the packaging record first")
    if cint(packaging.packed_quantity) <= 0:
        frappe.throw("الكمية المغلفة يجب أن تكون أكبر من صفر / Packed quantity must be greater than zero")
    plan = frappe.get_doc("WAFD Meal Plan", packaging.meal_plan)
    project = frappe.get_doc("WAFD Catering Project", packaging.project)
    existing = frappe.db.get_value(
        "WAFD Loading Record", {"packaging_record": packaging.name}, "name"
    )
    if existing:
        return {"name": existing, "created": False}

    # Vehicle and driver are mandatory on the loading record. They may not be
    # configured as project defaults, so open a populated draft for the user
    # instead of trying to insert an incomplete document.
    return {
        "created": True,
        "values": {
            "project": packaging.project,
            "meal_plan": packaging.meal_plan,
            "production_batch": packaging.production_batch,
            "packaging_record": packaging.name,
            "hotel": plan.hotel,
            "loading_date": now_datetime(),
            "quantity": packaging.packed_quantity,
            "box_count": packaging.box_count,
            "vehicle": project.default_vehicle,
            "driver": project.default_driver,
            "status": "قيد التحميل / Loading",
        },
    }


@frappe.whitelist()
def create_delivery_trip(loading_name):
    loading = frappe.get_doc("WAFD Loading Record", loading_name)
    loading.check_permission("write")
    if loading.status not in ("تم التحميل / Loaded", "خرجت / Dispatched"):
        frappe.throw("يجب اعتماد التحميل قبل إنشاء رحلة التوصيل / Loading must be completed first")
    if not loading.vehicle or not loading.driver:
        frappe.throw("حدد المركبة والسائق / Select vehicle and driver")
    plan = frappe.get_doc("WAFD Meal Plan", loading.meal_plan)
    return _get_or_create(
        "WAFD Delivery Trip",
        {"loading_record": loading.name},
        {
            "project": loading.project,
            "meal_plan": loading.meal_plan,
            "loading_record": loading.name,
            "trip_date": plan.service_date,
            "vehicle": loading.vehicle,
            "driver": loading.driver,
            "hotel": loading.hotel or plan.hotel,
            "quantity": loading.quantity,
            "actual_departure": loading.dispatch_time,
            "status": "تم التحميل / Loaded",
        },
    )


@frappe.whitelist()
def create_delivery_proof(trip_name):
    """Return safe defaults for a new proof, or the existing proof name.

    Delivery proof requires receiver data, photo and signature, so it must be
    completed interactively instead of being inserted as an incomplete record.
    """
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    trip.check_permission("write")
    if trip.status not in ("في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed"):
        frappe.throw("يجب بدء الرحلة أو تسجيل الوصول أولاً / Start the trip or mark arrival first")

    existing = frappe.db.get_value("WAFD Delivery Proof", {"delivery_trip": trip.name}, "name")
    if existing:
        return {"name": existing, "created": False}

    return {
        "created": True,
        "values": {
            "delivery_trip": trip.name,
            "project": trip.project,
            "meal_plan": trip.meal_plan,
            "hotel": trip.hotel,
            "delivery_time": now_datetime(),
            "received_quantity": trip.quantity,
            "rejected_quantity": 0,
            "status": "مقبول بالكامل / Fully Accepted",
        },
    }


@frappe.whitelist()
def set_trip_status(trip_name, status):
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    trip.check_permission("write")
    allowed = {
        "في الطريق / In Transit",
        "وصلت / Arrived",
        "متأخرة / Delayed",
    }
    if status not in allowed:
        frappe.throw("حالة الرحلة غير مسموحة / Invalid trip status")
    if status == "في الطريق / In Transit" and not trip.actual_departure:
        trip.actual_departure = now_datetime()
    if status == "وصلت / Arrived" and not trip.actual_arrival:
        trip.actual_arrival = now_datetime()
    trip.status = status
    trip.save()
    return {"name": trip.name, "status": trip.status}


@frappe.whitelist()
def get_project_operations_summary(project_name):
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("read")
    counts = {}
    mappings = {
        "meal_plans": "WAFD Meal Plan",
        "production_batches": "WAFD Production Batch",
        "packaging_records": "WAFD Packaging Record",
        "loading_records": "WAFD Loading Record",
        "delivery_trips": "WAFD Delivery Trip",
        "delivery_proofs": "WAFD Delivery Proof",
        "invoices": "WAFD Invoice",
    }
    for key, doctype in mappings.items():
        counts[key] = frappe.db.count(doctype, {"project": project.name})
    counts["delivered_meals"] = cint(project.delivered_meals)
    counts["remaining_meals"] = cint(project.remaining_meals)
    counts["progress_percent"] = project.progress_percent or 0
    return counts
