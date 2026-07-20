import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, now_datetime, getdate


class WAFDStockMovement(Document):
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
        self._validate_reference()
        self._validate_master_data()
        if self.posting_date and get_datetime(self.posting_date) > now_datetime():
            frappe.throw("تاريخ الترحيل لا يمكن أن يكون مستقبلياً / Posting date cannot be in the future")

    def _validate_master_data(self):
        seen = set()
        for row in self.items or []:
            if row.ingredient in seen:
                frappe.throw(f"المكون مكرر في الحركة: {row.ingredient} / Duplicate ingredient in movement")
            seen.add(row.ingredient)
            if flt(row.unit_cost) < 0:
                frappe.throw("تكلفة الوحدة لا يمكن أن تكون سالبة / Unit cost cannot be negative")
            ingredient = frappe.db.get_value("WAFD Ingredient", row.ingredient, ["is_active", "uom"], as_dict=True)
            if not ingredient or not ingredient.is_active:
                frappe.throw(f"المكون غير نشط: {row.ingredient} / Ingredient is inactive")
            if not row.uom:
                row.uom = ingredient.uom
            elif ingredient.uom and row.uom != ingredient.uom:
                frappe.throw(f"وحدة الصنف {row.ingredient} يجب أن تكون {ingredient.uom} / Ingredient UOM mismatch")
            if row.production_date and row.expiry_date and getdate(row.production_date) > getdate(row.expiry_date):
                frappe.throw(f"تاريخ إنتاج {row.ingredient} بعد تاريخ الانتهاء / Production date cannot be after expiry date")
            if self.movement_type == "استلام / Receipt" and row.expiry_date and getdate(row.expiry_date) <= getdate(self.posting_date):
                frappe.throw(f"لا يمكن استلام صنف منتهي أو ينتهي في تاريخ الاستلام: {row.ingredient} / Expired item cannot be received")
            if row.receiving_temperature is not None and (flt(row.receiving_temperature) < -50 or flt(row.receiving_temperature) > 100):
                frappe.throw(f"حرارة استلام غير منطقية للصنف {row.ingredient} / Invalid receiving temperature")

    def _validate_reference(self):
        if self.reference_type == "WAFD Purchase Order" and self.reference_name:
            po = frappe.get_doc("WAFD Purchase Order", self.reference_name)
            if self.movement_type != "استلام / Receipt":
                frappe.throw("مرجع أمر الشراء مسموح لحركات الاستلام فقط / Purchase order references are only allowed for receipts")
            if po.status == "ملغي / Cancelled":
                frappe.throw("أمر الشراء ملغي / Purchase order is cancelled")
            if self.target_warehouse != po.warehouse:
                frappe.throw("مستودع الاستلام يجب أن يطابق مستودع أمر الشراء / Receipt warehouse must match the purchase order")
            ordered = {row.ingredient: row for row in po.items or []}
            posted = _posted_purchase_receipts(po.name, exclude_movement=self.name)
            for row in self.items or []:
                if row.ingredient not in ordered:
                    frappe.throw(f"الصنف {row.ingredient} غير موجود في أمر الشراء / Item is not in the purchase order")
                po_row = ordered[row.ingredient]
                if row.uom and po_row.uom and row.uom != po_row.uom:
                    frappe.throw(f"وحدة استلام {row.ingredient} لا تطابق أمر الشراء / Receipt UOM mismatch")
                remaining = flt(po_row.quantity) - flt(posted.get(row.ingredient, 0))
                if flt(row.quantity) > remaining + 0.000001:
                    frappe.throw(
                        f"كمية استلام {row.ingredient} تتجاوز المتبقي {remaining} / Receipt exceeds outstanding quantity"
                    )

    def before_save(self):
        if not self.is_new() and self.get_db_value("status") == "مرحلة / Posted":
            frappe.throw("لا يمكن تعديل حركة مخزون مرحلة / A posted stock movement cannot be edited")

    def before_delete(self):
        if self.status == "مرحلة / Posted":
            frappe.throw("لا يمكن حذف حركة مخزون مرحلة / A posted stock movement cannot be deleted")

    def _validate_warehouses(self):
        if self.movement_type in ("صرف / Issue", "تحويل / Transfer", "هالك / Waste") and not self.source_warehouse:
            frappe.throw("حدد المستودع المصدر / Select source warehouse")
        if self.movement_type in ("استلام / Receipt", "تحويل / Transfer") and not self.target_warehouse:
            frappe.throw("حدد المستودع المستهدف / Select target warehouse")
        if self.movement_type == "تحويل / Transfer" and self.source_warehouse == self.target_warehouse:
            frappe.throw("المستودع المصدر والمستهدف يجب أن يكونا مختلفين / Source and target warehouses must differ")


def _posted_purchase_receipts(purchase_order_name, exclude_movement=None):
    totals = {}
    filters = {
        "movement_type": "استلام / Receipt",
        "reference_type": "WAFD Purchase Order",
        "reference_name": purchase_order_name,
        "status": "مرحلة / Posted",
    }
    movements = frappe.get_all("WAFD Stock Movement", filters=filters, pluck="name")
    for name in movements:
        if exclude_movement and name == exclude_movement:
            continue
        doc = frappe.get_doc("WAFD Stock Movement", name)
        for row in doc.items or []:
            totals[row.ingredient] = totals.get(row.ingredient, 0) + flt(row.quantity)
    return totals


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
    frappe.db.sql("select name from `tabWAFD Stock Movement` where name=%s for update", movement_name)
    doc.reload()
    if doc.status == "مرحلة / Posted":
        return {"name": doc.name, "posted": False}
    if doc.status == "ملغاة / Cancelled":
        frappe.throw("لا يمكن ترحيل حركة ملغاة / A cancelled movement cannot be posted")
    doc.validate()
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
    if doc.reference_type == "WAFD Purchase Order" and doc.reference_name:
        from wafd_one.wafd_one.doctype.wafd_purchase_order.wafd_purchase_order import sync_purchase_order_receipts
        sync_purchase_order_receipts(doc.reference_name)
    if doc.production_batch and frappe.db.exists("WAFD Production Batch", doc.production_batch):
        frappe.db.set_value(
            "WAFD Production Batch", doc.production_batch,
            {"material_issue": doc.name, "materials_status": "مصروفة / Issued"},
            update_modified=False,
        )
    return {"name": doc.name, "posted": True}
