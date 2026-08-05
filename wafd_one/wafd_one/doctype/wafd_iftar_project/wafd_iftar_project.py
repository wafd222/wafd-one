from __future__ import annotations

import math

import frappe
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt, now_datetime


DAILY_DISTRIBUTION = "يومي (يتكرر لكل يوم) / Daily (Repeats Each Day)"
WHOLE_PROJECT_DISTRIBUTION = "كامل المشروع / Whole Project"
ZAMZAM_INGREDIENT_NAME = "ماء زمزم 330 مل"

PROJECT_SITE_DEFAULTS = {
    "المسجد النبوي الشريف / Prophet’s Mosque": (
        "المسجد النبوي / Prophet Mosque",
        "جهة حكومية / Government Entity",
        "الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي",
    ),
    "مسجد قباء / Quba Mosque": (
        "مسجد قباء / Quba Mosque",
        "جهة حكومية / Government Entity",
        "هيئة تطوير منطقة المدينة المنورة",
    ),
    "مسجد القبلتين / Qiblatain Mosque": (
        "مسجد القبلتين / Qiblatain Mosque",
        "جهة حكومية / Government Entity",
        "هيئة تطوير منطقة المدينة المنورة",
    ),
    "مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)": (
        "الميقات / Miqat",
        "جهة حكومية / Government Entity",
        "هيئة تطوير منطقة المدينة المنورة",
    ),
}

STANDARD_COMPONENTS = [
    ("زبادي", 1, "أساسي / Core", 1),
    ("تمر", 5, "أساسي / Core", 1),
    ("ماء 330 مل", 1, "أساسي / Core", 1),
    ("دقة مدينية", 1, "أساسي / Core", 1),
    ("ملعقة", 1, "أساسي / Core", 1),
    ("منديل معطر", 1, "أساسي / Core", 1),
    ("خبز فتوت", 1, "أساسي / Core", 1),
    ("غلاف إفطار صائم", 1, "تغليف / Packaging", 1),
    ("غلاف شركة وفد المدينة", 1, "تغليف / Packaging", 1),
]


