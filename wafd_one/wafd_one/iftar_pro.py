from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, nowdate


WIZARD_BASE_PRICE = 9.0
WIZARD_PROPHETS_MOSQUE = "المسجد النبوي الشريف / Prophet’s Mosque"
WIZARD_HARAMAIN_ENTITY = "الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي"
WIZARD_LOCATION_DEFAULTS = {
    WIZARD_PROPHETS_MOSQUE: {
        "distribution_site": "المسجد النبوي الشريف / Prophet’s Mosque",
        "contracting_entity": WIZARD_HARAMAIN_ENTITY,
        "distribution_type": "مسجد أو حرم / Mosque or Haram",
    },
    "مسجد قباء / Quba Mosque": {
        "distribution_site": "مسجد قباء / Quba Mosque",
        "contracting_entity": "هيئة تطوير منطقة المدينة المنورة",
        "distribution_type": "مسجد أو حرم / Mosque or Haram",
    },
    "مسجد القبلتين / Qiblatain Mosque": {
        "distribution_site": "مسجد القبلتين / Qiblatain Mosque",
        "contracting_entity": "هيئة تطوير منطقة المدينة المنورة",
        "distribution_type": "مسجد أو حرم / Mosque or Haram",
    },
    "مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)": {
        "distribution_site": "مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)",
        "contracting_entity": "هيئة تطوير منطقة المدينة المنورة",
        "distribution_type": "مسجد أو حرم / Mosque or Haram",
    },
    "مشروع أو موقع آخر / Other Project or Site": {
        "distribution_site": "",
        "distribution_type": "توزيع خارجي أو جهة / External Distribution or Entity",
    },
}
WIZARD_OPTIONAL_ITEMS = [
    "معمول", "فواكه مجففة", "مكسرات مشكلة", "لوزين",
    "عصير برتقال 200 مل", "عصير تفاح 200 مل",
]


def _ingredient_reference_cost(name):
    """Resolve by document name *or* ingredient_name.

    Wizard labels use Arabic ingredient names while WAFD Ingredient may use an
    autoname/code as its document name.  Looking up only by docname caused some
    add-ons to appear as zero-priced.
    """
    ingredient_id = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": name}, "name") or name
    row = frappe.db.get_value(
        "WAFD Ingredient", ingredient_id,
        ["latest_market_cost", "standard_cost"],
        as_dict=True,
    ) or {}
    return frappe.utils.flt(row.get("latest_market_cost") or row.get("standard_cost") or 0)


@frappe.whitelist()
def get_wizard_defaults():
    """Single server-owned source for wizard defaults and add-on pricing."""
    optional_prices = {name: _ingredient_reference_cost(name) for name in WIZARD_OPTIONAL_ITEMS}
    return {
        "base_price": WIZARD_BASE_PRICE,
        "locations": WIZARD_LOCATION_DEFAULTS,
        "optional_prices": optional_prices,
        "water_reference_price": _ingredient_reference_cost("ماء 330 مل") or 0.62,
        "zamzam_reference_price": _ingredient_reference_cost("ماء زمزم 330 مل") or 1.50,
    }


@frappe.whitelist()
def search_iftar_projects(project=None, table_owner=None, date=None, limit=100):
    """Search report-center projects without silently forcing the latest project."""
    filters = {"docstatus": ["<", 2]}
    if project:
        filters["name"] = project
    if date:
        d = getdate(date)
        filters["start_date"] = ["<=", d]
        filters["end_date"] = [">=", d]

    names = None
    if table_owner:
        # Child-table rows inherit project read access through their parent.
        owner_rows = frappe.get_all(
            "WAFD Iftar Distribution Recipient",
            filters={"table_owner_name": ["like", f"%{table_owner}%"], "parenttype": "WAFD Iftar Project"},
            pluck="parent",
            limit_page_length=max(1, min(cint(limit), 500)),
        )
        operation_projects = frappe.get_all(
            "WAFD Iftar Daily Operation",
            filters={"table_owner_name": ["like", f"%{table_owner}%"], "docstatus": ["<", 2]},
            pluck="project",
            limit_page_length=max(1, min(cint(limit), 500)),
        )
        names = list(dict.fromkeys([x for x in owner_rows + operation_projects if x]))
        if not names:
            return []
        filters["name"] = ["in", names]

    rows = frappe.get_list(
        "WAFD Iftar Project",
        filters=filters,
        fields=["name", "project_title", "distribution_site", "contracting_entity", "start_date", "end_date", "total_meals", "daily_meals", "status", "modified"],
        order_by="start_date desc, modified desc",
        limit_page_length=max(1, min(cint(limit), 500)),
    )
    return rows


