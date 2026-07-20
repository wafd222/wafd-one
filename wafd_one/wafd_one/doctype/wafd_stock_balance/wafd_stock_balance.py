import frappe
from frappe.model.document import Document
from frappe.utils import flt


class WAFDStockBalance(Document):
    def validate(self):
        self.actual_quantity = flt(self.actual_quantity)
        self.reserved_quantity = flt(self.reserved_quantity)
        if self.actual_quantity < 0 or self.reserved_quantity < 0:
            frappe.throw("كميات المخزون لا يمكن أن تكون سالبة / Stock quantities cannot be negative")
        if self.reserved_quantity > self.actual_quantity:
            frappe.throw("الكمية المحجوزة لا يمكن أن تتجاوز الفعلية / Reserved quantity cannot exceed actual quantity")
        if flt(self.average_cost) < 0:
            frappe.throw("متوسط التكلفة لا يمكن أن يكون سالباً / Average cost cannot be negative")
        ingredient_uom = frappe.db.get_value("WAFD Ingredient", self.ingredient, "uom")
        if not self.uom:
            self.uom = ingredient_uom
        elif ingredient_uom and self.uom != ingredient_uom:
            frappe.throw("وحدة رصيد المخزون لا تطابق وحدة المكون / Stock balance UOM mismatch")
        self.available_quantity = self.actual_quantity - self.reserved_quantity
        self.stock_value = self.actual_quantity * flt(self.average_cost)
        duplicate = frappe.db.get_value(
            "WAFD Stock Balance",
            {"warehouse": self.warehouse, "ingredient": self.ingredient, "name": ["!=", self.name]},
            "name",
        )
        if duplicate:
            frappe.throw("يوجد سجل رصيد لهذا الصنف في المستودع / A stock balance already exists for this ingredient and warehouse")
