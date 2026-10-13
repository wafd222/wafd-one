import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate, now_datetime


_WEIGHT = {"كجم / Kg": 1000.0, "جرام / Gram": 1.0}
_VOLUME = {"لتر / Liter": 1000.0, "مل / ML": 1.0}
_COUNT = {"حبة / Piece": 1.0}


def _unit_group(uom):
    for group in (_WEIGHT, _VOLUME, _COUNT):
        if uom in group:
            return group
    return None


def _convert_pack_to_ingredient_unit(pack_quantity, pack_uom, ingredient_uom):
    source = _unit_group(pack_uom)
    target = _unit_group(ingredient_uom)
    if not source or source is not target:
        frappe.throw(
            "وحدة العبوة لا تتوافق مع وحدة المكون / Pack UOM is incompatible with ingredient UOM"
        )
    base_quantity = flt(pack_quantity) * source[pack_uom]
    return base_quantity / target[ingredient_uom]


class WAFDIngredientPrice(Document):
    def validate(self):
        if not self.ingredient:
            return
        qty = flt(self.pack_quantity)
        price = flt(self.pack_price)
        if qty <= 0:
            frappe.throw("كمية العبوة يجب أن تكون أكبر من صفر / Pack quantity must be greater than zero")
        if price < 0:
            frappe.throw("سعر العبوة لا يمكن أن يكون سالبًا / Pack price cannot be negative")
        if self.observed_on and getdate(self.observed_on) > getdate(nowdate()):
            frappe.throw("تاريخ الرصد لا يمكن أن يكون في المستقبل / Observation date cannot be in the future")

        ingredient_uom = frappe.db.get_value("WAFD Ingredient", self.ingredient, "uom")
        if not ingredient_uom:
            frappe.throw("وحدة قياس المكون غير محددة / Ingredient UOM is not set")
        quantity_in_ingredient_uom = _convert_pack_to_ingredient_unit(qty, self.pack_uom, ingredient_uom)
        if quantity_in_ingredient_uom <= 0:
            frappe.throw("الكمية المحولة يجب أن تكون أكبر من صفر / Converted quantity must be greater than zero")
        self.unit_cost = price / quantity_in_ingredient_uom

    def on_update(self):
        self._refresh_ingredient_cost()

    def on_trash(self):
        ingredient = self.ingredient
        if ingredient:
            frappe.enqueue(
                "wafd_one.wafd_one.doctype.wafd_ingredient_price.wafd_ingredient_price.refresh_ingredient_cost",
                ingredient=ingredient,
                enqueue_after_commit=True,
            )

    def _refresh_ingredient_cost(self):
        refresh_ingredient_cost(self.ingredient)


def refresh_ingredient_cost(ingredient):
    if not ingredient or not frappe.db.exists("WAFD Ingredient", ingredient):
        return
    latest = frappe.get_all(
        "WAFD Ingredient Price",
        filters={
            "ingredient": ingredient,
            "approval_status": ["in", ["معتمد / Approved", "مرجعي / Benchmark"]],
        },
        fields=["name", "unit_cost", "observed_on", "source_type", "source_name", "approval_status"],
        order_by="observed_on desc, modified desc",
        limit=1,
    )
    values = {
        "latest_market_cost": 0,
        "latest_price_date": None,
        "latest_price_source": None,
        "cost_last_updated": now_datetime(),
        "cost_confidence": "منخفضة / Low",
    }
    if latest:
        row = latest[0]
        values.update({
            "latest_market_cost": flt(row.unit_cost),
            "latest_price_date": row.observed_on,
            "latest_price_source": " - ".join(filter(None, [row.source_name, row.source_type])),
            "cost_basis": "متوسط أسعار موثقة / Verified Price Average" if row.approval_status == "معتمد / Approved" else "تقديري / Estimated",
            "cost_confidence": "عالية / High" if row.approval_status == "معتمد / Approved" else "متوسطة / Medium",
        })
        if row.approval_status == "معتمد / Approved":
            values["standard_cost"] = flt(row.unit_cost)
    frappe.db.set_value("WAFD Ingredient", ingredient, values, update_modified=False)