@frappe.whitelist()
def create_project(data):
    if isinstance(data, str):
        data = frappe.parse_json(data)
    data = dict(data or {})
    location_default = WIZARD_LOCATION_DEFAULTS.get(data.get("project_title")) or {}
    if location_default.get("distribution_site"):
        data["distribution_site"] = location_default["distribution_site"]
    if location_default.get("contracting_entity"):
        data["contracting_entity"] = location_default["contracting_entity"]
    if location_default.get("distribution_type"):
        data["distribution_type"] = location_default["distribution_type"]
    optional_items_for_price = data.get("optional_items") or []
    if isinstance(optional_items_for_price, str):
        optional_items_for_price = frappe.parse_json(optional_items_for_price)
    optional_costs = {x: _ingredient_reference_cost(x) for x in optional_items_for_price}
    unpriced_optional = [name for name, cost in optional_costs.items() if frappe.utils.flt(cost) <= 0]
    if unpriced_optional:
        frappe.throw(
            _("لا يمكن إنشاء المشروع لأن الإضافات التالية بلا سعر مرجعي: {0} / "
              "Selected add-ons are missing reference prices: {0}").format(", ".join(unpriced_optional))
        )
    calculated_sale_price = WIZARD_BASE_PRICE + sum(optional_costs.values())
    if cint(data.get("include_zamzam")):
        water_cost = _ingredient_reference_cost("ماء 330 مل") or 0.62
        zamzam_cost = _ingredient_reference_cost("ماء زمزم 330 مل") or 1.50
        calculated_sale_price += max(0, zamzam_cost - water_cost)
    # The wizard price is server-owned and fully recomputed from the current selection.
    # Never preserve a stale higher browser value after an add-on is removed.
    data["sale_price_per_meal"] = frappe.utils.flt(calculated_sale_price, precision=2)
    required = [
        "project_title", "contracting_entity", "distribution_site",
        "start_date", "end_date", "daily_meals", "sale_price_per_meal",
    ]
    missing = [field for field in required if not data.get(field)]
    if missing:
        frappe.throw(_("الحقول المطلوبة غير مكتملة: {0}").format(", ".join(missing)))
    allowed = required + [
        "season_type", "contracting_entity_type", "site_details", "meal_template", "include_zamzam", "distribution_type"
    ]
    doc = frappe.get_doc({
        "doctype": "WAFD Iftar Project",
        **{key: value for key, value in data.items() if key in allowed},
    })
    doc.insert()
    optional_items = data.get("optional_items") or []
    if isinstance(optional_items, str):
        optional_items = frappe.parse_json(optional_items)
    if optional_items:
        existing = {r.ingredient for r in (doc.components or [])}
        for item in optional_items:
            name = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": item}, "name")
            if name and name not in existing:
                doc.append("components", {"ingredient": name, "quantity_per_meal": 1, "component_group": "إضافة / Add-on", "is_mandatory": 0})
        doc.save(ignore_permissions=True)
    # Store editable operating-cost agreements entered during creation. Costs are
    # deliberately flexible: quantity + negotiated rate + allocation basis.
    total_meals = cint(doc.total_meals) or (cint(doc.daily_meals) * max(1, cint(doc.number_of_days)))
    cartons = max(1, (total_meals + 24) // 25)
    cost_rows = [
        ("carton_unit_cost", "الكرتون / Carton", cartons, "للوحدة / Per Unit", "تكلفة كرتون سعة 25 وجبة"),
        ("tablecloth_unit_cost", "السفرة / Tablecloth", cint(data.get("tablecloth_count") or 1), "لليوم / Per Day", "تكلفة السفرة اليومية"),
        ("supervisors_manager_rate", "مدير المشرفين / Supervisors Manager", cint(data.get("supervisors_manager_count") or 1), "لليوم / Per Day", "أجر مدير المشرفين"),
        ("supervisors_rate", "المشرفون / Supervisors", cint(data.get("supervisors_count") or 0), "لليوم / Per Day", "أجر المشرفين"),
        ("assistants_rate", "المساعدون / Assistants", cint(data.get("assistants_count") or 0), "لليوم / Per Day", "أجر المساعدين"),
        ("packaging_workers_rate", "عمال التغليف / Packaging Workers", cint(data.get("packaging_workers_count") or 0), "لليوم / Per Day", "أجر عمال التغليف"),
        ("loading_workers_rate", "عمال التحميل / Loading Workers", cint(data.get("loading_workers_count") or 0), "لليوم / Per Day", "أجر عمال التحميل"),
        ("drivers_rate", "السائقون / Drivers", cint(data.get("drivers_count") or 0), "لليوم / Per Day", "أجر السائقين"),
    ]
    for key, cost_type, quantity, basis, description in cost_rows:
        rate = frappe.utils.flt(data.get(key))
        if rate and quantity:
            doc.append("operating_costs", {
                "cost_type": cost_type, "description": description,
                "quantity": quantity, "rate": rate, "allocation_basis": basis,
                "cost_basis": "تقديري / Estimated",
            })
    other_rate = frappe.utils.flt(data.get("other_cost_rate"))
    if other_rate:
        doc.append("operating_costs", {
            "cost_type": "أخرى / Other",
            "description": data.get("other_cost_description") or "تكلفة إضافية",
            "quantity": frappe.utils.flt(data.get("other_cost_quantity") or 1),
            "rate": other_rate,
            "allocation_basis": data.get("other_cost_basis") or "للمشروع / Per Project",
            "cost_basis": "تقديري / Estimated",
        })
    if doc.operating_costs:
        # Populate project resource counters so later recalculation remains consistent.
        doc.supervisors = cint(data.get("supervisors_count") or doc.supervisors)
        doc.assistants = cint(data.get("assistants_count") or doc.assistants)
        doc.save(ignore_permissions=True)

    # Ramadan and recurring fasting projects normally reuse the same table owners
    # and field team.  Copy the latest setup only when explicitly requested.
    if cint(data.get("reuse_last_setup")):
        previous = frappe.db.get_value(
            "WAFD Iftar Project",
            {"distribution_site": doc.distribution_site, "name": ["!=", doc.name], "docstatus": ["<", 2]},
            "name", order_by="creation desc",
        )
        if previous:
            previous_doc = frappe.get_doc("WAFD Iftar Project", previous)
            # Reuse table-owner allocations only when the previous plan has the same
            # daily allocation. A different-size project must never inherit quantities
            # that exceed its new planned meals (the source of the mobile creation error).
            previous_allocated = sum(cint(r.meal_quantity) for r in (previous_doc.distribution_recipients or []))
            current_planned = cint(doc.planned_distribution_meals) or cint(doc.daily_meals)
            can_reuse_allocations = bool(previous_doc.distribution_recipients and previous_allocated == current_planned)
            if can_reuse_allocations and not doc.distribution_recipients:
                for row in previous_doc.distribution_recipients:
                    values = row.as_dict().copy()
                    for key in ("name", "parent", "parentfield", "parenttype", "idx", "doctype"):
                        values.pop(key, None)
                    doc.append("distribution_recipients", values)
            if not cint(data.get("supervisors_count")):
                doc.supervisors = cint(previous_doc.supervisors)
            if not cint(data.get("assistants_count")):
                doc.assistants = cint(previous_doc.assistants)
            if can_reuse_allocations or not cint(data.get("supervisors_count")) or not cint(data.get("assistants_count")):
                doc.save(ignore_permissions=True)

    generate_daily_operations(doc.name, ignore_permissions=True)
    first_operation = frappe.db.get_value("WAFD Iftar Daily Operation", {"project": doc.name}, "name", order_by="operation_date asc")
    return {"name": doc.name, "route": f"/app/wafd-iftar-project/{doc.name}", "first_operation": first_operation}


@frappe.whitelist()
def generate_daily_operations(project_name, ignore_permissions=False):
    project = frappe.get_doc("WAFD Iftar Project", project_name)
    if not ignore_permissions:
        project.check_permission("write")

    if not project.start_date or not project.end_date or cint(project.daily_meals) <= 0:
        return {"created": 0, "updated": 0, "removed": 0}

    start = getdate(project.start_date)
    end = getdate(project.end_date)
    expected_dates = set()
    day = start
    while day <= end:
        expected_dates.add(day)
        day = add_days(day, 1)

    existing = frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": project.name},
        fields=[
            "name", "operation_date", "status", "produced_meals", "packaged_meals",
            "loaded_meals", "delivered_meals", "received_meals", "docstatus",
        ],
    )
    by_date = {getdate(row.operation_date): row for row in existing}
    created = updated = removed = 0

    for operation_date in sorted(expected_dates):
        row = by_date.get(operation_date)
        if not row:
            frappe.get_doc({
                "doctype": "WAFD Iftar Daily Operation",
                "project": project.name,
                "operation_date": operation_date,
                "planned_meals": cint(project.daily_meals),
                "status": "مخطط / Planned",
                "produced_meals": 0,
                "packaged_meals": 0,
                "loaded_meals": 0,
                "delivered_meals": 0,
                "received_meals": 0,
                "surplus_meals": 0,
                "waste_meals": 0,
                "preservation_society_quantity": 0,
            }).insert(ignore_permissions=True)
            created += 1
        elif cint(frappe.db.get_value("WAFD Iftar Daily Operation", row.name, "planned_meals")) != cint(project.daily_meals):
            frappe.db.set_value(
                "WAFD Iftar Daily Operation", row.name, "planned_meals", cint(project.daily_meals),
                update_modified=False,
            )
            updated += 1

    # Remove only untouched draft rows outside the new project range. Never
    # delete operational history containing entered quantities.
    for operation_date, row in by_date.items():
        if operation_date in expected_dates:
            continue
        has_activity = any(cint(row.get(field)) for field in [
            "produced_meals", "packaged_meals", "loaded_meals", "delivered_meals", "received_meals"
        ])
        if not has_activity and cint(row.docstatus) == 0:
            frappe.delete_doc("WAFD Iftar Daily Operation", row.name, ignore_permissions=True)
            removed += 1

    return {"created": created, "updated": updated, "removed": removed}


