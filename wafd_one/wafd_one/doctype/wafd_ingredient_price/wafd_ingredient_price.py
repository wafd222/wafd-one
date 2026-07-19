import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WAFDIngredientPrice(Document):
    def validate(self):
        qty = flt(self.pack_quantity)
        if qty <= 0:
            frappe.throw("كمية العبوة يجب أن تكون أكبر من صفر / Pack quantity must be greater than zero")
        factor = 1
        if self.pack_uom == "جرام / Gram":
            factor = 1000
        elif self.pack_uom == "مل / ML":
            factor = 1000
        self.unit_cost = flt(self.pack_price) * factor / qty

    def on_update(self):
        if self.approval_status in ("معتمد / Approved", "مرجعي / Benchmark"):
            latest = frappe.get_all("WAFD Ingredient Price", filters={"ingredient": self.ingredient, "approval_status": ["in", ["معتمد / Approved", "مرجعي / Benchmark"]]}, fields=["name","unit_cost","observed_on","source_type"], order_by="observed_on desc, modified desc", limit=1)
            if latest and latest[0].name == self.name:
                frappe.db.set_value("WAFD Ingredient", self.ingredient, {"latest_market_cost": latest[0].unit_cost, "latest_price_date": latest[0].observed_on, "price_confidence": latest[0].source_type}, update_modified=False)