class WAFDIftarProject(Document):
    def validate(self):
        self._apply_project_defaults()
        self._remove_blank_child_rows()
        self._ensure_standard_components()
        self._validate_dates_and_times()
        self._calculate_quantities()
        self._sync_known_operating_quantities()
        self._hydrate_component_costs()
        self._calculate_operating_costs()
        distribution_complete = self._validate_distribution()
        self._auto_generate_cartons(distribution_complete)
        self._hydrate_carton_vehicles()
        self._validate_closing_quantities()
        self._calculate_profitability()

    def _remove_blank_child_rows(self):
        self.set("cartons", [
            row for row in (self.cartons or [])
            if cint(row.carton_no) or cint(row.meal_quantity) or row.recipient_name or row.vehicle
        ])
        self.set("distribution_recipients", [
            row for row in (self.distribution_recipients or [])
            if row.table_owner_name or cint(row.meal_quantity) or row.supervisor_name or row.assistant_name
        ])
        self.set("operating_costs", [
            row for row in (self.operating_costs or [])
            if row.cost_type or row.description or flt(row.quantity) or flt(row.rate)
        ])


    def _apply_project_defaults(self):
        defaults = PROJECT_SITE_DEFAULTS.get(self.project_title)
        if defaults:
            self.distribution_site, self.contracting_entity_type, self.contracting_entity = defaults
        elif self.project_title == "مشروع أو موقع آخر / Other Project or Site":
            self.distribution_site = "موقع آخر / Other"

    def _ensure_standard_components(self):
        # Standard meal materials are automatic; the user only selects optional additions.
        if self.components:
            return
        rows = list(STANDARD_COMPONENTS)
        if self.include_zamzam:
            rows.append((ZAMZAM_INGREDIENT_NAME, 1, "إضافة / Add-on", 1))
        missing = []
        for ingredient_name, qty, group, mandatory in rows:
            ingredient = _ingredient_name(ingredient_name)
            if not ingredient:
                missing.append(ingredient_name)
                continue
            self.append("components", {
                "ingredient": ingredient,
                "quantity_per_meal": qty,
                "component_group": group,
                "is_mandatory": mandatory,
            })
        if missing:
            frappe.throw("المواد المرجعية التالية غير موجودة: " + "، ".join(missing))

    def _validate_dates_and_times(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw("تاريخ النهاية لا يمكن أن يسبق تاريخ البداية / End date cannot precede start date")
        if self.departure_time and self.site_arrival_time and self.site_arrival_time < self.departure_time:
            frappe.throw("وقت الوصول لا يمكن أن يسبق وقت مغادرة المصنع / Arrival cannot precede factory departure")
        if self.site_arrival_time and self.distribution_deadline and self.distribution_deadline < self.site_arrival_time:
            frappe.throw("موعد التسليم لا يمكن أن يسبق وقت الوصول / Distribution deadline cannot precede arrival")

    def _calculate_quantities(self):
        days = date_diff(self.end_date, self.start_date) + 1 if self.start_date and self.end_date else 0
        self.number_of_days = max(days, 0)
        if cint(self.daily_meals) <= 0:
            frappe.throw("عدد الوجبات اليومية يجب أن يكون أكبر من صفر / Daily meals must be greater than zero")
        self.total_meals = cint(self.daily_meals) * cint(self.number_of_days)
        if cint(self.max_carton_capacity) <= 0 or cint(self.max_carton_capacity) > 25:
            frappe.throw("السعة القصوى للكرتون يجب أن تكون من 1 إلى 25 وجبة / Carton capacity must be between 1 and 25 meals")
        self.planned_distribution_meals = (
            cint(self.total_meals)
            if self.distribution_plan_basis == WHOLE_PROJECT_DISTRIBUTION
            else cint(self.daily_meals)
        )

    def _sync_known_operating_quantities(self):
        mapping = {
            "المشرف العام / General Supervisor": (cint(self.general_supervisors), "لليوم / Per Day"),
            "المشرفون / Supervisors": (cint(self.supervisors), "لليوم / Per Day"),
            "المساعدون / Assistants": (cint(self.assistants), "لليوم / Per Day"),
            "النقل / Transport": (cint(self.vehicles_count), "لليوم / Per Day"),
            "ثلاجات الشاي / Tea Coolers": (cint(self.tea_coolers), "للمشروع / Per Project"),
            "ثلاجات القهوة / Coffee Coolers": (cint(self.coffee_coolers), "للمشروع / Per Project"),
            "أكياس النفايات / Waste Bags": (cint(self.waste_bag_count), "للوحدة / Per Unit"),
            "السفر / Tablecloths": (len(self.distribution_recipients or []), "للوحدة / Per Unit"),
        }
        for row in self.operating_costs or []:
            if row.cost_type in mapping:
                quantity, default_basis = mapping[row.cost_type]
                row.quantity = quantity
                row.allocation_basis = row.allocation_basis or default_basis

    def _hydrate_component_costs(self):
        seen = set()
        for row in self.components or []:
            if not row.ingredient:
                continue
            if row.ingredient in seen:
                frappe.throw(f"المادة مكررة في مكونات الوجبة: {row.ingredient} / Duplicate meal component")
            seen.add(row.ingredient)
            data = frappe.db.get_value(
                "WAFD Ingredient",
                row.ingredient,
                ["ingredient_name", "uom", "latest_market_cost", "standard_cost", "latest_price_source", "cost_basis"],
                as_dict=True,
            ) or {}
            row.uom = row.uom or data.get("uom")
            resolved_cost = flt(data.get("latest_market_cost")) or flt(data.get("standard_cost"))
            if not resolved_cost and data.get("ingredient_name") == ZAMZAM_INGREDIENT_NAME:
                resolved_cost = flt(self.zamzam_reference_price)
            if not flt(row.unit_cost):
                row.unit_cost = resolved_cost
            row.price_source = data.get("latest_price_source") or data.get("cost_basis") or "المخزون / Inventory"
            row.cost_per_meal = flt(row.quantity_per_meal) * flt(row.unit_cost)
            if row.is_mandatory and flt(row.quantity_per_meal) <= 0:
                frappe.throw(f"الكمية مطلوبة للمادة الإلزامية {row.ingredient} / Quantity is required for mandatory component")

    def _calculate_operating_costs(self):
        days = max(cint(self.number_of_days), 1)
        meals = cint(self.total_meals)
        for row in self.operating_costs or []:
            multiplier = 1
            if row.allocation_basis == "لليوم / Per Day":
                multiplier = days
            elif row.allocation_basis == "للوجبة / Per Meal":
                multiplier = meals
            row.amount = flt(row.quantity) * flt(row.rate) * multiplier
        self.operating_cost_total = sum(flt(r.amount) for r in (self.operating_costs or []))

    def _validate_distribution(self):
        distributed = 0
        names = set()
        capacity = cint(self.max_carton_capacity) or 25
        for row in self.distribution_recipients or []:
            qty = cint(row.meal_quantity)
            if qty < 25:
                frappe.throw("أقل كمية لصاحب السفرة هي 25 وجبة / Minimum allocation per table owner is 25 meals")
            identity = (row.table_owner_name or "").strip()
            if identity and identity in names:
                frappe.throw(f"صاحب السفرة مكرر: {identity} / Duplicate table owner")
            names.add(identity)
            row.carton_count = math.ceil(qty / capacity)
            if row.received and not row.received_on:
                row.received_on = now_datetime()
            distributed += qty
        self.distribution_variance = cint(self.planned_distribution_meals) - distributed
        if distributed > cint(self.planned_distribution_meals):
            frappe.throw("إجمالي كميات التوزيع يتجاوز وجبات خطة التوزيع / Distribution exceeds planned distribution meals")
        return bool(distributed and distributed == cint(self.planned_distribution_meals))

    def _auto_generate_cartons(self, distribution_complete: bool):
        """Generate carton rows only when the allocation is complete.

        Draft projects remain saveable while distribution is incomplete. Any manually
        added empty carton row is ignored. Generated operational status and vehicle
        assignments are preserved when the allocation has not changed.
        """
        if not distribution_complete:
            self.set("cartons", [])
            return

        capacity = cint(self.max_carton_capacity) or 25
        if capacity < 1 or capacity > 25:
            frappe.throw("السعة القصوى للكرتون من 1 إلى 25 وجبة / Carton capacity must be between 1 and 25 meals")

        expected_plan = []
        carton_no = 1
        for recipient in self.distribution_recipients or []:
            remaining = cint(recipient.meal_quantity)
            recipient.carton_count = math.ceil(remaining / capacity) if remaining else 0
            while remaining > 0:
                qty = min(capacity, remaining)
                expected_plan.append((carton_no, recipient.table_owner_name, qty))
                remaining -= qty
                carton_no += 1

        current_plan = [
            (cint(row.carton_no), row.recipient_name, cint(row.meal_quantity))
            for row in (self.cartons or [])
        ]
        if current_plan == expected_plan:
            return

        previous = {
            (cint(row.carton_no), row.recipient_name, cint(row.meal_quantity)): row
            for row in (self.cartons or [])
        }
        self.set("cartons", [])
        for number, recipient_name, meals in expected_plan:
            old = previous.get((number, recipient_name, meals))
            self.append("cartons", {
                "carton_no": number,
                "recipient_name": recipient_name,
                "meal_quantity": meals,
                "status": old.status if old else "مخطط / Planned",
                "vehicle": old.vehicle if old else None,
                "notes": old.notes if old else None,
            })

    def _hydrate_carton_vehicles(self):
        for row in self.cartons or []:
            if not row.vehicle:
                row.vehicle_details = ""
                continue
            vehicle = frappe.db.get_value(
                "WAFD Vehicle", row.vehicle, ["plate_number", "vehicle_type", "make_model"], as_dict=True
            ) or {}
            parts = [vehicle.get("plate_number"), vehicle.get("vehicle_type"), vehicle.get("make_model")]
            row.vehicle_details = " — ".join(str(part) for part in parts if part)

    def _validate_closing_quantities(self):
        closing_values = [cint(self.surplus_meals), cint(self.waste_meals), cint(self.preservation_society_quantity)]
        if any(value < 0 for value in closing_values):
            frappe.throw("كميات الإغلاق لا يمكن أن تكون سالبة / Closing quantities cannot be negative")
        if sum(closing_values) > cint(self.total_meals):
            frappe.throw("إجمالي الفائض والتالف والمسلّم للجمعية يتجاوز وجبات المشروع / Closing quantities exceed project meals")

    def _calculate_profitability(self):
        material_per_meal = sum(flt(r.cost_per_meal) for r in (self.components or []))
        self.material_cost_total = material_per_meal * cint(self.total_meals)
        self.total_project_cost = flt(self.material_cost_total) + flt(self.operating_cost_total)
        self.actual_cost_per_meal = self.total_project_cost / self.total_meals if self.total_meals else 0
        self.total_revenue = flt(self.sale_price_per_meal) * cint(self.total_meals)
        self.expected_profit = flt(self.total_revenue) - flt(self.total_project_cost)
        self.profit_margin = (self.expected_profit / self.total_revenue * 100) if self.total_revenue else 0

    def before_submit(self):
        zero_costs = [
            row.ingredient for row in (self.components or [])
            if row.is_mandatory and flt(row.unit_cost) <= 0
        ]
        if zero_costs:
            frappe.throw(
                "أدخل التكلفة الفعلية للمواد الإلزامية قبل الاعتماد: "
                + "، ".join(zero_costs)
                + " / Mandatory component costs are missing"
            )
        if cint(self.distribution_variance) != 0:
            frappe.throw("يجب توزيع كامل وجبات الخطة قبل الاعتماد / All planned meals must be allocated before submission")
        carton_meals = sum(cint(row.meal_quantity) for row in (self.cartons or []))
        if not self.cartons or carton_meals != cint(self.planned_distribution_meals):
            frappe.throw("أنشئ خطة كراتين مطابقة لخطة التوزيع قبل الاعتماد / Generate a matching carton plan before submission")


def _ingredient_name(name: str) -> str | None:
    return frappe.db.get_value("WAFD Ingredient", {"ingredient_name": name}, "name")


@frappe.whitelist()
def load_standard_components(project_name: str):
    doc = frappe.get_doc("WAFD Iftar Project", project_name)
    doc.check_permission("write")
    standard = list(STANDARD_COMPONENTS)
    if doc.include_zamzam:
        standard.append((ZAMZAM_INGREDIENT_NAME, 1, "إضافة / Add-on", 1))

    zamzam_id = _ingredient_name(ZAMZAM_INGREDIENT_NAME)
    if not doc.include_zamzam and zamzam_id:
        doc.set("components", [row for row in (doc.components or []) if row.ingredient != zamzam_id])

    existing = {r.ingredient for r in doc.components or []}
    missing = []
    for ingredient, qty, group, mandatory in standard:
        name = _ingredient_name(ingredient)
        if not name:
            missing.append(ingredient)
            continue
        if name not in existing:
            doc.append("components", {
                "ingredient": name,
                "quantity_per_meal": qty,
                "component_group": group,
                "is_mandatory": mandatory,
            })
    if missing:
        frappe.throw("المواد المرجعية التالية غير موجودة: " + "، ".join(missing))
    doc.save()
    return {"components": len(doc.components)}


@frappe.whitelist()
def load_standard_operating_costs(project_name: str):
    doc = frappe.get_doc("WAFD Iftar Project", project_name)
    doc.check_permission("write")
    standards = [
        ("المشرف العام / General Supervisor", cint(doc.general_supervisors), "لليوم / Per Day"),
        ("المشرفون / Supervisors", cint(doc.supervisors), "لليوم / Per Day"),
        ("المساعدون / Assistants", cint(doc.assistants), "لليوم / Per Day"),
        ("النقل / Transport", cint(doc.vehicles_count), "لليوم / Per Day"),
        ("ثلاجات الشاي / Tea Coolers", cint(doc.tea_coolers), "للمشروع / Per Project"),
        ("ثلاجات القهوة / Coffee Coolers", cint(doc.coffee_coolers), "للمشروع / Per Project"),
        ("أكياس النفايات / Waste Bags", cint(doc.waste_bag_count), "للوحدة / Per Unit"),
        ("السفر / Tablecloths", len(doc.distribution_recipients or []), "للوحدة / Per Unit"),
    ]
    existing = {row.cost_type: row for row in (doc.operating_costs or [])}
    for cost_type, qty, basis in standards:
        if qty <= 0:
            continue
        if cost_type in existing:
            existing[cost_type].quantity = qty
            existing[cost_type].allocation_basis = basis
        else:
            doc.append("operating_costs", {
                "cost_type": cost_type,
                "quantity": qty,
                "allocation_basis": basis,
                "cost_basis": "تكلفة داخلية / Internal Cost",
            })
    doc.save()
    return {"operating_costs": len(doc.operating_costs)}


@frappe.whitelist()
def generate_cartons(project_name: str):
    doc = frappe.get_doc("WAFD Iftar Project", project_name)
    doc.check_permission("write")
    capacity = cint(doc.max_carton_capacity) or 25
    if capacity < 1 or capacity > 25:
        frappe.throw("السعة القصوى للكرتون من 1 إلى 25 وجبة / Carton capacity must be between 1 and 25 meals")
    expected = cint(doc.planned_distribution_meals) or (
        cint(doc.total_meals) if doc.distribution_plan_basis == WHOLE_PROJECT_DISTRIBUTION else cint(doc.daily_meals)
    )
    allocated = sum(cint(row.meal_quantity) for row in (doc.distribution_recipients or []))
    if allocated != expected:
        frappe.throw(f"خطة التوزيع يجب أن تساوي {expected} وجبة قبل إنشاء الكراتين / Distribution must equal {expected} meals")

    doc.set("cartons", [])
    carton_no = 1
    for recipient in doc.distribution_recipients or []:
        remaining = cint(recipient.meal_quantity)
        recipient.carton_count = math.ceil(remaining / capacity) if remaining else 0
        while remaining > 0:
            qty = min(capacity, remaining)
            doc.append("cartons", {
                "carton_no": carton_no,
                "recipient_name": recipient.table_owner_name,
                "meal_quantity": qty,
                "status": "مخطط / Planned",
            })
            remaining -= qty
            carton_no += 1
    doc.save()
    return {"carton_count": len(doc.cartons), "meal_count": sum(cint(r.meal_quantity) for r in doc.cartons)}