@frappe.whitelist()
def get_project_operations(project_name):
    frappe.has_permission("WAFD Iftar Project", "read", project_name, throw=True)
    return frappe.get_all(
        "WAFD Iftar Daily Operation",
        filters={"project": project_name},
        fields=[
            "name", "operation_date", "status", "planned_meals", "produced_meals",
            "packaged_meals", "loaded_meals", "delivered_meals", "received_meals",
            "surplus_meals", "waste_meals", "completion_percent",
        ],
        order_by="operation_date asc",
    )


@frappe.whitelist()
def get_dashboard(date=None):
    operation_date = getdate(date or nowdate())

    def fetch_rows(target_date):
        data = frappe.get_all(
            "WAFD Iftar Daily Operation",
            filters={"operation_date": target_date},
            fields=[
                "name", "project", "status", "planned_meals", "produced_meals",
                "packaged_meals", "loaded_meals", "delivered_meals", "received_meals",
                "completion_percent",
            ],
            order_by="modified desc",
        )
        if data:
            project_names = list({row.project for row in data if row.project})
            project_meta = {
                row.name: row for row in frappe.get_all(
                    "WAFD Iftar Project",
                    filters={"name": ["in", project_names]},
                    fields=["name", "project_title", "distribution_site", "contracting_entity"],
                )
            }
            for row in data:
                meta = project_meta.get(row.project)
                row.project_title = meta.project_title if meta else row.project
                row.distribution_site = meta.distribution_site if meta else ""
                row.contracting_entity = meta.contracting_entity if meta else ""
        return data

    rows = fetch_rows(operation_date)

    # Self-healing: generate missing daily rows for projects covering selected date.
    if not rows:
        projects = frappe.get_all(
            "WAFD Iftar Project",
            filters={
                "start_date": ["<=", operation_date],
                "end_date": [">=", operation_date],
                "docstatus": ["<", 2],
            },
            pluck="name",
        )
        for project_name in projects:
            generate_daily_operations(project_name, ignore_permissions=True)
        if projects:
            rows = fetch_rows(operation_date)

    # When today has no work, suggest the nearest available operation date so
    # the operations page does not appear empty while a project is upcoming.
    suggested_date = None
    if not rows:
        nearest = frappe.db.sql(
            """
            select operation_date
            from `tabWAFD Iftar Daily Operation`
            where docstatus < 2
            order by abs(datediff(operation_date, %s)), operation_date asc
            limit 1
            """,
            operation_date,
            as_dict=True,
        )
        if nearest:
            suggested_date = nearest[0].operation_date

    keys = [
        "planned_meals", "produced_meals", "packaged_meals", "loaded_meals",
        "delivered_meals", "received_meals",
    ]
    sums = {key: sum(cint(row.get(key)) for row in rows) for key in keys}
    sums["remaining_meals"] = max(0, sums["planned_meals"] - sums["received_meals"])
    sums["project_count"] = len({row.project for row in rows})
    active_projects = frappe.get_list(
        "WAFD Iftar Project",
        filters={"docstatus": ["<", 2]},
        fields=["name", "project_title", "distribution_site", "start_date", "end_date", "daily_meals", "total_meals", "status"],
        order_by="start_date desc, modified desc",
        limit_page_length=500,
    )
    sums["active_project_count"] = len(active_projects)
    sums["completion_percent"] = round(
        sums["received_meals"] / sums["planned_meals"] * 100, 1
    ) if sums["planned_meals"] else 0
    return {
        "summary": sums,
        "rows": rows,
        "selected_date": operation_date,
        "suggested_date": suggested_date,
        "active_projects": active_projects,
    }



