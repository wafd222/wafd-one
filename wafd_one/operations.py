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
    roles = set(frappe.get_roles())
    if "WAFD Quality Inspector" in roles:
        batch.check_permission("read")
    else:
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
    values = {
        "project": batch.project,
        "production_batch": batch.name,
        "meal_plan": batch.meal_plan,
        "packaging_date": batch.batch_date or nowdate(),
        "planned_quantity": quantity,
        "packed_quantity": packed,
        "rejected_quantity": max(quantity - packed, 0),
        "box_count": cint(batch.box_count),
        "units_per_box": cint(batch.units_per_box),
        "supervisor": batch.packaging_supervisor or frappe.session.user,
        "status": "مخطط / Planned",
    }
    # Quality approval is a hand-off, not permission to operate packaging.
    # Create the next-stage record server-side, then return it read-only to the inspector.
    if "WAFD Quality Inspector" in roles:
        doc = frappe.get_doc({"doctype": "WAFD Packaging Record", **values})
        doc.insert(ignore_permissions=True)
        return {"name": doc.name, "created": True}
    return {"created": True, "values": values}


@frappe.whitelist()
def create_loading_record(packaging_name):
    packaging = frappe.get_doc("WAFD Packaging Record", packaging_name)
    packaging.check_permission("write")

    # Repair legacy records whose quantities are complete but status stayed Planned.
    original_status = packaging.status
    packaging._validate_quantities()
    packaging._derive_status()
    if packaging.status != original_status:
        packaging.save()

    if packaging.status not in ("مكتمل / Completed", "جاهز للتحميل / Ready for Loading"):
        frappe.throw("يجب إكمال سجل التغليف والتحقق من الملصقات أولاً / Complete packaging and verify box labels first")
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
            "hot_cabinet_count": cint(packaging.hot_cabinet_count),
            "hot_cabinet_sandwich_total": cint(packaging.hot_cabinet_sandwich_total),
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
    if not loading.loading_photo:
        frappe.throw("صورة التحميل مطلوبة قبل إنشاء الرحلة / Loading photo is required before creating the trip")
    if not loading.supervisor:
        frappe.throw("يجب تسجيل مشرف التحميل قبل إنشاء الرحلة / Loading supervisor must be recorded")
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


