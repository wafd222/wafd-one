import frappe
from frappe.model.document import Document
from frappe.utils import add_days, cint, date_diff, flt, getdate, now_datetime


class WAFDCateringProject(Document):
    def validate(self):
        self._sync_from_contract()
        self._validate_dates()
        self._validate_contract()
        self._calculate_services()
        self._calculate_summary()
        self._validate_approvals()

    def before_save(self):
        if self.name and not self.project_code:
            self.project_code = self.name

    def after_insert(self):
        if not self.project_code:
            frappe.db.set_value(self.doctype, self.name, "project_code", self.name, update_modified=False)

    def _sync_from_contract(self):
        if not self.contract or getattr(self.flags, "from_contract_sync", False):
            return
        values = frappe.db.get_value(
            "WAFD Contract",
            self.contract,
            ["mission", "hotel", "start_date", "end_date", "beneficiary_count", "contract_value", "currency",
             "contract_type", "service_model", "first_meal", "last_meal", "vip_count", "children_count",
             "delivery_location", "contact_person", "contact_phone", "delivery_window", "delivery_instructions",
             "project_manager", "operations_manager", "delivery_supervisor", "default_kitchen", "operation_priority",
             "tax_rate", "tax_amount", "grand_total", "discount_amount", "advance_amount"],
            as_dict=True,
        )
        if not values:
            frappe.throw("العقد المحدد غير موجود / Selected contract does not exist")
        sync_fields = (
            "mission", "start_date", "end_date", "beneficiary_count", "contract_value", "currency",
            "contract_type", "service_model", "first_meal", "last_meal", "vip_count", "children_count",
            "delivery_location", "contact_person", "contact_phone", "delivery_window", "delivery_instructions",
            "project_manager", "operations_manager", "delivery_supervisor", "default_kitchen", "operation_priority",
            "tax_rate", "tax_amount", "grand_total", "discount_amount", "advance_amount",
        )
        for fieldname in sync_fields:
            if self.get(fieldname) in (None, "", 0) and values.get(fieldname) not in (None, ""):
                self.set(fieldname, values.get(fieldname))

        contract_hotel = values.get("hotel")
        if contract_hotel:
            if not self.primary_hotel:
                self.primary_hotel = contract_hotel
            if not any(row.hotel == contract_hotel for row in (self.hotels or [])):
                self.append("hotels", {
                    "hotel": contract_hotel,
                    "guest_count": self.beneficiary_count or 0,
                })

    def _validate_contract(self):
        if not self.contract:
            return
        contract = frappe.db.get_value(
            "WAFD Contract", self.contract,
            ["project", "mission", "start_date", "end_date"], as_dict=True,
        )
        if not contract:
            frappe.throw("العقد المحدد غير موجود / Selected contract does not exist")
        if contract.project and contract.project != self.name:
            frappe.throw("العقد مرتبط بمشروع آخر / Contract is linked to another project")
        if contract.mission and self.mission and contract.mission != self.mission:
            frappe.throw("العميل في المشروع لا يطابق العميل في العقد / Project mission does not match contract mission")
        if contract.start_date and self.start_date and getdate(self.start_date) < getdate(contract.start_date):
            frappe.throw("بداية المشروع لا يمكن أن تسبق بداية العقد / Project cannot start before contract")
        if contract.end_date and self.end_date and getdate(self.end_date) > getdate(contract.end_date):
            frappe.throw("نهاية المشروع لا يمكن أن تتجاوز نهاية العقد / Project cannot end after contract")

    def _validate_dates(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                frappe.throw("تاريخ النهاية يجب أن يكون بعد تاريخ البداية / End date must be after start date")
            self.duration_days = date_diff(self.end_date, self.start_date) + 1
        else:
            self.duration_days = 0

    def _calculate_services(self):
        total_meals = 0
        estimated_revenue = 0
        default_days = cint(self.duration_days) or 1
        default_beneficiaries = cint(self.beneficiary_count)
        for row in self.get("services") or []:
            service_start = getdate(row.service_start_date or self.start_date) if self.start_date else None
            service_end = getdate(row.service_end_date or self.end_date) if self.end_date else None
            if service_start and service_end and service_end < service_start:
                frappe.throw(f"تاريخ نهاية الخدمة يجب أن يكون بعد بدايتها في صف {row.idx} / Invalid service date range in row {row.idx}")
            if self.start_date and service_start and service_start < getdate(self.start_date):
                frappe.throw(f"بداية الخدمة خارج مدة المشروع في صف {row.idx} / Service starts before project in row {row.idx}")
            if self.end_date and service_end and service_end > getdate(self.end_date):
                frappe.throw(f"نهاية الخدمة خارج مدة المشروع في صف {row.idx} / Service ends after project in row {row.idx}")
            calculated_days = date_diff(service_end, service_start) + 1 if service_start and service_end else default_days
            days = cint(row.service_days) or calculated_days
            row.service_days = days
            beneficiaries = cint(row.beneficiaries) or default_beneficiaries
            multiplier = flt(row.meals_per_person_per_day) or 1
            row.total_meals = cint(days * beneficiaries * multiplier)
            row.estimated_revenue = flt(row.total_meals) * flt(row.unit_price)
            total_meals += cint(row.total_meals)
            estimated_revenue += flt(row.estimated_revenue)
        self.total_meals = total_meals
        self.estimated_revenue = estimated_revenue or flt(self.contract_value)

    def _calculate_summary(self):
        self.remaining_meals = max(cint(self.total_meals) - cint(self.delivered_meals), 0)
        self.progress_percent = (flt(self.delivered_meals) / flt(self.total_meals) * 100) if self.total_meals else 0
        self.profit = flt(self.revenue) - flt(self.actual_cost)
        self.profit_margin_percent = (self.profit / flt(self.revenue) * 100) if self.revenue else 0

    def _validate_approvals(self):
        if self.is_new():
            return
        previous = self.get_doc_before_save()
        if not previous:
            return
        checks = {
            "project_manager_approved": {"System Manager", "WAFD Project Manager"},
            "operations_approved": {"System Manager", "WAFD Operations Manager"},
            "finance_approved": {"System Manager", "WAFD Finance User"},
            "general_manager_approved": {"System Manager"},
        }
        user_roles = set(frappe.get_roles())
        for fieldname, allowed_roles in checks.items():
            if cint(self.get(fieldname)) != cint(previous.get(fieldname)) and not user_roles.intersection(allowed_roles):
                frappe.throw(f"ليس لديك صلاحية تغيير الاعتماد: {self.meta.get_label(fieldname)}")


    def on_update(self):
        if self.contract and not getattr(self.flags, "from_contract_sync", False):
            values = {"project": self.name}
            if self.mission:
                values["mission"] = self.mission
            frappe.db.set_value("WAFD Contract", self.contract, values, update_modified=False)

MEAL_SEQUENCE = (
    "سحور / Suhoor",
    "إفطار / Breakfast",
    "كوفي بريك / Coffee Break",
    "غداء / Lunch",
    "عشاء / Dinner",
    "إفطار صائم / Iftar Saem",
)

MEAL_DEFAULT_TIMES = {
    "سحور / Suhoor": "02:00:00",
    "إفطار / Breakfast": "07:00:00",
    "كوفي بريك / Coffee Break": "10:00:00",
    "غداء / Lunch": "13:00:00",
    "عشاء / Dinner": "19:00:00",
    "إفطار صائم / Iftar Saem": "18:00:00",
}

# Meal Plan historically used a shorter English label for Iftar Saem.
MEAL_PLAN_TYPE_MAP = {
    "إفطار صائم / Iftar Saem": "إفطار صائم / Iftar",
}


def _project_hotels(project):
    rows = [row for row in (project.hotels or []) if row.hotel]
    if not rows and project.primary_hotel:
        rows = [frappe._dict(hotel=project.primary_hotel, guest_count=project.beneficiary_count or 0)]
    if not rows:
        frappe.throw("أضف فندقاً واحداً على الأقل / Add at least one hotel")
    return rows


def _allocate_hotel_counts(project, hotel_rows, total_beneficiaries):
    hotel_counts = [max(cint(row.guest_count), 0) for row in hotel_rows]
    allocated = sum(hotel_counts)
    if allocated > total_beneficiaries and total_beneficiaries:
        frappe.throw(
            f"مجموع نزلاء الفنادق ({allocated}) يتجاوز عدد المستفيدين ({total_beneficiaries}) / Hotel allocation exceeds beneficiaries"
        )
    if not allocated:
        base, remainder = divmod(total_beneficiaries, len(hotel_rows))
        hotel_counts = [base + (1 if idx < remainder else 0) for idx in range(len(hotel_rows))]
    elif allocated < total_beneficiaries:
        hotel_counts[-1] += total_beneficiaries - allocated
    return hotel_counts


def _meal_range_for_date(project, service_date):
    """Return meals allowed on a date, respecting first/last meal boundaries."""
    meals = list(MEAL_SEQUENCE)
    first_meal = project.first_meal if project.first_meal in meals else "إفطار / Breakfast"
    last_meal = project.last_meal if project.last_meal in meals else "عشاء / Dinner"
    if getdate(service_date) == getdate(project.start_date):
        meals = meals[meals.index(first_meal):]
    if getdate(service_date) == getdate(project.end_date):
        meals = meals[: meals.index(last_meal) + 1]
    return meals


def _schedule_rows(project):
    """Build normalized meal schedule rows from explicit services or contract boundaries."""
    rows = []
    if project.services:
        for service in project.services:
            service_start = getdate(service.service_start_date or project.start_date)
            service_end = getdate(service.service_end_date or project.end_date)
            if service.service_days:
                service_end = min(service_end, getdate(add_days(service_start, cint(service.service_days) - 1)))
            current_date = service_start
            while current_date <= service_end:
                rows.append(frappe._dict(
                    service_date=current_date,
                    meal_type=service.service_type,
                    service_time=service.service_time or MEAL_DEFAULT_TIMES.get(service.service_type),
                    menu_name=service.meal_name or service.service_type,
                    recipe=service.recipe,
                    unit_price=flt(service.unit_price),
                    beneficiaries=cint(service.beneficiaries) or cint(project.beneficiary_count),
                    multiplier=flt(service.meals_per_person_per_day) or 1,
                    source_service_row=service.name,
                ))
                current_date = getdate(add_days(current_date, 1))
        return rows

    # No service rows: derive the full schedule directly from project dates and
    # first/last meal. This makes a newly-created contract project operational
    # without duplicating the same data in a service table first.
    current_date = getdate(project.start_date)
    while current_date <= getdate(project.end_date):
        for meal_type in _meal_range_for_date(project, current_date):
            rows.append(frappe._dict(
                service_date=current_date,
                meal_type=meal_type,
                service_time=MEAL_DEFAULT_TIMES.get(meal_type),
                menu_name=meal_type,
                recipe=None,
                unit_price=0,
                beneficiaries=cint(project.beneficiary_count),
                multiplier=1,
                source_service_row=None,
            ))
        current_date = getdate(add_days(current_date, 1))
    return rows


def _meal_plan_preview(project):
    hotel_rows = _project_hotels(project)
    schedule = _schedule_rows(project)
    plan_count = 0
    total_quantity = 0
    dates = set()
    meals = set()
    for row in schedule:
        counts = _allocate_hotel_counts(project, hotel_rows, cint(row.beneficiaries))
        for guests in counts:
            quantity = cint(guests * flt(row.multiplier))
            if quantity > 0:
                plan_count += 1
                total_quantity += quantity
        dates.add(str(row.service_date))
        meals.add(row.meal_type)
    return {
        "plan_count": plan_count,
        "total_quantity": total_quantity,
        "day_count": len(dates),
        "hotel_count": len(hotel_rows),
        "meal_types": list(meals),
        "derived_from_services": bool(project.services),
    }


@frappe.whitelist()
def get_meal_plan_preview(project_name):
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("read")
    if not project.start_date or not project.end_date:
        frappe.throw("حدد تاريخ بداية ونهاية المشروع / Set project start and end dates")
    if cint(project.beneficiary_count) <= 0:
        frappe.throw("حدد عدد المستفيدين / Set beneficiary count")
    return _meal_plan_preview(project)


@frappe.whitelist()
def generate_meal_plans(project_name, replace_existing=0):
    """Generate daily hotel meal plans from explicit services or project meal boundaries."""
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("write")
    if project.status in ("مكتمل / Completed", "ملغي / Cancelled"):
        frappe.throw("لا يمكن إنشاء خطط لمشروع مكتمل أو ملغي / Cannot plan a completed or cancelled project")
    if not project.start_date or not project.end_date:
        frappe.throw("حدد تاريخ بداية ونهاية المشروع / Set project start and end dates")
    if cint(project.beneficiary_count) <= 0:
        frappe.throw("حدد عدد المستفيدين / Set beneficiary count")

    hotel_rows = _project_hotels(project)
    schedule = _schedule_rows(project)
    if not schedule:
        frappe.throw("تعذر تكوين جدول الوجبات / Could not build meal schedule")

    replace_existing = cint(replace_existing)
    if replace_existing:
        protected = frappe.get_all(
            "WAFD Meal Plan",
            filters={"project": project.name, "status": ["not in", ["مسودة / Draft", "ملغي / Cancelled"]]},
            pluck="name",
        )
        if protected:
            frappe.throw(
                "لا يمكن الاستبدال لوجود خطط بدأ تنفيذها: {0} / Cannot replace plans already in operation".format(
                    ", ".join(protected[:5])
                )
            )
        existing = frappe.get_all("WAFD Meal Plan", filters={"project": project.name}, pluck="name")
        for name in existing:
            frappe.delete_doc("WAFD Meal Plan", name, ignore_permissions=True)

    created = 0
    skipped = 0
    total_quantity = 0
    warnings = []
    for row in schedule:
        total_beneficiaries = cint(row.beneficiaries) or cint(project.beneficiary_count)
        hotel_counts = _allocate_hotel_counts(project, hotel_rows, total_beneficiaries)
        for hotel_row, guests in zip(hotel_rows, hotel_counts):
            quantity = cint(guests * flt(row.multiplier))
            if quantity <= 0:
                continue
            meal_type = MEAL_PLAN_TYPE_MAP.get(row.meal_type, row.meal_type)
            filters = {
                "project": project.name,
                "hotel": hotel_row.hotel,
                "service_date": row.service_date,
                "meal_type": meal_type,
            }
            if row.source_service_row:
                filters["source_service_row"] = row.source_service_row
            if frappe.db.exists("WAFD Meal Plan", filters):
                skipped += 1
                continue
            doc = frappe.get_doc({
                "doctype": "WAFD Meal Plan",
                **filters,
                "quantity": quantity,
                "service_time": row.service_time,
                "menu_name": row.menu_name or meal_type,
                "recipe": row.recipe,
                "unit_price": flt(row.unit_price),
                "status": "مسودة / Draft",
            })
            doc.insert()
            created += 1
            total_quantity += quantity
            if not row.recipe:
                warnings.append(f"{row.service_date} - {meal_type}: لا توجد وصفة / Recipe missing")

    totals = {
        "meal_plans": frappe.db.count("WAFD Meal Plan", {"project": project.name}),
        "total_quantity": sum(
            cint(x.quantity) for x in frappe.get_all(
                "WAFD Meal Plan", filters={"project": project.name, "status": ["!=", "ملغي / Cancelled"]}, fields=["quantity"]
            )
        ),
    }
    frappe.db.set_value(
        project.doctype,
        project.name,
        {
            "meal_plans_created": totals["meal_plans"],
            "last_operation_plan_at": now_datetime(),
            "status": "تخطيط / Planning" if project.status == "مسودة / Draft" else project.status,
        },
        update_modified=True,
    )
    return {
        "created": created,
        "skipped": skipped,
        "created_quantity": total_quantity,
        "totals": totals,
        "warnings": list(dict.fromkeys(warnings)),
        "derived_from_services": bool(project.services),
    }


@frappe.whitelist()
def generate_operation_plan(project_name):
    """Create the operational documents for a catering project without duplicating existing records."""
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("write")

    if project.status in ("مكتمل / Completed", "ملغي / Cancelled"):
        frappe.throw("لا يمكن إنشاء خطة تشغيل لمشروع مكتمل أو ملغي / Cannot plan a completed or cancelled project")

    meal_result = generate_meal_plans(project.name)
    meal_plans = frappe.get_all(
        "WAFD Meal Plan",
        filters={"project": project.name, "status": ["!=", "ملغي / Cancelled"]},
        fields=["name", "hotel", "service_date", "service_time", "quantity", "recipe"],
        order_by="service_date asc, service_time asc",
    )

    batches_created = 0
    batches_skipped = 0
    # Delivery trips are intentionally not created here. A trip must be linked
    # to a completed loading record and is created later from that record.
    trips_created = 0
    trips_skipped = frappe.db.count("WAFD Delivery Trip", {"project": project.name})
    warnings = []

    for plan in meal_plans:
        batch_name = frappe.db.get_value("WAFD Production Batch", {"meal_plan": plan.name}, "name")
        if batch_name:
            batches_skipped += 1
        else:
            if not plan.recipe:
                warnings.append(f"{plan.name}: لا توجد وصفة / Recipe is missing")
            else:
                batch = frappe.get_doc({
                    "doctype": "WAFD Production Batch",
                    "project": project.name,
                    "meal_plan": plan.name,
                    "recipe": plan.recipe,
                    "source_warehouse": project.default_source_warehouse,
                    "batch_date": plan.service_date,
                    "planned_quantity": plan.quantity,
                    "status": "مخطط / Planned",
                })
                batch.insert()
                batches_created += 1

    totals = {
        "meal_plans": frappe.db.count("WAFD Meal Plan", {"project": project.name}),
        "production_batches": frappe.db.count("WAFD Production Batch", {"project": project.name}),
        "delivery_trips": frappe.db.count("WAFD Delivery Trip", {"project": project.name}),
    }
    frappe.db.set_value(
        project.doctype,
        project.name,
        {
            "meal_plans_created": totals["meal_plans"],
            "production_batches_created": totals["production_batches"],
            "delivery_trips_created": totals["delivery_trips"],
            "last_operation_plan_at": now_datetime(),
            "status": "تخطيط / Planning" if project.status == "مسودة / Draft" else project.status,
        },
        update_modified=True,
    )

    return {
        "meal_plans_created": meal_result.get("created", 0),
        "meal_plans_skipped": meal_result.get("skipped", 0),
        "batches_created": batches_created,
        "batches_skipped": batches_skipped,
        "trips_created": trips_created,
        "trips_skipped": trips_skipped,
        "totals": totals,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _combine_service_datetime(service_date, service_time, minutes_before=0):
    if not service_date or not service_time:
        return None
    from datetime import timedelta
    from frappe.utils import get_datetime

    value = get_datetime(f"{service_date} {service_time}")
    return value - timedelta(minutes=minutes_before)


@frappe.whitelist()
def refresh_production_materials(project_name):
    """Recalculate material requirements for every production batch in a project."""
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("write")
    from wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch import refresh_material_requirements

    names = frappe.get_all("WAFD Production Batch", filters={"project": project.name}, pluck="name")
    totals = {"batches": 0, "available": 0, "shortage": 0, "not_calculated": 0, "material_cost": 0}
    for name in names:
        result = refresh_material_requirements(name)
        totals["batches"] += 1
        totals["material_cost"] += flt(result.get("total_material_cost"))
        status = result.get("materials_status")
        if status in ("متوفرة / Available", "مصروفة / Issued"):
            totals["available"] += 1
        elif status == "عجز / Shortage":
            totals["shortage"] += 1
        else:
            totals["not_calculated"] += 1
    return totals
