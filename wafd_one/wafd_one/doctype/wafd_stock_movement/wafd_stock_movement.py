import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class WafdStockMovement(Document):
    def validate(self):
        if self.status == "مرحلة / Posted" and not self.posted_on:
            frappe.throw("استخدم زر ترحيل الحركة / Use the Post Movement button")
        total = 0
        for row in self.items or []:
            if flt(row.quantity) <= 0:
                frappe.throw("كمية الصنف يجب أن تكون أكبر من صفر / Item quantity must be greater than zero")
            row.amount = flt(row.quantity) * flt(row.unit_cost)
            total += row.amount
        self.total_amount = total
        self._validate_warehouses()

    def _validate_warehouses(self):
        if self.movement_type in ("صرف / Issue", "تحويل / Transfer", "هالك / Waste") and not self.source_warehouse:
            frappe.throw("حدد المستودع المصدر / Select source warehouse")
        if self.movement_type in ("استلام / Receipt", "تحويل / Transfer") and not self.target_warehouse:
            frappe.throw("حدد المستودع المستهدف / Select target warehouse")
        if self.movement_type == "تحويل / Transfer" and self.source_warehouse == self.target_warehouse:
            frappe.throw("المستودع المصدر والمستهدف يجب أن يكونا مختلفين / Source and target warehouses must differ")


def _get_balance(warehouse, ingredient, uom=None, for_update=False):
    name = frappe.db.get_value("WAFD Stock Balance", {"warehouse": warehouse, "ingredient": ingredient}, "name")
    if name:
        doc = frappe.get_doc("WAFD Stock Balance", name)
        if for_update:
            frappe.db.sql("select name from `tabWAFD Stock Balance` where name=%s for update", name)
            doc.reload()
        return doc
    return frappe.get_doc({"doctype": "WAFD Stock Balance", "warehouse": warehouse, "ingredient": ingredient, "uom": uom, "actual_quantity": 0, "reserved_quantity": 0, "average_cost": 0})


def _add_stock(warehouse, row, posting_date):
    balance = _get_balance(warehouse, row.ingredient, row.uom, for_update=True)
    old_qty = flt(balance.actual_quantity)
    incoming = flt(row.quantity)
    new_qty = old_qty + incoming
    if new_qty > 0:
        balance.average_cost = ((old_qty * flt(balance.average_cost)) + (incoming * flt(row.unit_cost))) / new_qty
    balance.actual_quantity = new_qty
    balance.last_movement_date = posting_date
    balance.save(ignore_permissions=True)


def _remove_stock(warehouse, row, posting_date):
    balance = _get_balance(warehouse, row.ingredient, row.uom, for_update=True)
    required = flt(row.quantity)
    available = flt(balance.available_quantity)
    if available < required:
        frappe.throw(f"المخزون غير كافٍ للصنف {row.ingredient}: المطلوب {required} والمتاح {available} / Insufficient stock")
    balance.actual_quantity = flt(balance.actual_quantity) - required
    balance.last_movement_date = posting_date
    balance.save(ignore_permissions=True)


@frappe.whitelist()
def post_movement(movement_name):
    doc = frappe.get_doc("WAFD Stock Movement", movement_name)
    doc.check_permission("write")
    if doc.status == "مرحلة / Posted":
        return {"name": doc.name, "posted": False}
    if doc.status == "ملغاة / Cancelled":
        frappe.throw("لا يمكن ترحيل حركة ملغاة / A cancelled movement cannot be posted")
    doc._validate_warehouses()
    if not doc.items:
        frappe.throw("أضف صنفًا واحدًا على الأقل / Add at least one item")
    for row in doc.items:
        if doc.movement_type == "استلام / Receipt":
            _add_stock(doc.target_warehouse, row, doc.posting_date)
        elif doc.movement_type in ("صرف / Issue", "هالك / Waste"):
            _remove_stock(doc.source_warehouse, row, doc.posting_date)
        elif doc.movement_type == "تحويل / Transfer":
            _remove_stock(doc.source_warehouse, row, doc.posting_date)
            _add_stock(doc.target_warehouse, row, doc.posting_date)
        elif doc.movement_type == "تسوية / Adjustment":
            warehouse = doc.target_warehouse or doc.source_warehouse
            if not warehouse:
                frappe.throw("حدد مستودع التسوية / Select adjustment warehouse")
            balance = _get_balance(warehouse, row.ingredient, row.uom, for_update=True)
            balance.actual_quantity = flt(row.quantity)
            balance.average_cost = flt(row.unit_cost) or flt(balance.average_cost)
            balance.last_movement_date = doc.posting_date
            balance.save(ignore_permissions=True)
    doc.db_set({"status": "مرحلة / Posted", "posted_by": frappe.session.user, "posted_on": now_datetime()}, update_modified=True)
    return {"name": doc.name, "posted": True}
