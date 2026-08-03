import math

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, cint, now_datetime


class WAFDIftarProject(Document):
    def validate(self):
        self._validate_dates_and_quantities()
        self._calculate_meal_items()
        self._calculate_distribution()
        self._calculate_hospitality_and_costs()

    def before_submit(self):
        if cint(self.unallocated_meals) != 0:
            frappe.throw(
                "يجب توزيع كامل العدد اليومي على أصحاب السفر قبل الاعتماد. المتبقي: {0} وجبة / "
                "Allocate the full daily quantity before submission. Remaining: {0}".format(cint(self.unallocated_meals))
            )
        if not self.distribution_rows:
            frappe.throw("أضف مستلمًا واحدًا على الأقل في خطة التوزيع / Add at least one distribution recipient")
        self.status = "معتمد / Approved"

    def on_cancel(self):
        self.status = "ملغي / Cancelled"

    def _validate_dates_and_quantities(self):
        if self.end_date < self.start_date:
            frappe.throw("تاريخ النهاية لا يمكن أن يسبق تاريخ البداية / End date cannot be before start date")
        self.number_of_days = date_diff(self.end_date, self.start_date) + 1
        if cint(self.daily_meals) <= 0:
            frappe.throw("عدد الوجبات اليومية يجب أن يكون أكبر من صفر / Daily meals must be greater than zero")
        if cint(self.meals_per_carton) <= 0:
            frappe.throw("عدد الوجبات في الكرتون يجب أن يكون أكبر من صفر / Meals per carton must be greater than zero")
        self.total_meals = cint(self.daily_meals) * cint(self.number_of_days)
        self.daily_cartons = math.ceil(cint(self.daily_meals) / cint(self.meals_per_carton))
        self.total_daily_cartons = cint(self.daily_cartons) + cint(self.reserve_cartons)

    def _calculate_meal_items(self):
        total = 0.0
        for row in self.meal_items or []:
            if not cint(row.included):
                row.cost_per_meal = row.total_quantity = row.total_cost = 0
                continue
            if flt(row.quantity_per_meal) <= 0:
                frappe.throw(f"كمية المكون يجب أن تكون أكبر من صفر: {row.item_name}")
            if row.ingredient:
                vals = frappe.db.get_value("WAFD Ingredient", row.ingredient, ["uom", "standard_cost", "latest_market_cost"], as_dict=True)
                if vals:
                    row.uom = vals.uom or row.uom
                    row.unit_cost = flt(vals.latest_market_cost) or flt(vals.standard_cost) or flt(row.unit_cost)
            row.cost_per_meal = flt(row.quantity_per_meal) * flt(row.unit_cost)
            row.total_quantity = flt(row.quantity_per_meal) * cint(self.daily_meals)
            row.total_cost = flt(row.cost_per_meal) * cint(self.daily_meals)
            total += flt(row.total_cost)
        self.meal_material_cost = total

    def _calculate_distribution(self):
        allocated = 0
        cartons = 0
        for row in self.distribution_rows or []:
            if row.recipient:
                vals = frappe.db.get_value("WAFD Iftar Recipient", row.recipient, ["recipient_name", "mobile", "default_location"], as_dict=True)
                if vals:
                    row.recipient_name = vals.recipient_name or row.recipient_name
                    row.mobile = row.mobile or vals.mobile
                    row.distribution_point = row.distribution_point or vals.default_location
            if cint(row.meal_quantity) <= 0:
                frappe.throw("كمية كل مستلم يجب أن تكون أكبر من صفر / Each recipient quantity must be greater than zero")
            row.carton_quantity = math.ceil(cint(row.meal_quantity) / cint(self.meals_per_carton))
            if cint(row.received) and not row.received_at:
                row.received_at = now_datetime()
            allocated += cint(row.meal_quantity)
            cartons += cint(row.carton_quantity)
        if allocated > cint(self.daily_meals):
            frappe.throw("مجموع التوزيع أكبر من عدد الوجبات اليومية / Distribution exceeds daily meals")
        self.allocated_meals = allocated
        self.unallocated_meals = cint(self.daily_meals) - allocated
        self.allocated_cartons = cartons

    def _calculate_hospitality_and_costs(self):
        hospitality = 0.0
        for row in self.hospitality_items or []:
            row.total_cost = flt(row.quantity) * flt(row.unit_cost)
            hospitality += flt(row.total_cost)
        self.hospitality_cost = hospitality
        self.daily_total_cost = flt(self.meal_material_cost) + hospitality + flt(self.labor_cost_daily) + flt(self.transport_cost_daily) + flt(self.other_cost_daily)
        self.cost_per_meal = flt(self.daily_total_cost) / cint(self.daily_meals) if cint(self.daily_meals) else 0
        self.project_total_cost = flt(self.daily_total_cost) * cint(self.number_of_days)
        self.project_revenue = flt(self.selling_price_per_meal) * cint(self.total_meals)
        self.project_profit = flt(self.project_revenue) - flt(self.project_total_cost)


@frappe.whitelist()
def get_standard_iftar_components():
    return [
        {"included": 1, "item_name": "ماء 330 مل / Water 330 ml", "quantity_per_meal": 1, "uom": "عبوة / Bottle", "unit_cost": 0.45},
        {"included": 1, "item_name": "لبن أو زبادي / Laban or Yogurt", "quantity_per_meal": 1, "uom": "عبوة / Cup", "unit_cost": 1.10},
        {"included": 1, "item_name": "تمر / Dates", "quantity_per_meal": 5, "uom": "حبة / Piece", "unit_cost": 0.12, "notes": "سكري أو عجوة أو حسب الاعتماد"},
        {"included": 1, "item_name": "خبز فتوت / Fatoot Bread", "quantity_per_meal": 1, "uom": "قطعة / Piece", "unit_cost": 0.65},
        {"included": 1, "item_name": "دقة مديني / Madini Duqqa", "quantity_per_meal": 1, "uom": "عبوة / Pack", "unit_cost": 0.35},
        {"included": 1, "item_name": "ملعقة / Spoon", "quantity_per_meal": 1, "uom": "حبة / Each", "unit_cost": 0.05},
        {"included": 1, "item_name": "منديل معطر / Wet Wipe", "quantity_per_meal": 1, "uom": "حبة / Each", "unit_cost": 0.08},
        {"included": 1, "item_name": "غلاف خاص / Special Meal Wrap", "quantity_per_meal": 1, "uom": "حبة / Each", "unit_cost": 0.30},
        {"included": 0, "item_name": "بسكويت / Biscuit", "quantity_per_meal": 1, "uom": "عبوة / Pack", "unit_cost": 0.50},
        {"included": 0, "item_name": "معمول / Maamoul", "quantity_per_meal": 1, "uom": "حبة / Piece", "unit_cost": 0.75},
        {"included": 0, "item_name": "لوزين / Lozine Cake", "quantity_per_meal": 1, "uom": "حبة / Piece", "unit_cost": 0.85},
        {"included": 0, "item_name": "ماء زمزم / Zamzam Water", "quantity_per_meal": 1, "uom": "عبوة / Bottle", "unit_cost": 1.50},
    ]