def refresh_operational_statuses():
    """Refresh delay indicators without requiring users to open each document."""
    current = now_datetime()

    batches = frappe.get_all(
        "WAFD Production Batch",
        filters={
            "status": ["not in", ["جاهز / Ready", "مكتمل / Completed", "موقوف / Stopped"]],
            "service_deadline": ["is", "set"],
        },
        fields=["name", "service_deadline"],
    )
    delayed_batches = 0
    for row in batches:
        if row.service_deadline and frappe.utils.get_datetime(row.service_deadline) < current:
            frappe.db.set_value(
                "WAFD Production Batch", row.name, "schedule_status", "متأخر / Delayed", update_modified=False
            )
            delayed_batches += 1

    trips = frappe.get_all(
        "WAFD Delivery Trip",
        filters={
            "status": ["in", ["مخططة / Planned", "تم التحميل / Loaded", "في الطريق / In Transit"]],
            "planned_arrival": ["is", "set"],
        },
        fields=["name", "planned_arrival"],
    )
    delayed_trips = 0
    for row in trips:
        if row.planned_arrival and frappe.utils.get_datetime(row.planned_arrival) < current:
            planned_arrival = frappe.utils.get_datetime(row.planned_arrival)
            minutes = max(int((current - planned_arrival).total_seconds() // 60), 0)
            frappe.db.set_value(
                "WAFD Delivery Trip",
                row.name,
                {
                    "status": "متأخرة / Delayed",
                    "delay_reason": "تجاوز وقت الوصول المخطط تلقائياً / Planned arrival time exceeded automatically",
                    "delay_minutes": minutes,
                    "on_time_status": "متأخر / Delayed",
                },
                update_modified=False,
            )
            delayed_trips += 1

    return {"delayed_batches": delayed_batches, "delayed_trips": delayed_trips}


@frappe.whitelist()
def get_operations_dashboard(project_name=None):
    """Return lightweight live KPIs for operations managers."""
    filters = {"project": project_name} if project_name else {}
    result = {
        "meal_plans": frappe.db.count("WAFD Meal Plan", filters),
        "production_batches": frappe.db.count("WAFD Production Batch", filters),
        "packaging_records": frappe.db.count("WAFD Packaging Record", filters),
        "loading_records": frappe.db.count("WAFD Loading Record", filters),
        "delivery_trips": frappe.db.count("WAFD Delivery Trip", filters),
        "delivery_proofs": frappe.db.count("WAFD Delivery Proof", filters),
    }
    result["delayed_production"] = frappe.db.count(
        "WAFD Production Batch", {**filters, "schedule_status": "متأخر / Delayed"}
    )
    result["at_risk_production"] = frappe.db.count(
        "WAFD Production Batch", {**filters, "schedule_status": "معرض للتأخير / At Risk"}
    )
    result["delayed_trips"] = frappe.db.count(
        "WAFD Delivery Trip", {**filters, "status": "متأخرة / Delayed"}
    )
    delivered = frappe.db.sql(
        """select coalesce(sum(received_quantity),0), coalesce(sum(rejected_quantity),0)
        from `tabWAFD Delivery Proof` where (%s is null or project=%s)""",
        (project_name, project_name),
    )[0]
    result["accepted_quantity"] = cint(delivered[0])
    result["rejected_quantity"] = cint(delivered[1])
    total = result["accepted_quantity"] + result["rejected_quantity"]
    result["acceptance_percent"] = (result["accepted_quantity"] / total * 100) if total else 0
    return result

@frappe.whitelist()
def get_next_operational_action(project_name):
    """Return the first incomplete step in the end-to-end project workflow.

    This is intentionally read-only. It never approves quality, dispatches a
    vehicle, accepts a delivery, invoices, or confirms a payment on behalf of
    the user. It only identifies and opens the next document requiring review.
    """
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("read")

    daily = frappe.db.get_value(
        "WAFD Daily Meal Plan", {"project": project.name},
        ["name", "status", "service_date"], as_dict=True,
        order_by="service_date asc, creation asc",
    )
    if not daily:
        return {
            "step": "daily_plan", "label": "إنشاء الخطط اليومية / Generate Daily Plans",
            "method": "wafd_one.daily_planning.generate_daily_plans",
            "method_args": {"project_name": project.name},
            "route": ["List", "WAFD Daily Meal Plan", {"project": project.name}],
        }

    batch = frappe.db.get_value(
        "WAFD Production Batch", {"project": project.name},
        ["name", "status", "quality_status", "produced_quantity", "planned_quantity"],
        as_dict=True, order_by="batch_date asc, creation asc",
    )
    if not batch:
        return {
            "step": "production", "label": "إنشاء دفعات الإنتاج / Create Production Batches",
            "doctype": "WAFD Daily Meal Plan", "name": daily.name,
            "route": ["Form", "WAFD Daily Meal Plan", daily.name],
        }

    incomplete_batch = frappe.db.get_value(
        "WAFD Production Batch",
        {"project": project.name, "status": ["not in", ["جاهز / Ready", "مكتمل / Completed"]]},
        ["name", "status", "quality_status"], as_dict=True,
        order_by="batch_date asc, creation asc",
    )
    if incomplete_batch:
        return {
            "step": "production", "label": "متابعة الإنتاج والجودة / Continue Production & Quality",
            "doctype": "WAFD Production Batch", "name": incomplete_batch.name,
            "route": ["Form", "WAFD Production Batch", incomplete_batch.name],
        }

    packaging = frappe.db.get_value(
        "WAFD Packaging Record", {"project": project.name, "status": ["!=", "مكتمل / Completed"]},
        ["name", "status"], as_dict=True, order_by="packaging_date asc, creation asc",
    )
    if packaging:
        return {
            "step": "packaging", "label": "استكمال التغليف / Complete Packaging",
            "doctype": "WAFD Packaging Record", "name": packaging.name,
            "route": ["Form", "WAFD Packaging Record", packaging.name],
        }

    batch_without_packaging = frappe.db.sql(
        """select pb.name from `tabWAFD Production Batch` pb
           left join `tabWAFD Packaging Record` pr on pr.production_batch=pb.name
           where pb.project=%s and pb.quality_status='ناجح / Passed' and pr.name is null
           order by pb.batch_date asc, pb.creation asc limit 1""",
        (project.name,), as_dict=True,
    )
    if batch_without_packaging:
        name = batch_without_packaging[0].name
        return {
            "step": "packaging", "label": "إنشاء سجل التغليف / Create Packaging Record",
            "doctype": "WAFD Production Batch", "name": name,
            "route": ["Form", "WAFD Production Batch", name],
        }

    loading = frappe.db.get_value(
        "WAFD Loading Record", {"project": project.name, "status": ["!=", "خرجت / Dispatched"]},
        ["name", "status"], as_dict=True, order_by="loading_date asc, creation asc",
    )
    if loading:
        return {
            "step": "loading", "label": "استكمال التحميل / Complete Loading",
            "doctype": "WAFD Loading Record", "name": loading.name,
            "route": ["Form", "WAFD Loading Record", loading.name],
        }

    packaging_without_loading = frappe.db.sql(
        """select pr.name from `tabWAFD Packaging Record` pr
           left join `tabWAFD Loading Record` lr on lr.packaging_record=pr.name
           where pr.project=%s and pr.status='مكتمل / Completed' and lr.name is null
           order by pr.packaging_date asc, pr.creation asc limit 1""",
        (project.name,), as_dict=True,
    )
    if packaging_without_loading:
        name = packaging_without_loading[0].name
        return {
            "step": "loading", "label": "إنشاء سجل التحميل / Create Loading Record",
            "doctype": "WAFD Packaging Record", "name": name,
            "route": ["Form", "WAFD Packaging Record", name],
        }

    trip = frappe.db.get_value(
        "WAFD Delivery Trip",
        {"project": project.name, "status": ["not in", ["تم التسليم / Delivered", "ملغية / Cancelled"]]},
        ["name", "status"], as_dict=True, order_by="trip_date asc, creation asc",
    )
    if trip:
        return {
            "step": "delivery", "label": "متابعة رحلة التوصيل / Continue Delivery Trip",
            "doctype": "WAFD Delivery Trip", "name": trip.name,
            "route": ["Form", "WAFD Delivery Trip", trip.name],
        }

    loading_without_trip = frappe.db.sql(
        """select lr.name from `tabWAFD Loading Record` lr
           left join `tabWAFD Delivery Trip` dt on dt.loading_record=lr.name and dt.status!='ملغية / Cancelled'
           where lr.project=%s and lr.status in ('تم التحميل / Loaded','خرجت / Dispatched') and dt.name is null
           order by lr.loading_date asc, lr.creation asc limit 1""",
        (project.name,), as_dict=True,
    )
    if loading_without_trip:
        name = loading_without_trip[0].name
        return {
            "step": "delivery", "label": "إنشاء رحلة التوصيل / Create Delivery Trip",
            "doctype": "WAFD Loading Record", "name": name,
            "route": ["Form", "WAFD Loading Record", name],
        }

    trip_without_proof = frappe.db.sql(
        """select dt.name from `tabWAFD Delivery Trip` dt
           left join `tabWAFD Delivery Proof` dp on dp.delivery_trip=dt.name
           where dt.project=%s and dt.status in ('وصلت / Arrived','متأخرة / Delayed','في الطريق / In Transit')
             and dp.name is null
           order by dt.trip_date asc, dt.creation asc limit 1""",
        (project.name,), as_dict=True,
    )
    if trip_without_proof:
        name = trip_without_proof[0].name
        return {
            "step": "proof", "label": "إثبات التسليم / Record Delivery Proof",
            "doctype": "WAFD Delivery Trip", "name": name,
            "route": ["Form", "WAFD Delivery Trip", name],
        }

    from wafd_one.finance import get_uninvoiced_delivery_items
    billable = get_uninvoiced_delivery_items(project.name)
    if billable:
        return {
            "step": "invoice", "label": "إنشاء فاتورة من التسليم / Create Delivery Invoice",
            "method": "wafd_one.finance.create_invoice_from_deliveries",
            "method_args": {"project_name": project.name},
        }

    invoice = frappe.db.get_value(
        "WAFD Invoice", {"project": project.name, "status": ["not in", ["مدفوعة / Paid", "ملغاة / Cancelled"]]},
        ["name", "status", "balance"], as_dict=True, order_by="invoice_date asc, creation asc",
    )
    if invoice:
        return {
            "step": "payment", "label": "تسجيل التحصيل / Register Payment",
            "doctype": "WAFD Invoice", "name": invoice.name,
            "route": ["Form", "WAFD Invoice", invoice.name],
        }

    return {
        "step": "complete", "label": "الدورة مكتملة / Workflow Complete",
        "route": ["Form", "WAFD Catering Project", project.name],
    }


@frappe.whitelist()
def create_delivery_note(trip_name):
    trip = frappe.get_doc("WAFD Delivery Trip", trip_name)
    trip.check_permission("write")
    if trip.status not in ("وصلت / Arrived", "تم التسليم / Delivered"):
        frappe.throw("يجب وصول الرحلة أو تسجيل التسليم أولاً / Trip must arrive before creating the delivery note")
    existing = frappe.db.get_value("WAFD Delivery Note", {"delivery_trip": trip.name}, "name")
    if existing:
        return {"name": existing, "created": False}
    loading = frappe.get_doc("WAFD Loading Record", trip.loading_record) if trip.loading_record else None
    return {"created": True, "values": {
        "delivery_trip": trip.name, "project": trip.project, "meal_plan": trip.meal_plan,
        "loading_record": trip.loading_record, "hotel": trip.hotel, "vehicle": trip.vehicle,
        "driver": trip.driver, "delivery_time": trip.actual_arrival or now_datetime(),
        "delivered_quantity": trip.quantity, "box_count": cint(loading.box_count) if loading else 0,
        "hot_cabinet_count": cint(getattr(loading, "hot_cabinet_count", 0)) if loading else 0,
        "status": "تم التسليم / Delivered"}}

@frappe.whitelist()
def create_receiving_note(delivery_note_name):
    note = frappe.get_doc("WAFD Delivery Note", delivery_note_name)
    note.check_permission("write")
    if note.status != "تم التسليم / Delivered":
        frappe.throw("يجب اعتماد سند التسليم أولاً / Delivery note must be marked delivered first")
    if cint(note.delivered_quantity) <= 0:
        frappe.throw("الكمية المسلمة يجب أن تكون أكبر من صفر / Delivered quantity must be greater than zero")
    existing = frappe.db.get_value("WAFD Receiving Note", {"delivery_note": note.name}, "name")
    if existing:
        return {"name": existing, "created": False}
    return {"created": True, "values": {
        "delivery_trip": note.delivery_trip, "delivery_note": note.name, "project": note.project,
        "meal_plan": note.meal_plan, "loading_record": note.loading_record, "hotel": note.hotel,
        "vehicle": note.vehicle, "driver": note.driver, "receipt_time": now_datetime(),
        "delivered_quantity": note.delivered_quantity, "received_quantity": note.delivered_quantity,
        "rejected_quantity": 0, "receiver_name": note.receiver_name,
        "receiver_title": note.receiver_title, "status": "مسودة / Draft"}}

@frappe.whitelist()
def get_batch_workflow_state(batch_name):
    """Return the furthest persisted operational stage for a production batch.

    This is deliberately derived from linked documents rather than stale status fields,
    so old/closed projects cannot accidentally recreate an earlier workflow stage.
    """
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("read")
    packaging = frappe.db.get_value("WAFD Packaging Record", {"production_batch": batch.name}, ["name", "status"], as_dict=True)
    loading = frappe.db.get_value("WAFD Loading Record", {"production_batch": batch.name}, ["name", "status"], as_dict=True)
    trip = None
    proof = None
    if loading:
        trip = frappe.db.get_value("WAFD Delivery Trip", {"loading_record": loading.name, "status": ["!=", "ملغية / Cancelled"]}, ["name", "status"], as_dict=True)
    if trip:
        proof = frappe.db.get_value("WAFD Delivery Proof", {"delivery_trip": trip.name}, "name")
    stage = "production"
    if packaging: stage = "packaging"
    if loading: stage = "loading"
    if trip: stage = "delivery"
    if proof or (trip and trip.status == "تم التسليم / Delivered"): stage = "delivered"
    return {"stage": stage, "packaging": packaging, "loading": loading, "trip": trip, "proof": proof}


def assert_batch_not_past(batch_name, allowed_stage="production"):
    """Block destructive/repeating actions when a later stage already exists."""
    state = get_batch_workflow_state(batch_name)
    rank = {"production": 0, "packaging": 1, "loading": 2, "delivery": 3, "delivered": 4}
    if rank.get(state["stage"], 0) > rank.get(allowed_stage, 0):
        frappe.throw(
            "هذه الدفعة انتقلت بالفعل إلى مرحلة لاحقة؛ تم منع تكرار العملية لحماية المخزون والبيانات "
            "/ This batch has already progressed to a later stage; duplicate processing was blocked"
        )
    return state