_STAGE_FIELDS = {
    "produced": "produced_meals",
    "packaged": "packaged_meals",
    "loaded": "loaded_meals",
    "delivered": "delivered_meals",
    "received": "received_meals",
}


@frappe.whitelist()
def update_daily_stage(operation_name, stage, recipient_name=None, recipient_id=None, received_by=None, table_owner_name=None, supervisor_name=None, supervisors_manager=None, assigned_meals=None, assistants=None):
    """Advance a daily operation safely, including records that were submitted in older releases."""
    if stage not in _STAGE_FIELDS:
        frappe.throw(_("مرحلة تشغيل غير صالحة / Invalid operation stage"))

    doc = frappe.get_doc("WAFD Iftar Daily Operation", operation_name)
    doc.check_permission("write")
    planned = cint(doc.planned_meals)
    values = {
        "produced_meals": cint(doc.produced_meals),
        "packaged_meals": cint(doc.packaged_meals),
        "loaded_meals": cint(doc.loaded_meals),
        "delivered_meals": cint(doc.delivered_meals),
        "received_meals": cint(doc.received_meals),
    }
    source = {
        "produced": planned,
        "packaged": values["produced_meals"],
        "loaded": values["packaged_meals"],
        "delivered": values["loaded_meals"],
        "received": values["delivered_meals"],
    }[stage]
    if stage != "produced" and source <= 0:
        frappe.throw(_("يجب اعتماد المرحلة السابقة أولاً / Complete the previous stage first"))
    if stage == "delivered" and not cint(doc.authority_inspection_approved):
        frappe.throw(_("يجب اعتماد فحص مشرف التغذية قبل التسليم والتوزيع / Authority food inspection must be approved before distribution"))

    updates = {_STAGE_FIELDS[stage]: source}
    if stage == "received":
        final_recipient = (recipient_name or doc.recipient_name or "").strip()
        if not final_recipient:
            frappe.throw(_("اسم المستلم مطلوب قبل اعتماد الاستلام / Recipient name is required"))
        updates.update({
            "recipient_name": final_recipient,
            "recipient_id": recipient_id or doc.recipient_id,
            "received_by": received_by or final_recipient,
            "receipt_time": frappe.utils.now_datetime(),
            "table_owner_name": table_owner_name or doc.table_owner_name,
            "supervisor_name": supervisor_name or doc.supervisor_name,
            "supervisors_manager": supervisors_manager or doc.supervisors_manager,
            "assigned_meals": cint(assigned_meals or doc.assigned_meals or planned),
        })
        if assistants:
            assistant_rows = frappe.parse_json(assistants) if isinstance(assistants, str) else assistants
            if len(assistant_rows or []) > 100:
                frappe.throw(_("الحد التشغيلي الحالي 100 مساعد لكل سجل / Maximum 100 assistants per operation"))
            frappe.db.delete("WAFD Iftar Assistant Attendance", {
                "parent": doc.name,
                "parenttype": "WAFD Iftar Daily Operation",
                "parentfield": "assistants_attendance",
            })
            for idx, row in enumerate(assistant_rows or [], 1):
                name = (row.get("assistant_name") or "").strip()
                if not name:
                    continue
                child = frappe.get_doc({
                    "doctype": "WAFD Iftar Assistant Attendance",
                    "parent": doc.name,
                    "parenttype": "WAFD Iftar Daily Operation",
                    "parentfield": "assistants_attendance",
                    "idx": idx,
                    "assistant_name": name,
                    "mobile_no": row.get("mobile_no"),
                    "attendance_status": row.get("attendance_status") or "حاضر / Present",
                    "check_in_time": row.get("check_in_time"),
                    "check_out_time": row.get("check_out_time"),
                    "notes": row.get("notes"),
                })
                child.db_insert()

    # Derive status and completion from the values after this transition.
    values.update({k: cint(v) for k, v in updates.items() if k in values})
    received = values["received_meals"]
    if received >= planned and planned:
        status = "مستلم / Received"
    elif values["delivered_meals"]:
        status = "في التوزيع / Distributing"
    elif values["loaded_meals"]:
        status = "جاهز للتحميل / Ready to Load"
    elif values["produced_meals"]:
        status = "قيد الإنتاج / In Production"
    else:
        status = "مخطط / Planned"
    updates["status"] = status
    updates["completion_percent"] = min(100, received / planned * 100) if planned else 0
    frappe.db.set_value("WAFD Iftar Daily Operation", doc.name, updates, update_modified=True)
    next_operation = None
    if stage == "received":
        next_operation = frappe.db.get_value(
            "WAFD Iftar Daily Operation",
            {"project": doc.project, "operation_date": [">", doc.operation_date], "docstatus": ["<", 2]},
            "name",
            order_by="operation_date asc",
        )
    return {
        "name": doc.name,
        "stage": stage,
        "status": status,
        "completion_percent": updates["completion_percent"],
        "next_operation": next_operation,
    }


@frappe.whitelist()
def add_daily_photo(operation_name, photo, caption=None, site_label=None, table_owner_name=None, include_in_report=1):
    """Attach a field photo to the daily operation from a supervisor/manager account."""
    doc = frappe.get_doc("WAFD Iftar Daily Operation", operation_name)
    doc.check_permission("write")
    if not photo:
        frappe.throw(_("الصورة مطلوبة / Photo is required"))
    row = doc.append("daily_photos", {
        "photo": photo,
        "caption": caption or "",
        "site_label": site_label or doc.distribution_site or "",
        "table_owner_name": table_owner_name or doc.table_owner_name or "",
        "uploaded_by": frappe.utils.get_fullname(frappe.session.user) or frappe.session.user,
        "uploaded_at": frappe.utils.now_datetime(),
        "include_in_report": cint(include_in_report),
    })
    doc.save(ignore_permissions=True)
    return {"name": row.name, "count": len(doc.daily_photos or [])}


@frappe.whitelist()
def remove_daily_photo(operation_name, row_name):
    doc = frappe.get_doc("WAFD Iftar Daily Operation", operation_name)
    doc.check_permission("write")
    doc.set("daily_photos", [r for r in (doc.daily_photos or []) if r.name != row_name])
    doc.save(ignore_permissions=True)
    return {"count": len(doc.daily_photos or [])}
